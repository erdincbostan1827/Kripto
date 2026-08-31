from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.acceptance_contract import PROFILE_ORDER, PROFILE_TO_GROUPS
from backend.app.release.provenance_signature_evidence import verify_provenance_signature_evidence
import scripts.verify_external_acceptance as verifier


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p167@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P167"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _aggregate_payload(root: Path) -> dict:
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    environment = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    sources: dict[str, dict] = {}
    aggregate_evidence: list[dict] = []
    for profile in PROFILE_ORDER:
        profile_evidence = [
            {"key": key, "source_profile": profile, "observed_at": "2026-08-30T00:00:00+00:00"}
            for group in PROFILE_TO_GROUPS[profile]
            for key in verifier.GROUP_KEYS[group]
        ]
        aggregate_evidence.extend(profile_evidence)
        path = reports / f"manifest_{profile}.json"
        path.write_text(json.dumps({"profile": profile, "environment": environment, "evidence": profile_evidence}), encoding="utf-8")
        sources[profile] = {
            "status": "VERIFIED",
            "reference": str(path.relative_to(root)),
            "sha256": _sha(path),
            "problems": [],
        }
    return {"source_profiles": sources, "environment": environment, "evidence": aggregate_evidence}


def _fake_verify(path: Path, *, root: Path, max_age_hours: int = 168, group_ttl_hours=None):
    profile = path.stem.removeprefix("manifest_")
    return {"verified": True, "profile": profile, "groups": {g: "PASS" for g in PROFILE_TO_GROUPS[profile]}}


def test_aggregate_exactly_rebinds_evidence_rows_to_source_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _aggregate_payload(tmp_path)
    monkeypatch.setattr(verifier, "verify_manifest", _fake_verify)
    assert verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168) == []

    payload["evidence"][0]["observed_at"] = "2099-01-01T00:00:00+00:00"
    problems = verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168)
    assert f"AGGREGATE_EVIDENCE_ROW_MISMATCH:{payload['evidence'][0]['key']}" in problems


def _signature_evidence(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict]:
    git_sha = _git(root)
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(root, reports / "release_challenge.json")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
    env = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    prov = reports / "provenance.json"
    sig = reports / "provenance.sig"
    prov.write_text('{"classification":"REAL_CI_BUILD_PROVENANCE"}', encoding="utf-8")
    sig.write_text("detached-signature", encoding="utf-8")
    evidence = reports / "provenance_signature_verification.json"
    evidence.write_text(json.dumps({
        "schema_version": "2.0",
        "classification": "REAL_PROVENANCE_SIGNATURE_VERIFICATION",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "real_system": True,
        "executed": True,
        "signature_verified": True,
        "signer_identity": "ci-signing-identity",
        "signature_mechanism": "test-detached-signature",
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "environment": env,
        "provenance_artifact": "reports/external_acceptance/provenance.json",
        "provenance_sha256": _sha(prov),
        "signature_artifact": "reports/external_acceptance/provenance.sig",
        "signature_sha256": _sha(sig),
    }), encoding="utf-8")
    return evidence, env


def test_strict_provenance_signature_binds_trusted_challenge_and_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, env = _signature_evidence(tmp_path, monkeypatch)
    result = verify_provenance_signature_evidence(path, root=tmp_path, strict_external=True, expected_environment=env)
    assert result["verified"] is True

    other = {"acceptance_environment_id_hash": "c" * 64, "topology_hash": env["topology_hash"]}
    result = verify_provenance_signature_evidence(path, root=tmp_path, strict_external=True, expected_environment=other)
    assert result["verified"] is False
    assert "SIGNATURE_ENVIRONMENT_MISMATCH" in result["problems"]


def test_strict_provenance_signature_rejects_release_challenge_rotation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, env = _signature_evidence(tmp_path, monkeypatch)
    create_challenge(tmp_path, tmp_path / "reports" / "external_acceptance" / "release_challenge.json")
    result = verify_provenance_signature_evidence(path, root=tmp_path, strict_external=True, expected_environment=env)
    assert result["verified"] is False
    assert "SIGNATURE_RELEASE_CHALLENGE_MISMATCH" in result["problems"]


def test_strict_provenance_signature_rejects_signature_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, env = _signature_evidence(tmp_path, monkeypatch)
    reports = tmp_path / "reports" / "external_acceptance"
    real_sig = reports / "provenance.real.sig"
    (reports / "provenance.sig").replace(real_sig)
    (reports / "provenance.sig").symlink_to(real_sig.name)
    doc = json.loads(path.read_text())
    doc["signature_sha256"] = _sha(real_sig)
    path.write_text(json.dumps(doc), encoding="utf-8")
    result = verify_provenance_signature_evidence(path, root=tmp_path, strict_external=True, expected_environment=env)
    assert result["verified"] is False
    assert "SIGNATURE_ARTIFACT_SYMLINK_NOT_ALLOWED:signature_artifact" in result["problems"]


def test_transferred_supply_chain_receipt_binds_trusted_challenge_and_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.external.verify_transferred_supply_chain as supply

    git_sha = _git(tmp_path)
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(tmp_path, reports / "release_challenge.json")
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
    monkeypatch.setenv("ACCEPTANCE_ENVIRONMENT_ID", "phase167-real-target")
    monkeypatch.setenv("ACCEPTANCE_TOPOLOGY_HASH", "b" * 64)

    (tmp_path / "frontend").mkdir(parents=True, exist_ok=True)
    (tmp_path / "uv.lock").write_text("uv-lock", encoding="utf-8")
    (tmp_path / "frontend" / "package-lock.json").write_text("{}", encoding="utf-8")
    sbom = reports / "sbom.cdx.json"
    licenses = reports / "dependency_licenses.json"
    semantic_receipt = reports / "supply_chain_artifact_verification.json"
    scanner_receipt = reports / "scanner_image_digests.json"
    provenance = reports / "provenance.json"
    transfer_manifest = tmp_path / "reports" / "CI_BUILD_EVIDENCE_MANIFEST.json"
    sbom.write_text("{}", encoding="utf-8")
    licenses.write_text("{}", encoding="utf-8")
    scanner_receipt.write_text("{}", encoding="utf-8")
    semantic_receipt.write_text(json.dumps({
        "classification": "SUPPLY_CHAIN_ARTIFACT_SEMANTIC_VERIFICATION",
        "verified": True,
        "sbom": {"sha256": _sha(sbom)},
        "license_report": {"sha256": _sha(licenses)},
    }), encoding="utf-8")
    transfer_manifest.write_text("{}", encoding="utf-8")
    provenance.write_text(json.dumps({
        "classification": "REAL_CI_BUILD_PROVENANCE",
        "git_commit_sha": git_sha,
        "ci_run_id": "167",
        "dependency_lock_hash": _sha(tmp_path / "uv.lock"),
        "frontend_lock_hash": _sha(tmp_path / "frontend" / "package-lock.json"),
        "sbom_hash": _sha(sbom),
        "license_report_hash": _sha(licenses),
        "supply_chain_verification_hash": _sha(semantic_receipt),
        "scanner_image_digest_manifest_hash": _sha(scanner_receipt),
        "container_digest": "repo@sha256:" + "d" * 64,
        "frontend_artifact_hash": "e" * 64,
    }), encoding="utf-8")

    monkeypatch.setattr(supply, "verify_build_evidence", lambda *a, **k: {"verified": True, "problems": [], "manifest_sha256": "1" * 64})
    monkeypatch.setattr(supply, "verify_supply_chain_artifacts", lambda *a, **k: {"verified": True, "problems": []})
    monkeypatch.setattr(supply, "verify_scanner_digests", lambda *a, **k: {"verified": True, "problems": [], "sha256": "2" * 64})

    result = supply.verify(tmp_path)
    assert result["verified"] is True
    assert result["schema_version"] == "2.0"
    assert result["release_challenge"] == {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]}
    assert result["environment"]["acceptance_environment_id_hash"] == hashlib.sha256(b"phase167-real-target").hexdigest()
    assert result["environment"]["topology_hash"] == "b" * 64
