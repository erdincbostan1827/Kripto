from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

import scripts.database_migration_guard as guard
import scripts.transactional_release_update as update


def _release(root: Path, revisions: list[tuple[str, str | None]], marker: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "marker.txt").write_text(marker)
    versions = root / "alembic" / "versions"; versions.mkdir(parents=True)
    entries = {}
    for i, (rev, down) in enumerate(revisions):
        down_src = "None" if down is None else repr(down)
        (versions / f"{i:04d}_{rev}.py").write_text(f"revision = {rev!r}\ndown_revision = {down_src}\n")
        entries[rev] = {
            "down_revision": down,
            "previous_release_compatible": True,
            "requires_backup": True,
            "rollback_strategy": "restore_or_forward",
        }
    (root / guard.CONTRACT_FILE).write_text(json.dumps({
        "schema_version": "1.0", "classification": "DATABASE_MIGRATION_COMPATIBILITY_CONTRACT", "migrations": entries
    }))
    return root


def _backup_receipt(tmp_path: Path, active: Path, head: str) -> Path:
    backup = tmp_path / "database.dump"; backup.write_bytes(b"verified-backup")
    backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
    restore = tmp_path / "database.dump.restore-drill.json"
    restore_body = {
        "schema_version": "1.0", "classification": "VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT",
        "backup_sha256": backup_hash, "restore_status": "PASS", "restored_table_count": 3, "completed_at": "test",
        "policy": "REAL_RESTORE_COMMAND_COMPLETED_AND_DATABASE_SMOKE_CHECK_PASSED",
    }
    restore_body["provenance_sha256"] = guard._canonical_hash(restore_body)
    restore.write_text(json.dumps(restore_body))
    receipt = tmp_path / "database-backup-receipt.json"
    receipt.write_text(json.dumps({
        "schema_version": "1.0", "classification": "VERIFIED_DATABASE_BACKUP_RECEIPT",
        "migration_head": head, "active_tree_sha256": update._tree_sha256(active),
        "backup_artifact": backup.name, "backup_sha256": backup_hash,
        "restore_drill_receipt": restore.name, "restore_drill_receipt_sha256": hashlib.sha256(restore.read_bytes()).hexdigest(),
        "restore_drill_provenance_sha256": restore_body["provenance_sha256"],
    }))
    return receipt


def _probe(head_file: Path) -> list[str]:
    return [sys.executable, "-c", f"from pathlib import Path; print(Path({str(head_file)!r}).read_text().strip())"]


def _migrate(head_file: Path, head: str, rc: int = 0) -> list[str]:
    return [sys.executable, "-c", f"from pathlib import Path; Path({str(head_file)!r}).write_text({head!r}); raise SystemExit({rc})"]


def test_migration_plan_requires_explicit_descendant_contract(tmp_path: Path):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    candidate = _release(tmp_path / "candidate", [("m1", None), ("m2", "m1")], "new")
    plan = guard.compare_release_migrations(active, candidate)
    assert plan["required"] is True
    assert plan["from_head"] == "m1" and plan["to_head"] == "m2"
    assert plan["pending"] == ["m2"]
    assert plan["previous_release_compatible"] is True
    assert plan["requires_backup"] is True


def test_previous_release_incompatible_migration_is_blocked_before_execution(tmp_path: Path):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    candidate = _release(tmp_path / "candidate", [("m1", None), ("m2", "m1")], "new")
    contract = json.loads((candidate / guard.CONTRACT_FILE).read_text())
    contract["migrations"]["m2"]["previous_release_compatible"] = False
    (candidate / guard.CONTRACT_FILE).write_text(json.dumps(contract))
    with pytest.raises(RuntimeError, match="MIGRATION_PREVIOUS_RELEASE_INCOMPATIBLE"):
        guard.compare_release_migrations(active, candidate)


def test_backup_receipt_binds_artifact_head_and_active_tree(tmp_path: Path):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    receipt = _backup_receipt(tmp_path, active, "m1")
    result = guard.verify_backup_receipt(receipt, expected_head="m1", expected_active_tree_sha256=update._tree_sha256(active))
    assert result["verified"] is True
    (tmp_path / "database.dump").write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="DATABASE_BACKUP_ARTIFACT_HASH_MISMATCH"):
        guard.verify_backup_receipt(receipt, expected_head="m1", expected_active_tree_sha256=update._tree_sha256(active))


def test_guarded_migration_commits_only_after_authoritative_target_probe(tmp_path: Path):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    candidate = _release(tmp_path / "candidate", [("m1", None), ("m2", "m1")], "new")
    backup = _backup_receipt(tmp_path, active, "m1")
    head = tmp_path / "db-head"; head.write_text("m1")
    state = tmp_path / "state"
    result = guard.run_guarded_migration(
        active=active, candidate=candidate, state_dir=state, backup_receipt=backup,
        probe_command=_probe(head), migration_command=_migrate(head, "m2"), candidate_git_commit_sha="a" * 40,
    )
    assert result["migrated"] is True and result["status"] == "MIGRATION_COMMITTED"
    receipt = Path(result["migration_receipt"])
    verified = guard.verify_migration_receipt(
        receipt, active_tree_sha256=update._tree_sha256(active), candidate_tree_sha256=update._tree_sha256(candidate),
        from_head="m1", to_head="m2", candidate_git_commit_sha="a" * 40,
    )
    assert verified["verified"] is True
    assert not (state / guard.JOURNAL).exists()


def test_interrupted_after_database_reaches_target_is_recovered_to_verified_receipt(tmp_path: Path):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    candidate = _release(tmp_path / "candidate", [("m1", None), ("m2", "m1")], "new")
    backup = _backup_receipt(tmp_path, active, "m1")
    head = tmp_path / "db-head"; head.write_text("m1"); state = tmp_path / "state"
    with pytest.raises(RuntimeError, match="COMMAND_FAILED_RECOVERY_REQUIRED"):
        guard.run_guarded_migration(
            active=active, candidate=candidate, state_dir=state, backup_receipt=backup,
            probe_command=_probe(head), migration_command=_migrate(head, "m2", rc=9), candidate_git_commit_sha="b" * 40,
        )
    assert (state / guard.JOURNAL).exists()
    recovery = guard.recover_migration_transaction(state_dir=state, probe_command=_probe(head), cwd=candidate)
    assert recovery["status"] == "MIGRATION_COMPLETED_BEFORE_INTERRUPTION"
    assert Path(recovery["migration_receipt"]).is_file()
    assert not (state / guard.JOURNAL).exists()


def test_interrupted_before_database_change_recovers_without_faking_migration(tmp_path: Path):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    candidate = _release(tmp_path / "candidate", [("m1", None), ("m2", "m1")], "new")
    backup = _backup_receipt(tmp_path, active, "m1")
    head = tmp_path / "db-head"; head.write_text("m1"); state = tmp_path / "state"
    fail = [sys.executable, "-c", "raise SystemExit(7)"]
    with pytest.raises(RuntimeError, match="COMMAND_FAILED_RECOVERY_REQUIRED"):
        guard.run_guarded_migration(active=active, candidate=candidate, state_dir=state, backup_receipt=backup, probe_command=_probe(head), migration_command=fail)
    recovery = guard.recover_migration_transaction(state_dir=state, probe_command=_probe(head), cwd=candidate)
    assert recovery["status"] == "MIGRATION_NOT_APPLIED"
    assert not list(state.glob(f"{guard.RECEIPT_PREFIX}*.json"))


def test_ambiguous_interrupted_database_head_fails_closed_and_preserves_journal(tmp_path: Path):
    state = tmp_path / "state"; state.mkdir(); candidate = tmp_path / "candidate"; candidate.mkdir()
    head = tmp_path / "db-head"; head.write_text("unknown")
    guard._atomic_json(state / guard.JOURNAL, {
        "schema_version": "1.0", "classification": "DATABASE_MIGRATION_TRANSACTION", "transaction_id": "x",
        "from_head": "m1", "to_head": "m2", "active_tree_sha256": "a" * 64, "candidate_tree_sha256": "b" * 64,
        "compatibility_contract_sha256": "c" * 64, "database_backup_receipt_sha256": "d" * 64, "pending_revisions": ["m2"]
    })
    with pytest.raises(RuntimeError, match="DATABASE_MIGRATION_STATE_AMBIGUOUS"):
        guard.recover_migration_transaction(state_dir=state, probe_command=_probe(head), cwd=candidate)
    assert (state / guard.JOURNAL).exists()


def test_migration_receipt_tampering_is_rejected(tmp_path: Path):
    path = tmp_path / "receipt.json"
    body = {
        "schema_version": "1.0", "classification": "VERIFIED_DATABASE_MIGRATION_RECEIPT", "transaction_id": "x",
        "from_head": "m1", "to_head": "m2", "observed_head": "m2", "active_tree_sha256": "a"*64,
        "candidate_tree_sha256": "b"*64, "candidate_git_commit_sha": "c"*40, "compatibility_contract_sha256": "d"*64,
        "database_backup_receipt_sha256": "e"*64, "pending_revisions": ["m2"], "completed_at": "x"
    }
    body["provenance_sha256"] = guard._canonical_hash(body); path.write_text(json.dumps(body))
    body["to_head"] = "evil"; path.write_text(json.dumps(body))
    with pytest.raises(RuntimeError, match="PROVENANCE_MISMATCH"):
        guard.verify_migration_receipt(path, active_tree_sha256="a"*64, candidate_tree_sha256="b"*64, from_head="m1", to_head="m2", candidate_git_commit_sha="c"*40)


def test_release_updater_rejects_schema_head_change_without_guarded_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    package = tmp_path / "source.zip"; package.write_bytes(b"x")
    def fake_extract(package: Path, destination: Path, **kwargs):
        _release(destination / "project", [("m1", None), ("m2", "m1")], "new")
        return {"classification": "SOURCE_PACKAGE_SAFE_EXTRACTION"}
    monkeypatch.setattr(update, "extract", fake_extract)
    monkeypatch.setattr(update, "verify_source_package_identity", lambda root: {"verified": True, "problems": [], "git_commit_sha": "f"*40})
    with pytest.raises(RuntimeError, match="UPDATE_DATABASE_MIGRATION_RECEIPT_REQUIRED"):
        update.apply_update(package=package, active=active)
    assert (active / "marker.txt").read_text() == "old"
    assert not (tmp_path / update.JOURNAL).exists()


def test_acceptance_receipt_is_provenance_bound_and_rollback_requires_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active = _release(tmp_path / "active", [("m1", None)], "old")
    package = tmp_path / "source.zip"; package.write_bytes(b"x")
    def fake_extract(package: Path, destination: Path, **kwargs):
        _release(destination / "project", [("m1", None)], "new")
        return {"classification": "SOURCE_PACKAGE_SAFE_EXTRACTION"}
    monkeypatch.setattr(update, "extract", fake_extract)
    monkeypatch.setattr(update, "verify_source_package_identity", lambda root: {"verified": True, "problems": [], "git_commit_sha": "f"*40})
    monkeypatch.setattr(update, "run_post_cutover_acceptance", lambda root, **kwargs: {"accepted": True, "problems": [], "binding": {"accepted": True, "migration_version": "m1", "architecture_profile_hash": "a"*64}})
    result = update.apply_update(package=package, active=active)
    acceptance = Path(result["acceptance_receipt"])
    payload = update._verify_acceptance_receipt(acceptance)
    assert payload["provenance_sha256"]
    rollback = Path(result["rollback_directory"])
    acceptance.write_text(acceptance.read_text().replace('"migration_version": "m1"', '"migration_version": "evil"'))
    with pytest.raises(RuntimeError, match="UPDATE_ACCEPTANCE_RECEIPT_PROVENANCE_MISMATCH"):
        update.rollback_last_update(active=active, rollback_dir=rollback)
    assert (active / "marker.txt").read_text() == "new"
