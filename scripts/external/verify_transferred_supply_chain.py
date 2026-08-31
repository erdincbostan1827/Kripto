from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.supply_chain_evidence import verify_supply_chain_artifacts
from scripts.ci_build_evidence_manifest import verify as verify_build_evidence
from scripts.external.verify_scanner_image_digests import verify as verify_scanner_digests


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def verify(root: Path = ROOT) -> dict:
    problems: list[str] = []
    expected_git = _git_sha(root)
    reports = root / "reports" / "external_acceptance"
    challenge = verify_challenge(reports / "release_challenge.json", root=root, require_trust=True)
    if not challenge.get("verified"):
        problems.append("RELEASE_CHALLENGE_NOT_VERIFIED")
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    environment = {
        "acceptance_environment_id_hash": hashlib.sha256(env_id.encode()).hexdigest() if env_id else None,
        "topology_hash": topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else None,
    }
    if not environment["acceptance_environment_id_hash"]:
        problems.append("ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING")
    if not environment["topology_hash"]:
        problems.append("ACCEPTANCE_TOPOLOGY_HASH_MISSING")
    manifest_path = root / "reports" / "CI_BUILD_EVIDENCE_MANIFEST.json"
    sbom = reports / "sbom.cdx.json"
    licenses = reports / "dependency_licenses.json"
    semantic_receipt = reports / "supply_chain_artifact_verification.json"
    scanner_receipt = reports / "scanner_image_digests.json"
    provenance_path = reports / "provenance.json"

    transfer = verify_build_evidence(manifest_path, root=root, expected_git_sha=expected_git)
    if not transfer.get("verified"):
        problems.extend(f"TRANSFER:{p}" for p in transfer.get("problems", []))

    semantic = verify_supply_chain_artifacts(sbom, licenses)
    if not semantic.get("verified"):
        problems.extend(f"SEMANTIC:{p}" for p in semantic.get("problems", []))

    scanners = verify_scanner_digests(scanner_receipt)
    if not scanners.get("verified"):
        problems.extend(f"SCANNERS:{p}" for p in scanners.get("problems", []))

    try:
        receipt = json.loads(semantic_receipt.read_text(encoding="utf-8"))
        if receipt.get("classification") != "SUPPLY_CHAIN_ARTIFACT_SEMANTIC_VERIFICATION":
            problems.append("SEMANTIC_RECEIPT_CLASSIFICATION_INVALID")
        if receipt.get("verified") is not True:
            problems.append("SEMANTIC_RECEIPT_NOT_VERIFIED")
        if receipt.get("sbom", {}).get("sha256") != (_sha(sbom) if sbom.is_file() else None):
            problems.append("SEMANTIC_RECEIPT_SBOM_HASH_MISMATCH")
        if receipt.get("license_report", {}).get("sha256") != (_sha(licenses) if licenses.is_file() else None):
            problems.append("SEMANTIC_RECEIPT_LICENSE_HASH_MISMATCH")
    except Exception as exc:
        problems.append(f"SEMANTIC_RECEIPT_INVALID:{type(exc).__name__}")

    provenance: dict = {}
    try:
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"PROVENANCE_INVALID:{type(exc).__name__}")
    if provenance:
        if provenance.get("classification") != "REAL_CI_BUILD_PROVENANCE":
            problems.append("PROVENANCE_CLASSIFICATION_INVALID")
        if provenance.get("git_commit_sha") != expected_git:
            problems.append("PROVENANCE_GIT_MISMATCH")
        bindings = {
            "dependency_lock_hash": root / "uv.lock",
            "frontend_lock_hash": root / "frontend" / "package-lock.json",
            "sbom_hash": sbom,
            "license_report_hash": licenses,
            "supply_chain_verification_hash": semantic_receipt,
            "scanner_image_digest_manifest_hash": scanner_receipt,
        }
        for key, path in bindings.items():
            if not path.is_file():
                problems.append(f"PROVENANCE_INPUT_MISSING:{key}")
            elif provenance.get(key) != _sha(path):
                problems.append(f"PROVENANCE_HASH_MISMATCH:{key}")
        digest = provenance.get("container_digest")
        if not isinstance(digest, str) or "@sha256:" not in digest:
            problems.append("PROVENANCE_CONTAINER_DIGEST_INVALID")
        if not provenance.get("frontend_artifact_hash"):
            problems.append("PROVENANCE_FRONTEND_ARTIFACT_HASH_MISSING")
        if not provenance.get("ci_run_id"):
            problems.append("PROVENANCE_CI_RUN_ID_MISSING")

    return {
        "schema_version": "2.0",
        "classification": "TRANSFERRED_CI_SUPPLY_CHAIN_ACCEPTANCE",
        "verified": not problems,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": expected_git,
        "release_challenge": {"challenge_id": challenge.get("challenge_id"), "sha256": challenge.get("sha256")},
        "environment": environment,
        "problems": problems,
        "transfer_manifest_sha256": transfer.get("manifest_sha256"),
        "scanner_receipt_sha256": scanners.get("sha256"),
        "sbom_sha256": _sha(sbom) if sbom.is_file() else None,
        "license_report_sha256": _sha(licenses) if licenses.is_file() else None,
        "provenance_sha256": _sha(provenance_path) if provenance_path.is_file() else None,
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
