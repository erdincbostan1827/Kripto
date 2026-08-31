from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from backend.app.release.provenance_signature_evidence import verify_provenance_signature_evidence


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / "seed").write_text("x")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _evidence(root: Path) -> Path:
    git = _git(root)
    reports = root / "reports/external_acceptance"
    reports.mkdir(parents=True)
    prov = reports / "provenance.json"
    sig = reports / "provenance.sig"
    prov.write_text('{"classification":"REAL_CI_BUILD_PROVENANCE"}')
    sig.write_text("detached-signature")
    evidence = reports / "provenance_signature_verification.json"
    evidence.write_text(json.dumps({
        "schema_version": "1.0",
        "classification": "REAL_PROVENANCE_SIGNATURE_VERIFICATION",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git,
        "real_system": True,
        "executed": True,
        "signature_verified": True,
        "signer_identity": "ci-signing-identity",
        "signature_mechanism": "test-detached-signature",
        "provenance_artifact": "reports/external_acceptance/provenance.json",
        "provenance_sha256": _sha(prov),
        "signature_artifact": "reports/external_acceptance/provenance.sig",
        "signature_sha256": _sha(sig),
    }))
    return evidence


def test_signature_evidence_validates_real_bound_artifacts(tmp_path: Path):
    result = verify_provenance_signature_evidence(_evidence(tmp_path), root=tmp_path)
    assert result["verified"] is True


def test_signature_evidence_rejects_signature_tamper(tmp_path: Path):
    path = _evidence(tmp_path)
    (tmp_path / "reports/external_acceptance/provenance.sig").write_text("tampered")
    result = verify_provenance_signature_evidence(path, root=tmp_path)
    assert result["verified"] is False
    assert "SIGNATURE_HASH_MISMATCH:signature_artifact" in result["problems"]


def test_signature_evidence_rejects_unverified_claim(tmp_path: Path):
    path = _evidence(tmp_path)
    doc = json.loads(path.read_text())
    doc["signature_verified"] = False
    path.write_text(json.dumps(doc))
    result = verify_provenance_signature_evidence(path, root=tmp_path)
    assert not result["verified"]
    assert "SIGNATURE_NOT_VERIFIED" in result["problems"]
