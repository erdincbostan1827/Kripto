from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.supply_chain_evidence import verify_supply_chain_artifacts
from scripts.bounded_subprocess import run_captured_split
from scripts.external.verify_scanner_image_digests import verify as verify_scanner_image_digests

REPORTS = ROOT / "reports"
EXTERNAL = REPORTS / "external_acceptance"
DEFAULT_OUT = REPORTS / "phase245" / "PHASE225_TRANSFER_VERIFICATION.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IMMUTABLE_DIGEST_RE = re.compile(r"^ghcr\.io/.+@sha256:[0-9a-f]{64}$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def _git_sha() -> str:
    proc = run_captured_split(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=10)
    value = (proc.stdout or "").strip().lower()
    if proc.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise RuntimeError("GIT_REV_PARSE_FAILED")
    return value


def verify(expected_sha: str) -> dict:
    problems: list[str] = []
    expected = expected_sha.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        problems.append("EXPECTED_SHA_INVALID")

    try:
        actual = _git_sha()
    except Exception as exc:
        actual = "UNAVAILABLE"
        problems.append(f"GIT_SHA_UNAVAILABLE:{type(exc).__name__}")
    if actual != expected:
        problems.append("CHECKED_OUT_SHA_MISMATCH")

    build_path = REPORTS / "phase225" / "PRODUCTION_BUILD_EVIDENCE.json"
    provenance_path = EXTERNAL / "provenance.json"
    sbom_path = EXTERNAL / "sbom.cdx.json"
    license_path = EXTERNAL / "dependency_licenses.json"
    semantic_path = EXTERNAL / "supply_chain_artifact_verification.json"
    scanner_path = EXTERNAL / "scanner_image_digests.json"

    required = (build_path, provenance_path, sbom_path, license_path, semantic_path, scanner_path)
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    problems.extend(f"TRANSFER_FILE_MISSING:{path}" for path in missing)

    build: dict = {}
    provenance: dict = {}
    semantic_receipt: dict = {}
    if build_path.is_file():
        try:
            build = _json(build_path)
        except Exception as exc:
            problems.append(f"BUILD_RECEIPT_INVALID:{type(exc).__name__}")
    if provenance_path.is_file():
        try:
            provenance = _json(provenance_path)
        except Exception as exc:
            problems.append(f"PROVENANCE_INVALID:{type(exc).__name__}")
    if semantic_path.is_file():
        try:
            semantic_receipt = _json(semantic_path)
        except Exception as exc:
            problems.append(f"SEMANTIC_RECEIPT_INVALID:{type(exc).__name__}")

    if build:
        if build.get("classification") != "PRODUCTION_BUILD_EVIDENCE_HOSTED_ONLY":
            problems.append("BUILD_RECEIPT_CLASSIFICATION_INVALID")
        if build.get("verified") is not True:
            problems.append("BUILD_RECEIPT_NOT_VERIFIED")
        if str(build.get("git_commit_sha", "")).lower() != expected:
            problems.append("BUILD_RECEIPT_GIT_MISMATCH")
        truth = build.get("truth_boundary") if isinstance(build.get("truth_boundary"), dict) else {}
        if truth.get("hosted_build_evidence_passed") is not True:
            problems.append("BUILD_RECEIPT_HOSTED_GATE_NOT_PASS")
        for key in (
            "real_target_acceptance_claimed",
            "credentialed_testnet_claimed",
            "restart_pitr_ha_worm_claimed",
            "trusted_signing_claimed",
            "production_live_accepted",
        ):
            if truth.get(key) is not False:
                problems.append(f"BUILD_RECEIPT_TRUTH_BOUNDARY_INVALID:{key}")
        if sbom_path.is_file() and build.get("sbom_sha256") != _sha(sbom_path):
            problems.append("BUILD_RECEIPT_SBOM_HASH_MISMATCH")
        if provenance_path.is_file() and build.get("provenance_sha256") != _sha(provenance_path):
            problems.append("BUILD_RECEIPT_PROVENANCE_HASH_MISMATCH")
        image = build.get("acceptance_image")
        digest = build.get("acceptance_image_digest")
        if not isinstance(image, str) or not image.lower().endswith(f":{expected}"):
            problems.append("BUILD_RECEIPT_IMAGE_TAG_INVALID")
        if not isinstance(digest, str) or IMMUTABLE_DIGEST_RE.fullmatch(digest.lower()) is None:
            problems.append("BUILD_RECEIPT_IMAGE_DIGEST_INVALID")

    if provenance:
        if provenance.get("classification") != "REAL_CI_BUILD_PROVENANCE":
            problems.append("PROVENANCE_CLASSIFICATION_INVALID")
        if str(provenance.get("git_commit_sha", "")).lower() != expected:
            problems.append("PROVENANCE_GIT_MISMATCH")
        bindings = {
            "dependency_lock_hash": ROOT / "uv.lock",
            "frontend_lock_hash": ROOT / "frontend" / "package-lock.json",
            "sbom_hash": sbom_path,
            "license_report_hash": license_path,
            "supply_chain_verification_hash": semantic_path,
            "scanner_image_digest_manifest_hash": scanner_path,
        }
        for key, path in bindings.items():
            if not path.is_file():
                problems.append(f"PROVENANCE_INPUT_MISSING:{key}")
            elif provenance.get(key) != _sha(path):
                problems.append(f"PROVENANCE_HASH_MISMATCH:{key}")
        if not isinstance(provenance.get("frontend_artifact_hash"), str) or not SHA256_RE.fullmatch(
            str(provenance.get("frontend_artifact_hash", "")).lower()
        ):
            problems.append("PROVENANCE_FRONTEND_HASH_INVALID")
        if not provenance.get("ci_run_id"):
            problems.append("PROVENANCE_CI_RUN_ID_MISSING")
        if build:
            if provenance.get("container_image") != build.get("acceptance_image"):
                problems.append("PROVENANCE_IMAGE_MISMATCH")
            if provenance.get("container_digest") != build.get("acceptance_image_digest"):
                problems.append("PROVENANCE_IMAGE_DIGEST_MISMATCH")

    if sbom_path.is_file() and license_path.is_file():
        semantic = verify_supply_chain_artifacts(sbom_path, license_path)
        if not semantic.get("verified"):
            problems.extend(f"SUPPLY_CHAIN:{problem}" for problem in semantic.get("problems", []))
    if semantic_receipt:
        if semantic_receipt.get("classification") != "SUPPLY_CHAIN_ARTIFACT_SEMANTIC_VERIFICATION":
            problems.append("SEMANTIC_RECEIPT_CLASSIFICATION_INVALID")
        if semantic_receipt.get("verified") is not True:
            problems.append("SEMANTIC_RECEIPT_NOT_VERIFIED")
        if sbom_path.is_file() and semantic_receipt.get("sbom", {}).get("sha256") != _sha(sbom_path):
            problems.append("SEMANTIC_RECEIPT_SBOM_HASH_MISMATCH")
        if license_path.is_file() and semantic_receipt.get("license_report", {}).get("sha256") != _sha(license_path):
            problems.append("SEMANTIC_RECEIPT_LICENSE_HASH_MISMATCH")

    if scanner_path.is_file():
        scanner = verify_scanner_image_digests(scanner_path)
        if not scanner.get("verified"):
            problems.extend(f"SCANNER:{problem}" for problem in scanner.get("problems", []))

    return {
        "schema_version": "1.0",
        "classification": "PHASE225_TRANSFER_VERIFICATION",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified": not problems,
        "expected_git_commit_sha": expected,
        "checked_out_git_commit_sha": actual,
        "phase225_build_receipt_sha256": _sha(build_path) if build_path.is_file() else None,
        "hosted_provenance_sha256": _sha(provenance_path) if provenance_path.is_file() else None,
        "acceptance_image": build.get("acceptance_image") if build else None,
        "acceptance_image_digest": build.get("acceptance_image_digest") if build else None,
        "problems": problems,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", default=str(DEFAULT_OUT.relative_to(ROOT)))
    args = parser.parse_args()
    result = verify(args.expected_sha)
    output = (ROOT / args.output).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        print(json.dumps({"verified": False, "problems": ["OUTPUT_PATH_OUTSIDE_ROOT"]}, sort_keys=True))
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
