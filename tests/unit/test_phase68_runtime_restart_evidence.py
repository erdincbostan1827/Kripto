import pytest
import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.runtime_restart_evidence import CLASSIFICATION, REQUIRED_TRUE, verify_restart_evidence
from scripts.external_acceptance_runner import build_plan, _group_status, Evidence
from scripts.verify_external_acceptance import GROUP_KEYS




def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase68@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase68"], cwd=root, check=True)
    (root / "seed").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write_valid(tmp_path: Path, monkeypatch) -> Path:
    git_sha = _git(tmp_path)
    reports = tmp_path / "reports/external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(tmp_path, reports / "release_challenge.json")
    monkeypatch.setenv("ACCEPTANCE_ENVIRONMENT_ID", "isolated-prod-acceptance-01")
    monkeypatch.setenv("ACCEPTANCE_TOPOLOGY_HASH", "a" * 64)
    raw = reports / "restart.log"
    raw.write_text("state-before=42\nstate-after=42\nreconciled=12\n", encoding="utf-8")
    metrics = {k: True for k in REQUIRED_TRUE}
    metrics.update(reconciled_records=12, duplicate_orders_detected=0)
    payload = {
        "schema_version": "1.0",
        "classification": CLASSIFICATION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "real_system": True,
        "executed": True,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": {
            "acceptance_environment_id_hash": sha256(b"isolated-prod-acceptance-01").hexdigest(),
            "topology_hash": "a" * 64,
        },
        "source_artifacts": [{"path": str(raw.relative_to(tmp_path)), "sha256": _sha(raw)}],
        "metrics": metrics,
    }
    out = reports / "restart.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out


def test_restart_evidence_requires_state_reconciliation_and_fail_closed_risk(tmp_path, monkeypatch):
    path = _write_valid(tmp_path, monkeypatch)
    result = verify_restart_evidence(path, root=tmp_path)
    assert result["verified"], result
    doc = json.loads(path.read_text())
    doc["metrics"]["risk_fail_closed_during_outage"] = False
    path.write_text(json.dumps(doc))
    result = verify_restart_evidence(path, root=tmp_path)
    assert not result["verified"]
    assert any("risk_fail_closed_during_outage" in p for p in result["problems"])


def test_restart_evidence_binds_environment_and_topology(tmp_path, monkeypatch):
    path = _write_valid(tmp_path, monkeypatch)
    monkeypatch.setenv("ACCEPTANCE_TOPOLOGY_HASH", "b" * 64)
    result = verify_restart_evidence(path, root=tmp_path)
    assert "ACCEPTANCE_TOPOLOGY_MISMATCH" in result["problems"]


def test_restart_evidence_rejects_duplicate_orders(tmp_path, monkeypatch):
    path = _write_valid(tmp_path, monkeypatch)
    doc = json.loads(path.read_text())
    doc["metrics"]["duplicate_orders_detected"] = 1
    path.write_text(json.dumps(doc))
    result = verify_restart_evidence(path, root=tmp_path)
    assert "DUPLICATE_ORDERS_DETECTED" in result["problems"]


def test_restart_profile_requires_semantic_evidence_key():
    keys = [k for k, _, _ in build_plan("restart-drills")]
    assert keys[-1] == "restart_semantic_evidence"
    assert "restart_semantic_evidence" in GROUP_KEYS["restart_drills"]
    evidence = [
        Evidence(key=k, status="PASS", real_system=True, command=(), exit_code=0, blocker=None,
                 artifact="x", sha256="0" * 64, observed_at=datetime.now(timezone.utc).isoformat())
        for k in keys[:-1]
    ]
    assert _group_status(evidence)["restart_drills"] == "BLOCKED"


@pytest.fixture(autouse=True)
def _phase155_external_challenge_trust(monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
