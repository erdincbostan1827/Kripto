from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.drill_evidence import DrillEvidenceError, verify_restore_evidence


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p154@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P154"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _payload(root: Path) -> tuple[Path, dict, dict]:
    git_sha = _git(root)
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    artifact = root / "restore.log"
    artifact.write_text("restore-ok\n", encoding="utf-8")
    env = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    doc = {
        "schema_version": "2.0",
        "classification": "REAL_EXTERNAL_ACCEPTANCE_DRILL",
        "drill_kind": "PITR_RESTORE",
        "real_system": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": env,
        "artifacts": [{"path": "restore.log", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
        "isolated_environment": True,
        "backup_or_pitr_restored": True,
        "schema_validated": True,
        "referential_integrity_validated": True,
        "checksum_validated": True,
        "read_only_smoke_passed": True,
        "result_reported": True,
    }
    path = root / "pitr.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path, doc, env


def _trust(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')


def test_drill_evidence_is_bound_to_current_release_challenge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _trust(monkeypatch)
    path, doc, env = _payload(tmp_path)
    assert verify_restore_evidence(path, root=tmp_path, expected_environment=env)["drill_kind"] == "PITR_RESTORE"
    create_challenge(tmp_path, tmp_path / "reports" / "external_acceptance" / "release_challenge.json")
    with pytest.raises(DrillEvidenceError, match="challenge binding mismatch"):
        verify_restore_evidence(path, root=tmp_path, expected_environment=env)


def test_drill_evidence_cannot_be_replayed_on_different_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _trust(monkeypatch)
    path, doc, env = _payload(tmp_path)
    other = {"acceptance_environment_id_hash": "c" * 64, "topology_hash": env["topology_hash"]}
    with pytest.raises(DrillEvidenceError, match="environment mismatch"):
        verify_restore_evidence(path, root=tmp_path, expected_environment=other)


def test_drill_evidence_cannot_be_replayed_on_different_topology(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _trust(monkeypatch)
    path, doc, env = _payload(tmp_path)
    other = {"acceptance_environment_id_hash": env["acceptance_environment_id_hash"], "topology_hash": "d" * 64}
    with pytest.raises(DrillEvidenceError, match="topology mismatch"):
        verify_restore_evidence(path, root=tmp_path, expected_environment=other)
