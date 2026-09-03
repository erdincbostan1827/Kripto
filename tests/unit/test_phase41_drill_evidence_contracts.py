from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.release.drill_evidence import (
    DrillEvidenceError,
    verify_ha_evidence,
    verify_restore_evidence,
    verify_worm_evidence,
)
from scripts.external_acceptance_runner import build_plan
from backend.app.release.acceptance_challenge import create_challenge


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _base(root: Path, kind: str) -> dict:
    artifact = root / "evidence.log"
    artifact.write_text("real drill evidence\n", encoding="utf-8")
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    return {
        "schema_version": "2.0",
        "classification": "REAL_EXTERNAL_ACCEPTANCE_DRILL",
        "drill_kind": kind,
        "real_system": True,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": _git_sha(root),
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64},
        "artifacts": [{"path": "evidence.log", "sha256": _sha(artifact)}],
    }


def _write(root: Path, payload: dict) -> Path:
    path = root / "drill.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_restore_requires_all_semantic_checks(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "seed").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=tmp_path, check=True)
    p = _base(tmp_path, "PITR_RESTORE")
    for key in ("isolated_environment", "backup_or_pitr_restored", "schema_validated", "referential_integrity_validated", "checksum_validated", "read_only_smoke_passed", "result_reported"):
        p[key] = True
    assert verify_restore_evidence(_write(tmp_path, p), root=tmp_path, expected_environment=p["environment"])["drill_kind"] == "PITR_RESTORE"
    p["schema_validated"] = False
    with pytest.raises(DrillEvidenceError):
        verify_restore_evidence(_write(tmp_path, p), root=tmp_path, expected_environment=p["environment"])


def test_hash_tampering_is_rejected(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "seed").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=tmp_path, check=True)
    p = _base(tmp_path, "WORM_STORAGE")
    p.update({k: True for k in ("append_only_verified", "retention_lock_verified", "delete_before_retention_denied", "overwrite_denied", "readback_verified")})
    p.update(provider="test-provider", retention_policy_reference="policy-1")
    path = _write(tmp_path, p)
    (tmp_path / "evidence.log").write_text("tampered")
    with pytest.raises(DrillEvidenceError, match="hash mismatch"):
        verify_worm_evidence(path, root=tmp_path, expected_environment=p["environment"])


def test_ha_redis_is_conditional(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "seed").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=tmp_path, check=True)
    p = _base(tmp_path, "HA_FAILOVER")
    p.update({k: True for k in ("active_process_kill_passed", "stale_leader_fencing_passed", "private_stream_reconciliation_passed", "host_loss_simulation_passed", "db_failover_passed", "network_partition_passed")})
    p["redis_ha_applicable"] = True
    p["redis_failover_passed"] = False
    with pytest.raises(DrillEvidenceError, match="redis failover"):
        verify_ha_evidence(_write(tmp_path, p), root=tmp_path, expected_environment=p["environment"])
    p["redis_failover_passed"] = True
    assert verify_ha_evidence(_write(tmp_path, p), root=tmp_path, expected_environment=p["environment"])["drill_kind"] == "HA_FAILOVER"


def test_wrong_git_commit_is_rejected(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "seed").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=tmp_path, check=True)
    p = _base(tmp_path, "WORM_STORAGE")
    p.update({k: True for k in ("append_only_verified", "retention_lock_verified", "delete_before_retention_denied", "overwrite_denied", "readback_verified")})
    p.update(provider="test-provider", retention_policy_reference="policy-1", git_commit_sha="0" * 40)
    with pytest.raises(DrillEvidenceError, match="git commit"):
        verify_worm_evidence(_write(tmp_path, p), root=tmp_path, expected_environment=p["environment"])


def test_runner_exposes_worm_profile() -> None:
    assert build_plan("worm") == [
        ("worm_storage", ["python", "scripts/external/run_approved_drill.py", "worm"], True)
    ]
    assert any(key == "worm_storage" for key, _, _ in build_plan("all"))


@pytest.fixture(autouse=True)
def _phase155_external_challenge_trust(monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
