from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.evidence_ledger import append_entry
from backend.app.release.acceptance_contract import command_contract, command_contract_sha256
from scripts.verify_external_acceptance import verify_manifest


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p75@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P75"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _pitr_bundle(root: Path, nested_age_hours: int) -> Path:
    git_sha = _git(root)
    reports = root / "reports/external_acceptance"; reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    raw = root / "restore.log"; raw.write_text("real restore\n", encoding="utf-8")
    nested = {
        "schema_version": "2.0",
        "classification": "REAL_EXTERNAL_ACCEPTANCE_DRILL", "drill_kind": "PITR_RESTORE", "real_system": True,
        "observed_at": (datetime.now(timezone.utc) - timedelta(hours=nested_age_hours)).isoformat(),
        "git_commit_sha": git_sha,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": {"acceptance_environment_id_hash": "a"*64, "topology_hash": "b"*64},
        "artifacts": [{"path": "restore.log", "sha256": _sha(raw)}],
        "isolated_environment": True, "backup_or_pitr_restored": True, "schema_validated": True,
        "referential_integrity_validated": True, "checksum_validated": True, "read_only_smoke_passed": True,
        "result_reported": True,
    }
    nested_path = root / "pitr.json"; nested_path.write_text(json.dumps(nested), encoding="utf-8")
    run_id = "phase75-pitr-run"
    run_dir = reports / "runs" / run_id / "pitr"; run_dir.mkdir(parents=True, exist_ok=True)
    wrapper = run_dir / "pitr_wrapper.log"
    wrapper.write_text(json.dumps({"status": "PASS", "evidence_artifact": "pitr.json", "evidence_sha256": _sha(nested_path)}) + "\n", encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "3.2", "run_id": run_id, "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE", "generated_at": now,
        "profile": "pitr", "command_contract_sha256": command_contract_sha256("pitr"),
        "real_target_explicitly_confirmed": True, "challenge": challenge,
        "environment": {"git_commit_sha": git_sha, "acceptance_environment_id_hash": "a"*64, "topology_hash": "b"*64},
        "evidence": [{"key": "pitr_drill", "status": "PASS", "real_system": True, "exit_code": 0,
                      "blocker": None, "artifact": str(wrapper.relative_to(root)), "sha256": _sha(wrapper), "observed_at": now, "command": command_contract("pitr")["pitr_drill"]}],
        "groups": {"pitr": "PASS"}, "selected_all_pass": True,
    }
    manifest = root / "manifest.json"; manifest.write_text(json.dumps(payload), encoding="utf-8")
    append_entry(reports / "evidence_ledger.json", manifest_sha256=_sha(manifest), challenge_id=challenge["challenge_id"], git_commit_sha=git_sha, profile="pitr", root=root)
    return manifest


def test_nested_pitr_uses_group_specific_24h_ttl(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    result = verify_manifest(_pitr_bundle(tmp_path, nested_age_hours=30), root=tmp_path, max_age_hours=168)
    assert result["groups"]["pitr"] == "BLOCKED"
    assert any(p.startswith("DRILL_SUBARTIFACT_INVALID:pitr") for p in result["problems"])


def test_nested_pitr_group_ttl_override_applies_to_nested_receipt(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    result = verify_manifest(
        _pitr_bundle(tmp_path, nested_age_hours=30), root=tmp_path, max_age_hours=168, group_ttl_hours={"pitr": 48}
    )
    assert result["groups"]["pitr"] == "PASS"
    assert result["verified"] is True
