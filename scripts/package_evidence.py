from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import zipfile
from pathlib import Path

try:
    from scripts.package_release import scan_zip_safety
except ModuleNotFoundError:  # direct script execution
    from package_release import scan_zip_safety

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT.parent
ARCHIVE = OUT_DIR / "crypto_trading_platform_v5_1_evidence-local.zip"
MANIFEST_NAME = "EVIDENCE_PACKAGE_MANIFEST.json"

CANONICAL_FILES = [
    "RELEASE_MANIFEST.json",
    "REQUIREMENTS_TRACEABILITY.md",
    "REQUIREMENTS_TRACEABILITY_MATRIX.yaml",
    "requirements_acceptance_matrix.yaml",
    "reports/PROJECT_STATUS.json",
    "reports/ACCEPTANCE_CLOSURE_STATUS.json",
        "reports/PHASE176_READINESS.json",
    "reports/PHASE177_ACCEPTANCE_CAPABILITIES.json",
    "reports/PHASE177_EXTERNAL_ACCEPTANCE_HANDOFF.zip",
    "reports/RELEASE_CONSISTENCY.json",
    "reports/KNOWN_ISSUES_LIMITATIONS.md",
    "reports/PRODUCTION_READINESS_DOSSIER.json",
    "reports/EXTERNAL_EXECUTION_PLAN_VERIFICATION.json",
    "reports/PRODUCTION_ACCEPTANCE_HANDOFF.json",
    "reports/LOCAL_SOURCE_PROVENANCE.json",
    "reports/LATEST_PYTEST.txt",
    "reports/LATEST_COVERAGE.txt",
    "reports/TEST_COUNT.txt",
    "reports/TEST_INVENTORY.json",
    "reports/TEST_COLLECTION.txt",
    "reports/SECRET_SCAN.txt",
    "reports/PROHIBITED_SCAN.txt",
    "reports/ALEMBIC_OFFLINE_SQL.txt",
    "reports/SBOM.local.json",
    "reports/REAL_MOCK_UNSUPPORTED_MATRIX.md",
    "reports/local_acceptance/full_regression_manifest.json",
    "reports/external_acceptance/manifest_all.json",
    "reports/external_acceptance/release_challenge.json",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.create_system = 3
    return info


def _external_referenced_files(root: Path) -> set[str]:
    """Return only files explicitly referenced by the canonical merged manifest.

    Missing or malformed manifests do not cause broad directory inclusion. This is
    deliberately fail-closed: an evidence archive never sweeps arbitrary logs.
    """
    manifest_path = root / "reports/external_acceptance/manifest_all.json"
    if not manifest_path.exists():
        return set()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    refs: set[str] = set()
    for item in data.get("evidence", []) or []:
        if not isinstance(item, dict):
            continue
        for key in ("evidence_path", "reference", "path"):
            value = item.get(key)
            if isinstance(value, str) and value.startswith("reports/external_acceptance/"):
                refs.add(value)
    for item in (data.get("source_profiles") or {}).values():
        if not isinstance(item, dict):
            continue
        value = item.get("reference")
        if isinstance(value, str) and value.startswith("reports/external_acceptance/"):
            refs.add(value)
    return refs



def _local_regression_referenced_files(root: Path) -> set[str]:
    manifest_path = root / "reports/local_acceptance/full_regression_manifest.json"
    if not manifest_path.exists():
        return set()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    refs: set[str] = set()
    for item in data.get("shards", []) or []:
        if not isinstance(item, dict):
            continue
        ref = item.get("manifest")
        if isinstance(ref, str) and ref.startswith("reports/local_acceptance/"):
            refs.add(ref)
            shard_path = root / ref
            try:
                shard = json.loads(shard_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            log = shard.get("log")
            if isinstance(log, str) and log.startswith("reports/local_acceptance/"):
                refs.add(log)
    return refs


def _local_coverage_referenced_files(root: Path) -> set[str]:
    manifest_path = root / "reports/local_coverage/full_coverage_manifest.json"
    if not manifest_path.exists():
        return set()
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    refs: set[str] = {"reports/local_coverage/full_coverage_manifest.json"}
    coverage_json = data.get("coverage_json")
    if isinstance(coverage_json, str) and coverage_json.startswith("reports/local_coverage/"):
        refs.add(coverage_json)
    for item in data.get("shards", []) or []:
        if not isinstance(item, dict):
            continue
        ref = item.get("manifest")
        if not isinstance(ref, str) or not ref.startswith("reports/local_coverage/"):
            continue
        refs.add(ref)
        shard_path = root / ref
        try:
            shard = json.loads(shard_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key in ("log", "coverage_data"):
            value = shard.get(key)
            if isinstance(value, str) and value.startswith("reports/local_coverage/"):
                refs.add(value)
    return refs

def _safe_reference(relative: str) -> bool:
    rel = Path(relative)
    return bool(rel.parts) and not rel.is_absolute() and ".." not in rel.parts and "\\" not in relative and "\x00" not in relative


def _path_has_symlink_component(root: Path, relative: str) -> bool:
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def collect_files(root: Path = ROOT) -> list[Path]:
    explicit_refs = (_external_referenced_files(root)
                     | _local_regression_referenced_files(root) | _local_coverage_referenced_files(root))
    rels = set(CANONICAL_FILES) | explicit_refs
    files: list[Path] = []
    root_resolved = root.resolve()
    for rel in sorted(rels):
        if not _safe_reference(rel):
            raise ValueError(f"EVIDENCE_REFERENCE_UNSAFE:{rel}")
        path = root / rel
        if _path_has_symlink_component(root, rel):
            raise ValueError(f"EVIDENCE_REFERENCE_SYMLINK_NOT_ALLOWED:{rel}")
        resolved = path.resolve()
        try:
            resolved.relative_to(root_resolved)
        except ValueError as exc:
            raise ValueError(f"EVIDENCE_REFERENCE_OUTSIDE_ROOT:{rel}") from exc
        if not resolved.is_file():
            if rel in explicit_refs:
                raise ValueError(f"EVIDENCE_REFERENCED_FILE_MISSING:{rel}")
            continue
        # Never package obvious secret material or environment files.
        if resolved.name.startswith(".env") or "secrets" in Path(rel).parts:
            if rel in explicit_refs:
                raise ValueError(f"EVIDENCE_REFERENCE_FORBIDDEN:{rel}")
            continue
        files.append(resolved)
    return files


def build_evidence_archive(root: Path = ROOT, archive: Path = ARCHIVE) -> tuple[Path, dict]:
    files = collect_files(root)
    entries = [
        {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p), "size": p.stat().st_size}
        for p in files
    ]
    manifest = {
        "schema_version": "1.0",
        "classification": "EVIDENCE_TRANSPORT_BUNDLE_NOT_ACCEPTANCE_BY_ITSELF",
        "git_commit_sha": git_sha(root),
        "truth_policy": "Archive integrity proves transport integrity only; acceptance status remains governed by release_gate and semantic verifiers.",
        "file_count": len(entries),
        "files": entries,
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    archive.unlink(missing_ok=True)
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for entry in entries:
            zf.writestr(_zip_info(entry["path"]), (root / entry["path"]).read_bytes())
        zf.writestr(_zip_info(MANIFEST_NAME), manifest_bytes)
    return archive, manifest


def verify_evidence_archive(archive: Path = ARCHIVE) -> dict:
    problems: list[str] = []
    with zipfile.ZipFile(archive, "r") as zf:
        problems.extend(f"ARCHIVE_SAFETY:{p}" for p in scan_zip_safety(zf))
        raw_names = zf.namelist()
        if len(raw_names) != len(set(raw_names)):
            problems.append("DUPLICATE_ARCHIVE_MEMBER")
        names = set(raw_names)
        if MANIFEST_NAME not in names:
            return {"verified": False, "problems": sorted(set(problems + ["MANIFEST_MISSING"]))}
        try:
            manifest = json.loads(zf.read(MANIFEST_NAME))
        except Exception as exc:
            return {"verified": False, "problems": sorted(set(problems + [f"MANIFEST_INVALID:{type(exc).__name__}"]))}
        if manifest.get("schema_version") != "1.0":
            problems.append("MANIFEST_SCHEMA_INVALID")
        if manifest.get("classification") != "EVIDENCE_TRANSPORT_BUNDLE_NOT_ACCEPTANCE_BY_ITSELF":
            problems.append("MANIFEST_CLASSIFICATION_INVALID")
        rows = manifest.get("files") if isinstance(manifest.get("files"), list) else []
        if manifest.get("file_count") != len(rows):
            problems.append("MANIFEST_FILE_COUNT_MISMATCH")
        expected_names = {MANIFEST_NAME}
        seen: set[str] = set()
        for entry in rows:
            if not isinstance(entry, dict):
                problems.append("MANIFEST_ENTRY_INVALID")
                continue
            name = entry.get("path")
            if not isinstance(name, str) or not _safe_reference(name):
                problems.append(f"MANIFEST_PATH_UNSAFE:{name}")
                continue
            if name in seen:
                problems.append(f"MANIFEST_DUPLICATE_PATH:{name}")
            seen.add(name)
            expected_names.add(name)
            if name not in names:
                problems.append(f"FILE_MISSING:{name}")
                continue
            data = zf.read(name)
            if hashlib.sha256(data).hexdigest() != entry.get("sha256"):
                problems.append(f"HASH_MISMATCH:{name}")
            if len(data) != entry.get("size"):
                problems.append(f"SIZE_MISMATCH:{name}")
            if Path(name).name.startswith(".env") or "secrets" in Path(name).parts:
                problems.append(f"FORBIDDEN:{name}")
        for extra in sorted(names - expected_names):
            problems.append(f"UNEXPECTED_MEMBER:{extra}")
    return {"verified": not problems, "problems": sorted(set(problems))}


def main() -> int:
    archive, manifest = build_evidence_archive()
    result = verify_evidence_archive(archive)
    digest = sha256_file(archive)
    print(json.dumps({"archive": str(archive), "sha256": digest, "file_count": manifest["file_count"] + 1, **result}))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
