from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

import scripts.external.acceptance_return_promotion as promo
from scripts.external.acceptance_return_bundle import MANIFEST


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "reports/external_acceptance").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase181@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase 181"], cwd=root, check=True)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    return root


def _staged(root: Path, tmp_path: Path, files: dict[str, bytes]) -> Path:
    staged = tmp_path / "staged"
    staged.mkdir()
    rows = []
    for rel, data in files.items():
        path = staged / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    (staged / MANIFEST).write_text(json.dumps({"source_git_commit_sha": sha, "file_count": len(rows), "files": rows}), encoding="utf-8")
    return staged


def test_phase181_recovery_rolls_back_swapped_canonical_without_import_ledger(tmp_path: Path):
    root = _repo(tmp_path)
    canonical = root / "reports/external_acceptance"
    (canonical / "manifest_runtime.json").write_text("old\n", encoding="utf-8")
    bundle = "a" * 64
    backup = root / "reports/.external_acceptance.rollback-test"
    replacement = root / "reports/.external_acceptance.promote-test"
    os.replace(canonical, backup)
    canonical.mkdir()
    (canonical / "manifest_runtime.json").write_text("new\n", encoding="utf-8")
    promo._write_transaction_journal(root, {
        "status": "CANONICAL_SWAPPED", "bundle_manifest_sha256": bundle,
        "source_git_commit_sha": subprocess.check_output(["git","rev-parse","HEAD"], cwd=root, text=True).strip(),
        "canonical_relpath": "reports/external_acceptance",
        "backup_relpath": backup.relative_to(root).as_posix(),
        "replacement_relpath": replacement.relative_to(root).as_posix(),
        "lock_candidate_relpath": None, "lock_candidate_preexisting": False,
    })
    result = promo.recover_pending_transaction(root)
    assert result["status"] == "ROLLED_BACK"
    assert (canonical / "manifest_runtime.json").read_text() == "old\n"
    assert not (root / promo.TRANSACTION_JOURNAL).exists()


def test_phase181_recovery_finalizes_when_import_ledger_contains_bundle(tmp_path: Path):
    root = _repo(tmp_path)
    bundle = "b" * 64
    backup = root / "reports/.external_acceptance.rollback-test"
    backup.mkdir(parents=True)
    (backup / "old.json").write_text("old\n")
    promo._append_import_ledger(root, bundle_manifest_sha256=bundle, source_git_commit_sha="c"*40,
                                promoted_files=["reports/external_acceptance/new.json"], artifact_classes=["CANONICAL_EXTERNAL_ACCEPTANCE"])
    promo._write_transaction_journal(root, {
        "status": "LEDGER_COMMITTED", "bundle_manifest_sha256": bundle, "source_git_commit_sha": "c"*40,
        "canonical_relpath": "reports/external_acceptance",
        "backup_relpath": backup.relative_to(root).as_posix(),
        "replacement_relpath": "reports/.external_acceptance.promote-test",
        "lock_candidate_relpath": None, "lock_candidate_preexisting": False,
    })
    result = promo.recover_pending_transaction(root)
    assert result["status"] == "FINALIZED_COMMIT"
    assert not backup.exists()
    assert not (root / promo.TRANSACTION_JOURNAL).exists()


def test_phase181_import_ledger_binds_external_trust_anchor(tmp_path: Path):
    root = _repo(tmp_path)
    anchor = {
        "external_evidence_ledger_sha256": "1"*64,
        "external_evidence_ledger_head_hash": "2"*64,
        "ledger_checkpoint_sha256": "3"*64,
        "ledger_checkpoint_signature_sha256": "4"*64,
        "release_challenge_sha256": "5"*64,
    }
    promo._append_import_ledger(root, bundle_manifest_sha256="6"*64, source_git_commit_sha="7"*40,
                                promoted_files=[], artifact_classes=["TRUST_CHAIN_EVIDENCE"], trust_anchor=anchor)
    doc, problems = promo._load_import_ledger(root)
    assert problems == []
    assert doc["events"][0]["trust_anchor"] == anchor
    tampered = json.loads((root / promo.IMPORT_LEDGER).read_text())
    tampered["events"][0]["trust_anchor"]["ledger_checkpoint_sha256"] = "8"*64
    (root / promo.IMPORT_LEDGER).write_text(json.dumps(tampered))
    _, problems = promo._load_import_ledger(root)
    assert "IMPORT_LEDGER_HASH_INVALID:0" in problems


def test_phase181_trust_anchor_extracts_ledger_checkpoint_and_challenge(tmp_path: Path):
    staged = tmp_path / "staged"
    base = staged / "reports/external_acceptance"
    base.mkdir(parents=True)
    ledger = {"schema_version":"1.0","classification":"EXTERNAL_ACCEPTANCE_APPEND_ONLY_EVIDENCE_LEDGER","entries":[]}
    (base / "evidence_ledger.json").write_text(json.dumps(ledger))
    checkpoint = {"ledger_head_hash": promo.ZERO_HASH, "signature_sha256": "a"*64, "signer_key_id": "kid"}
    (base / "evidence_ledger_checkpoint.json").write_text(json.dumps(checkpoint))
    (base / "release_challenge.json").write_text("{}")
    anchor = promo._trust_anchor_from_staged(staged)
    assert anchor["external_evidence_ledger_verified"] is True
    assert anchor["external_evidence_ledger_head_hash"] == promo.ZERO_HASH
    assert anchor["ledger_checkpoint_head_hash"] == promo.ZERO_HASH
    assert len(anchor["release_challenge_sha256"]) == 64


def test_phase181_promote_invokes_recovery_before_assessment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _repo(tmp_path)
    staged = _staged(root, tmp_path, {"reports/external_acceptance/manifest_runtime.json": b"new\n"})
    monkeypatch.setattr(promo, "recover_pending_transaction", lambda _root: {"recovered": False, "status": "RECOVERY_FAILED", "problems": ["TRANSACTION_RECOVERY_FAILED:Fixture"]})
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    result = promo.promote(staged, root=root, confirm_source_sha=sha)
    assert result["promoted"] is False
    assert result["problems"] == ["TRANSACTION_RECOVERY_FAILED:Fixture"]
