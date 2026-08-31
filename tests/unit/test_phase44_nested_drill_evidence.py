from __future__ import annotations
import pytest

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.verify_external_acceptance import verify_manifest
from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.evidence_ledger import append_entry


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _setup_git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    (root / "seed").write_text("x")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _bundle(root: Path, *, tamper: bool = False) -> Path:
    sha = _setup_git(root)
    evidence_log = root / "real-pitr.log"
    evidence_log.write_text("restore executed\n")
    drill = {
        "schema_version": "2.0",
        "classification": "REAL_EXTERNAL_ACCEPTANCE_DRILL", "drill_kind": "PITR_RESTORE", "real_system": True,
        "observed_at": datetime.now(timezone.utc).isoformat(), "git_commit_sha": sha,
        "artifacts": [{"path": "real-pitr.log", "sha256": _sha(evidence_log)}],
        "isolated_environment": True, "backup_or_pitr_restored": True, "schema_validated": True,
        "referential_integrity_validated": True, "checksum_validated": True, "read_only_smoke_passed": True,
        "result_reported": True,
    }
    drill_path = root / "pitr.json"
    drill_path.write_text(json.dumps(drill))
    wrapper = root / "pitr_wrapper.log"
    wrapper.write_text(json.dumps({"status":"PASS", "evidence_artifact":"pitr.json", "evidence_sha256":_sha(drill_path)}) + "\n")
    now = datetime.now(timezone.utc).isoformat()
    reports = root / "reports/external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge_path = reports / "release_challenge.json"
    challenge = create_challenge(root, challenge_path)
    drill["release_challenge"] = {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]}
    drill["environment"] = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    drill_path.write_text(json.dumps(drill))
    wrapper.write_text(json.dumps({"status":"PASS", "evidence_artifact":"pitr.json", "evidence_sha256":_sha(drill_path)}) + "\n")
    payload = {
        "schema_version":"3.0", "classification":"EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE", "generated_at":now, "profile":"pitr",
        "real_target_explicitly_confirmed":True, "challenge":challenge, "environment":{"git_commit_sha":sha, "acceptance_environment_id_hash":"a"*64, "topology_hash":"b"*64},
        "evidence":[{"key":"pitr_drill","status":"PASS","real_system":True,"exit_code":0,"blocker":None,
                     "artifact":"pitr_wrapper.log","sha256":_sha(wrapper),"observed_at":now,"command":[]}],
        "groups":{"pitr":"PASS"}, "selected_all_pass":True,
    }
    manifest=root/"manifest.json"; manifest.write_text(json.dumps(payload))
    append_entry(reports / "evidence_ledger.json", manifest_sha256=_sha(manifest), challenge_id=challenge["challenge_id"], git_commit_sha=sha, profile="pitr")
    if tamper:
        drill["schema_validated"] = False
        drill_path.write_text(json.dumps(drill))
    return manifest


def test_nested_pitr_evidence_is_verified(tmp_path: Path) -> None:
    result = verify_manifest(_bundle(tmp_path), root=tmp_path)
    assert result["groups"]["pitr"] == "PASS"
    assert not any(p.startswith("DRILL_SUBARTIFACT_INVALID:pitr") for p in result["problems"])


def test_nested_pitr_tampering_blocks_group(tmp_path: Path) -> None:
    result = verify_manifest(_bundle(tmp_path, tamper=True), root=tmp_path)
    assert result["groups"]["pitr"] == "BLOCKED"
    assert any(p.startswith("DRILL_SUBARTIFACT_INVALID:pitr") for p in result["problems"])


@pytest.fixture(autouse=True)
def _phase155_external_challenge_trust(monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
