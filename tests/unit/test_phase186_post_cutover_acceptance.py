from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.transactional_release_update as update


def _migration_fixture(root: Path, head: str = "m1") -> None:
    versions = root / "alembic" / "versions"; versions.mkdir(parents=True, exist_ok=True)
    (versions / "001.py").write_text(f"revision = '{head}'\ndown_revision = None\n")
    (root / "MIGRATION_COMPATIBILITY.json").write_text(json.dumps({
        "schema_version": "1.0", "classification": "DATABASE_MIGRATION_COMPATIBILITY_CONTRACT",
        "migrations": {head: {"down_revision": None, "previous_release_compatible": True, "requires_backup": True, "rollback_strategy": "restore_or_forward"}}
    }))


def _active(parent: Path) -> Path:
    p = parent / "active"; p.mkdir(); (p / "marker.txt").write_text("old"); _migration_fixture(p)
    return p


def _fake_extract(package: Path, destination: Path, **kwargs):
    p = destination / "project"; p.mkdir(); (p / "marker.txt").write_text("new"); _migration_fixture(p)
    return {"classification": "SOURCE_PACKAGE_SAFE_EXTRACTION"}


def _verified(root: Path):
    return {"verified": True, "problems": [], "git_commit_sha": "a" * 40}


def test_failed_post_cutover_acceptance_automatically_restores_old_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active = _active(tmp_path); package = tmp_path / "source.zip"; package.write_bytes(b"x")
    monkeypatch.setattr(update, "extract", _fake_extract)
    monkeypatch.setattr(update, "verify_source_package_identity", _verified)
    monkeypatch.setattr(update, "run_post_cutover_acceptance", lambda root, **kwargs: {"accepted": False, "problems": ["MIGRATION_MISMATCH"], "binding": {"accepted": False}})
    with pytest.raises(RuntimeError, match="UPDATE_POST_CUTOVER_ACCEPTANCE_FAILED"):
        update.apply_update(package=package, active=active)
    assert (active / "marker.txt").read_text() == "old"
    assert not (tmp_path / update.JOURNAL).exists()
    assert not list(tmp_path.glob(f"{update.BACKUP_PREFIX}*"))


def test_successful_update_writes_hash_bound_rollback_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active = _active(tmp_path); package = tmp_path / "source.zip"; package.write_bytes(b"x")
    monkeypatch.setattr(update, "extract", _fake_extract)
    monkeypatch.setattr(update, "verify_source_package_identity", _verified)
    monkeypatch.setattr(update, "run_post_cutover_acceptance", lambda root, **kwargs: {"accepted": True, "problems": [], "binding": {"accepted": True, "problems": [], "migration_version": "m1"}})
    result = update.apply_update(package=package, active=active)
    rollback = Path(result["rollback_directory"]); receipt = Path(result["rollback_receipt"])
    payload = json.loads(receipt.read_text())
    assert payload["backup_tree_sha256"] == update._tree_sha256(rollback)
    assert result["runtime_binding"]["accepted"] is True


def test_tampered_rollback_tree_is_rejected_without_moving_active(tmp_path: Path):
    active = _active(tmp_path); (active / "marker.txt").write_text("new")
    backup = tmp_path / f"{update.BACKUP_PREFIX}abc"; backup.mkdir(); (backup / "marker.txt").write_text("old")
    update._atomic_json(update._receipt_path(backup), {
        "schema_version": "1.0", "classification": "VERIFIED_RELEASE_ROLLBACK_RECEIPT",
        "backup": backup.name, "backup_tree_sha256": update._tree_sha256(backup),
    })
    (backup / "marker.txt").write_text("tampered")
    with pytest.raises(RuntimeError, match="ROLLBACK_BACKUP_HASH_MISMATCH"):
        update.rollback_last_update(active=active, rollback_dir=backup)
    assert (active / "marker.txt").read_text() == "new"


def test_missing_rollback_receipt_fails_closed(tmp_path: Path):
    active = _active(tmp_path); backup = tmp_path / f"{update.BACKUP_PREFIX}abc"; backup.mkdir()
    with pytest.raises(RuntimeError, match="ROLLBACK_RECEIPT_MISSING_OR_UNSAFE"):
        update.rollback_last_update(active=active, rollback_dir=backup)


def test_runtime_binding_detects_migration_architecture_and_git_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "alembic" / "versions").mkdir(parents=True)
    (tmp_path / "alembic" / "versions" / "001.py").write_text("revision = '001'\ndown_revision = None\n")
    (tmp_path / "architecture_profile.yaml").write_text("profile: test\n")
    (tmp_path / "RELEASE_MANIFEST.json").write_text(json.dumps({
        "git_commit_sha": "b" * 40, "migration_version": "wrong", "architecture_profile_hash": "0" * 64
    }))
    monkeypatch.setattr(update, "verify_source_package_identity", lambda root: {"verified": True, "git_commit_sha": "a" * 40})
    result = update.verify_runtime_binding(tmp_path)
    assert result["accepted"] is False
    assert "RELEASE_PACKAGE_GIT_IDENTITY_MISMATCH" in result["problems"]
    assert "RELEASE_MIGRATION_HEAD_MISMATCH" in result["problems"]
    assert "RELEASE_ARCHITECTURE_PROFILE_HASH_MISMATCH" in result["problems"]


def test_runtime_binding_accepts_exact_static_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "alembic" / "versions").mkdir(parents=True)
    (tmp_path / "alembic" / "versions" / "001.py").write_text("revision = '001'\ndown_revision = None\n")
    arch = tmp_path / "architecture_profile.yaml"; arch.write_text("profile: test\n")
    (tmp_path / "RELEASE_MANIFEST.json").write_text(json.dumps({
        "git_commit_sha": "a" * 40, "migration_version": "001", "architecture_profile_hash": update._sha256_file(arch)
    }))
    monkeypatch.setattr(update, "verify_source_package_identity", lambda root: {"verified": True, "git_commit_sha": "a" * 40})
    result = update.verify_runtime_binding(tmp_path)
    assert result["accepted"] is True
    assert result["problems"] == []


def test_runtime_command_failure_causes_automatic_rollback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import sys
    active = _active(tmp_path); package = tmp_path / "source.zip"; package.write_bytes(b"x")
    monkeypatch.setattr(update, "extract", _fake_extract)
    monkeypatch.setattr(update, "verify_source_package_identity", _verified)
    monkeypatch.setattr(update, "verify_runtime_binding", lambda root: {"accepted": True, "problems": []})
    with pytest.raises(RuntimeError, match="POST_CUTOVER_RUNTIME_COMMAND_FAILED"):
        update.apply_update(package=package, active=active, acceptance_command=[sys.executable, "-c", "raise SystemExit(7)"])
    assert (active / "marker.txt").read_text() == "old"
    assert not (tmp_path / update.JOURNAL).exists()


def test_runtime_command_is_shell_free_and_accepts_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import sys
    active = _active(tmp_path); package = tmp_path / "source.zip"; package.write_bytes(b"x")
    monkeypatch.setattr(update, "extract", _fake_extract)
    monkeypatch.setattr(update, "verify_source_package_identity", _verified)
    monkeypatch.setattr(update, "verify_runtime_binding", lambda root: {"accepted": True, "problems": []})
    result = update.apply_update(package=package, active=active, acceptance_command=[sys.executable, "-c", "print('healthy')"])
    cmd = result["post_cutover_acceptance"]["runtime_command"]
    assert cmd["returncode"] == 0 and cmd["shell"] is False
    assert "healthy" in cmd["stdout_tail"]
