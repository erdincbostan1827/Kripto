from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "phase246" / "CAMPAIGN_BUNDLE_TRANSFER_VERIFICATION.json"
MANIFEST_NAME = "CAMPAIGN_BUNDLE_MANIFEST.json"
CLASSIFICATION = "PHASE246_CAMPAIGN_EVIDENCE_TRANSFER_BUNDLE"
MAX_FILES = 1000
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_MEMBER_BYTES = 256 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {
    "reports/external_acceptance/release_challenge.json",
    "reports/external_acceptance/campaign/private_stream.json",
    "reports/external_acceptance/campaign/paper_campaign.json",
    "reports/external_acceptance/campaign/live_shadow.json",
    "reports/external_acceptance/campaign/profitability.json",
}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> str:
    if "\\" in name or "\x00" in name:
        raise ValueError("ARCHIVE_MEMBER_NAME_INVALID")
    pure = PurePosixPath(name)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("ARCHIVE_MEMBER_PATH_UNSAFE")
    normalized = pure.as_posix()
    if normalized == MANIFEST_NAME:
        return normalized
    if not normalized.startswith("reports/external_acceptance/"):
        raise ValueError("ARCHIVE_MEMBER_OUTSIDE_ACCEPTANCE_ROOT")
    return normalized


def _json_bytes(data: bytes, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"{label}_INVALID_JSON:{type(exc).__name__}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label}_JSON_ROOT_INVALID")
    return payload


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def verify_and_stage(bundle: Path, *, expected_sha256: str, expected_candidate: str, root: Path = ROOT) -> dict[str, Any]:
    problems: list[str] = []
    expected_digest = expected_sha256.strip().lower()
    candidate = expected_candidate.strip().lower()
    if not SHA256_RE.fullmatch(expected_digest):
        problems.append("EXPECTED_BUNDLE_SHA256_INVALID")
    if not GIT_SHA_RE.fullmatch(candidate):
        problems.append("EXPECTED_CANDIDATE_SHA_INVALID")
    if not bundle.is_absolute():
        problems.append("BUNDLE_PATH_MUST_BE_ABSOLUTE")
    if not bundle.is_file():
        problems.append("BUNDLE_FILE_MISSING")
    if problems:
        return {"verified": False, "problems": problems}

    actual_digest = _sha_file(bundle)
    if actual_digest != expected_digest:
        return {"verified": False, "bundle_sha256": actual_digest, "problems": ["BUNDLE_SHA256_MISMATCH"]}

    try:
        with zipfile.ZipFile(bundle, "r") as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            if not infos or len(infos) > MAX_FILES:
                raise ValueError("ARCHIVE_FILE_COUNT_INVALID")
            total = 0
            normalized: dict[str, zipfile.ZipInfo] = {}
            for info in infos:
                name = _safe_member(info.filename)
                if name in normalized:
                    raise ValueError("ARCHIVE_DUPLICATE_MEMBER")
                if _is_symlink(info):
                    raise ValueError("ARCHIVE_SYMLINK_FORBIDDEN")
                if info.file_size < 0 or info.file_size > MAX_MEMBER_BYTES:
                    raise ValueError("ARCHIVE_MEMBER_SIZE_INVALID")
                total += info.file_size
                if total > MAX_TOTAL_BYTES:
                    raise ValueError("ARCHIVE_TOTAL_SIZE_EXCEEDED")
                normalized[name] = info

            manifest_info = normalized.get(MANIFEST_NAME)
            if manifest_info is None:
                raise ValueError("BUNDLE_MANIFEST_MISSING")
            manifest = _json_bytes(archive.read(manifest_info), label="BUNDLE_MANIFEST")
            if manifest.get("schema_version") != "1.0":
                raise ValueError("BUNDLE_SCHEMA_UNSUPPORTED")
            if manifest.get("classification") != CLASSIFICATION:
                raise ValueError("BUNDLE_CLASSIFICATION_INVALID")
            if str(manifest.get("candidate_sha", "")).lower() != candidate:
                raise ValueError("BUNDLE_CANDIDATE_SHA_MISMATCH")
            environment_id = manifest.get("acceptance_environment_id")
            topology_hash = str(manifest.get("topology_hash", "")).lower()
            if not isinstance(environment_id, str) or not environment_id.strip():
                raise ValueError("BUNDLE_ENVIRONMENT_ID_MISSING")
            if not SHA256_RE.fullmatch(topology_hash):
                raise ValueError("BUNDLE_TOPOLOGY_HASH_INVALID")
            raw_files = manifest.get("files")
            if not isinstance(raw_files, dict) or not raw_files:
                raise ValueError("BUNDLE_FILE_MANIFEST_INVALID")
            file_hashes = {str(key): str(value).lower() for key, value in raw_files.items()}
            expected_members = set(normalized) - {MANIFEST_NAME}
            if set(file_hashes) != expected_members:
                raise ValueError("BUNDLE_FILE_SET_MISMATCH")
            if not REQUIRED.issubset(expected_members):
                raise ValueError("BUNDLE_REQUIRED_EVIDENCE_MISSING")

            extracted: dict[str, bytes] = {}
            for name in sorted(expected_members):
                if not SHA256_RE.fullmatch(file_hashes[name]):
                    raise ValueError("BUNDLE_MEMBER_SHA256_INVALID")
                data = archive.read(normalized[name])
                if len(data) != normalized[name].file_size:
                    raise ValueError("BUNDLE_MEMBER_SIZE_MISMATCH")
                if _sha_bytes(data) != file_hashes[name]:
                    raise ValueError("BUNDLE_MEMBER_SHA256_MISMATCH")
                extracted[name] = data

            referenced_sources: set[str] = set()
            for receipt in REQUIRED - {"reports/external_acceptance/release_challenge.json"}:
                payload = _json_bytes(extracted[receipt], label="CAMPAIGN_RECEIPT")
                artifacts = payload.get("source_artifacts")
                if not isinstance(artifacts, list) or not artifacts:
                    raise ValueError("CAMPAIGN_SOURCE_ARTIFACTS_MISSING")
                for row in artifacts:
                    if not isinstance(row, dict):
                        raise ValueError("CAMPAIGN_SOURCE_ARTIFACT_INVALID")
                    source = _safe_member(str(row.get("path", "")))
                    expected = str(row.get("sha256", "")).lower()
                    if source not in extracted or not SHA256_RE.fullmatch(expected):
                        raise ValueError("CAMPAIGN_SOURCE_ARTIFACT_NOT_BUNDLED")
                    if _sha_bytes(extracted[source]) != expected:
                        raise ValueError("CAMPAIGN_SOURCE_ARTIFACT_HASH_MISMATCH")
                    referenced_sources.add(source)

            for name, data in extracted.items():
                target = (root / name).resolve()
                target.relative_to(root.resolve())
                if target.exists():
                    raise ValueError("STAGING_DESTINATION_ALREADY_EXISTS")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    except (OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        return {
            "verified": False,
            "bundle_sha256": actual_digest,
            "problems": [str(exc) or type(exc).__name__],
        }

    return {
        "schema_version": "1.0",
        "classification": "PHASE246_CAMPAIGN_BUNDLE_TRANSFER_VERIFICATION",
        "verified": True,
        "bundle_sha256": actual_digest,
        "candidate_sha": candidate,
        "acceptance_environment_id": environment_id,
        "acceptance_environment_id_sha256": hashlib.sha256(environment_id.encode()).hexdigest(),
        "topology_hash": topology_hash,
        "staged_file_count": len(extracted),
        "referenced_source_artifact_count": len(referenced_sources),
        "problems": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and stage a release-bound campaign evidence ZIP")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-candidate", required=True)
    parser.add_argument("--output", default=str(REPORT.relative_to(ROOT)))
    args = parser.parse_args()
    bundle = Path(args.bundle).expanduser().resolve()
    result = verify_and_stage(bundle, expected_sha256=args.expected_sha256, expected_candidate=args.expected_candidate)
    output = (ROOT / args.output).resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        print(json.dumps({"verified": False, "problems": ["OUTPUT_PATH_OUTSIDE_ROOT"]}, sort_keys=True))
        return 2
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
