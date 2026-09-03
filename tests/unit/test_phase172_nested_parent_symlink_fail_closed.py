from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.release.acceptance_challenge import create_challenge, verify_challenge
from app.release.campaign_acceptance import CLASSIFICATIONS, verify_campaign_evidence
from app.release.path_integrity import PathIntegrityError
from app.release.provenance_signature_evidence import verify_provenance_signature_evidence


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p172@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P172"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_challenge_creation_rejects_symlinked_parent_directory(tmp_path: Path) -> None:
    _git(tmp_path)
    real_reports = tmp_path / "real-reports"
    (real_reports / "external_acceptance").mkdir(parents=True)
    os.symlink(real_reports, tmp_path / "reports", target_is_directory=True)
    with pytest.raises(PathIntegrityError, match="symlink component"):
        create_challenge(tmp_path, tmp_path / "reports" / "external_acceptance" / "release_challenge.json")


def test_release_challenge_verification_rejects_symlinked_parent_directory(tmp_path: Path, monkeypatch) -> None:
    _git(tmp_path)
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    challenge = reports / "release_challenge.json"
    create_challenge(tmp_path, challenge)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    real_reports = tmp_path / "real-reports"
    (tmp_path / "reports").rename(real_reports)
    os.symlink(real_reports, tmp_path / "reports", target_is_directory=True)
    result = verify_challenge(challenge, root=tmp_path, require_trust=True)
    assert result["verified"] is False
    assert result["problems"] == ["CHALLENGE_PATH_INTEGRITY_INVALID"]


def _campaign(tmp_path: Path, monkeypatch) -> tuple[Path, dict]:
    git_sha = _git(tmp_path)
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    challenge = create_challenge(tmp_path, reports / "release_challenge.json")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    env = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    real_dir = tmp_path / "real-artifacts"
    real_dir.mkdir()
    artifact = real_dir / "source.log"
    artifact.write_text("ok", encoding="utf-8")
    os.symlink(real_dir, tmp_path / "artifact-alias", target_is_directory=True)
    payload = {
        "schema_version": "1.0",
        "classification": CLASSIFICATIONS["private-stream"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "real_system": True,
        "executed": True,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": env,
        "source_artifacts": [{"path": "artifact-alias/source.log", "sha256": _sha(artifact)}],
        "metrics": {
            "credentialed_testnet": True,
            "auth_lifecycle_passed": True,
            "reconnect_passed": True,
            "rest_reconciliation_passed": True,
            "duplicate_event_idempotency_passed": True,
            "out_of_order_protection_passed": True,
            "secrets_redacted": True,
            "observed_events": 1,
        },
    }
    evidence = tmp_path / "campaign.json"
    evidence.write_text(json.dumps(payload), encoding="utf-8")
    return evidence, env


def test_strict_campaign_rejects_parent_symlink_source_artifact(tmp_path: Path, monkeypatch) -> None:
    evidence, env = _campaign(tmp_path, monkeypatch)
    result = verify_campaign_evidence(
        evidence,
        kind="private-stream",
        root=tmp_path,
        strict_external=True,
        expected_environment=env,
    )
    assert result["verified"] is False
    assert "SOURCE_ARTIFACT_PATH_INTEGRITY_INVALID:0" in result["problems"]


def _signature(tmp_path: Path, monkeypatch) -> tuple[Path, dict]:
    git_sha = _git(tmp_path)
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    challenge = create_challenge(tmp_path, reports / "release_challenge.json")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    env = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    provenance = reports / "provenance.json"
    provenance.write_text("{}", encoding="utf-8")
    real_sig_dir = reports / "real-signatures"
    real_sig_dir.mkdir()
    signature = real_sig_dir / "provenance.sig"
    signature.write_text("signature", encoding="utf-8")
    os.symlink(real_sig_dir, reports / "sig-alias", target_is_directory=True)
    evidence = reports / "provenance_signature_verification.json"
    evidence.write_text(json.dumps({
        "schema_version": "2.0",
        "classification": "REAL_PROVENANCE_SIGNATURE_VERIFICATION",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "real_system": True,
        "executed": True,
        "signature_verified": True,
        "signer_identity": "ci-signer",
        "signature_mechanism": "detached",
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": env,
        "provenance_artifact": "reports/external_acceptance/provenance.json",
        "provenance_sha256": _sha(provenance),
        "signature_artifact": "reports/external_acceptance/sig-alias/provenance.sig",
        "signature_sha256": _sha(signature),
    }), encoding="utf-8")
    return evidence, env


def test_strict_provenance_rejects_parent_symlink_signature_artifact(tmp_path: Path, monkeypatch) -> None:
    evidence, env = _signature(tmp_path, monkeypatch)
    result = verify_provenance_signature_evidence(
        evidence, root=tmp_path, strict_external=True, expected_environment=env
    )
    assert result["verified"] is False
    assert "SIGNATURE_ARTIFACT_PATH_INTEGRITY_INVALID:signature_artifact" in result["problems"]


def test_nested_verifiers_use_shared_strict_path_contract() -> None:
    for file in (
        "backend/app/release/drill_evidence.py",
        "backend/app/release/runtime_restart_evidence.py",
        "backend/app/release/campaign_acceptance.py",
        "backend/app/release/provenance_signature_evidence.py",
    ):
        text = Path(file).read_text(encoding="utf-8")
        assert "strict_regular_file" in text
