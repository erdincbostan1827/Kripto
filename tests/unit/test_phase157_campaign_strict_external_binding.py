from pathlib import Path


def test_campaign_production_paths_enable_strict_external_mode():
    direct = Path("scripts/external/campaign_evidence_acceptance.py").read_text()
    aggregate = Path("scripts/verify_external_acceptance.py").read_text()
    assert "strict_external=True" in direct
    assert "strict_external=True" in aggregate
    assert "expected_environment=" in aggregate


def test_campaign_strict_mode_requires_trusted_challenge_and_environment_binding():
    text = Path("backend/app/release/campaign_acceptance.py").read_text()
    assert "require_trust=True if strict_external else None" in text
    assert "ACCEPTANCE_ENVIRONMENT_ID_MISMATCH" in text
    assert "ACCEPTANCE_TOPOLOGY_MISMATCH" in text
    assert "ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING" in text
    assert "ACCEPTANCE_TOPOLOGY_HASH_MISSING" in text

import hashlib
import json
import subprocess
from datetime import datetime, timezone

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.campaign_acceptance import CLASSIFICATIONS, verify_campaign_evidence


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p157@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P157"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _strict_payload(root: Path, monkeypatch):
    sha = _git(root)
    reports = root / "reports/external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
    env = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    artifact = root / "source.log"
    artifact.write_text("ok", encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "classification": CLASSIFICATIONS["private-stream"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": sha,
        "real_system": True,
        "executed": True,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": env,
        "source_artifacts": [{"path": "source.log", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
        "metrics": {"credentialed_testnet": True, "auth_lifecycle_passed": True, "reconnect_passed": True,
                    "rest_reconciliation_passed": True, "duplicate_event_idempotency_passed": True,
                    "out_of_order_protection_passed": True, "secrets_redacted": True, "observed_events": 1},
    }
    path = root / "campaign.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path, env


def test_strict_campaign_accepts_matching_trusted_environment(tmp_path, monkeypatch):
    path, env = _strict_payload(tmp_path, monkeypatch)
    result = verify_campaign_evidence(path, kind="private-stream", root=tmp_path, strict_external=True, expected_environment=env)
    assert result["verified"], result["problems"]


def test_strict_campaign_rejects_topology_replay(tmp_path, monkeypatch):
    path, env = _strict_payload(tmp_path, monkeypatch)
    other = {**env, "topology_hash": "c" * 64}
    result = verify_campaign_evidence(path, kind="private-stream", root=tmp_path, strict_external=True, expected_environment=other)
    assert not result["verified"]
    assert "ACCEPTANCE_TOPOLOGY_MISMATCH" in result["problems"]
