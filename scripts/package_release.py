from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ID = "0.3.0-local-acceptance"
OUTPUT_DIR = ROOT.parent
ARCHIVE = OUTPUT_DIR / f"crypto_trading_platform_v5_1_{RELEASE_ID}.zip"
CHECKSUM_FILE = OUTPUT_DIR / "SHA256SUMS.txt"
PACKAGE_MANIFEST = ROOT / "PACKAGE_MANIFEST.json"

EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    ".vite",
    ".venv",
    "venv",
    "secrets",
}
EXCLUDED_NAMES = {
    ".coverage",
    "coverage.xml",
    "pytest.xml",
    "PACKAGE_MANIFEST.json",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".tsbuildinfo"}
EXCLUDED_PREFIXES = (".coverage.",)

MAX_ARCHIVE_MEMBER_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_MANIFEST_BYTES = 16 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
WINDOWS_RESERVED_BASENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

# Release source archives intentionally exclude historical/ephemeral execution
# evidence. Acceptance evidence is shipped separately by package_evidence.py.
CANONICAL_REPORT_FILES = {
    "KNOWN_ISSUES_LIMITATIONS.md",
    "LATEST_COVERAGE.txt",
    "LATEST_PYTEST.txt",
    "PRODUCTION_READINESS_DOSSIER.json",
    "EXTERNAL_EXECUTION_PLAN_VERIFICATION.json",
    "PRODUCTION_ACCEPTANCE_HANDOFF.json",
    "PROJECT_STATUS.json",
    "RELEASE_CONSISTENCY.json",
    "REAL_MOCK_UNSUPPORTED_MATRIX.md",
    "SBOM.local.json",
    "TEST_COUNT.txt",
    "TEST_INVENTORY.json",
    "TEST_COLLECTION.txt",
    "ALEMBIC_OFFLINE_SQL.txt",
    "ACCEPTANCE_CLOSURE_STATUS.json",
        "PHASE176_READINESS.json",
    "PHASE177_ACCEPTANCE_CAPABILITIES.json",
    "SECRET_SCAN.txt",
    "PROHIBITED_SCAN.txt",
    "DEPENDENCY_POLICY.txt",
    "LOCAL_SOURCE_PROVENANCE.json",
    "PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md",
}

def _report_allowed(rel: Path) -> bool:
    if not rel.parts or rel.parts[0] != "reports":
        return True
    if len(rel.parts) != 2:
        return False
    return rel.name in CANONICAL_REPORT_FILES


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_sha(root: Path) -> str | None:
    try:
        value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None
    return value if len(value) == 40 else None


def _content_set_sha256(entries: list[dict]) -> str:
    normalized = [
        {"path": row["path"], "sha256": row["sha256"], "size": int(row["size"]), "executable": bool(row.get("executable", False))}
        for row in sorted(entries, key=lambda item: item["path"])
    ]
    data = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_release_files(root: Path = ROOT):
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        rel = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if (
            path.name in EXCLUDED_NAMES
            or path.suffix in EXCLUDED_SUFFIXES
            or any(path.name.startswith(prefix) for prefix in EXCLUDED_PREFIXES)
        ):
            continue
        if not _report_allowed(rel):
            continue
        # Never follow source-tree symlinks into the release archive.  A
        # symlink could otherwise read bytes outside the repository and silently
        # re-materialize them as a regular ZIP member.
        if path.is_symlink():
            raise ValueError(f"SOURCE_RELEASE_SYMLINK_NOT_ALLOWED:{rel.as_posix()}")
        if not path.is_file():
            continue
        yield path


def make_manifest(root: Path = ROOT) -> dict:
    entries = []
    for path in iter_release_files(root):
        rel = path.relative_to(root).as_posix()
        entries.append({
            "path": rel,
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
            "executable": bool(path.stat().st_mode & stat.S_IXUSR),
        })
    return {
        "schema_version": 2,
        "release_id": RELEASE_ID,
        "classification": "LOCAL_ACCEPTANCE_NOT_PRODUCTION_READY",
        "secrets_included": False,
        "file_count": len(entries),
        "package_role": "SOURCE_RELEASE_ARCHIVE",
        "content_set_sha256": _content_set_sha256(entries),
        "source_identity": {
            "identity_mode": "GIT_HEAD_AT_PACKAGE_TIME" if _git_sha(root) else "RECOVERED_SOURCE_NO_GIT",
            "git_commit_sha": _git_sha(root),
        },
        "evidence_packaged_separately": True,
        "report_policy": "canonical_current_reports_only",
        "source_archive_policy": {
            "portable_paths_required": True,
            "unexpected_members_rejected": True,
            "unexpected_extracted_files_rejected": True,
            "special_file_types_rejected": True,
            "archive_limits": {
                "max_member_bytes": MAX_ARCHIVE_MEMBER_BYTES,
                "max_total_bytes": MAX_ARCHIVE_TOTAL_BYTES,
                "max_manifest_bytes": MAX_MANIFEST_BYTES,
                "max_compression_ratio": MAX_COMPRESSION_RATIO,
            },
        },
        "files": entries,
    }


def _zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    mode = 0o755 if executable else 0o644
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.create_system = 3
    return info


def _portable_path_problem(name: str) -> str | None:
    if not name or "\\" in name or "\x00" in name:
        return "PORTABILITY_INVALID_SEPARATOR_OR_NUL"
    if name.startswith("/"):
        return "PORTABILITY_ABSOLUTE_PATH"
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return "PORTABILITY_UNSAFE_SEGMENT"
    for part in parts:
        if part.endswith((" ", ".")):
            return "PORTABILITY_WINDOWS_TRAILING_DOT_OR_SPACE"
        stem = part.split(".", 1)[0].upper()
        if stem in WINDOWS_RESERVED_BASENAMES:
            return "PORTABILITY_WINDOWS_RESERVED_NAME"
        if any(ord(ch) < 32 for ch in part):
            return "PORTABILITY_CONTROL_CHARACTER"
        if any(ch in '<>:"|?*' for ch in part):
            return "PORTABILITY_WINDOWS_INVALID_CHARACTER"
    return None


def _normalized_path_key(name: str) -> str:
    return unicodedata.normalize("NFC", name).casefold()


def scan_zip_safety(zf: zipfile.ZipFile) -> list[str]:
    """Fail-closed metadata-only preflight before reading/decompressing members."""
    problems: list[str] = []
    infos = zf.infolist()
    exact_seen: set[str] = set()
    normalized_seen: dict[str, str] = {}
    total = 0
    for info in infos:
        name = info.filename
        if name in exact_seen:
            problems.append(f"DUPLICATE_MEMBER:{name}")
        exact_seen.add(name)
        normalized = _normalized_path_key(name)
        prior = normalized_seen.get(normalized)
        if prior is not None and prior != name:
            problems.append(f"PORTABILITY_COLLISION:{prior}:{name}")
        normalized_seen.setdefault(normalized, name)
        path_problem = _portable_path_problem(name.rstrip("/") if info.is_dir() else name)
        if path_problem:
            problems.append(f"{path_problem}:{name}")
        if info.file_size < 0 or info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            problems.append(f"MEMBER_SIZE_LIMIT:{name}:{info.file_size}")
        total += max(info.file_size, 0)
        if info.compress_size == 0:
            if info.file_size > 0:
                problems.append(f"COMPRESSION_RATIO_LIMIT:{name}:INF")
        elif info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            problems.append(f"COMPRESSION_RATIO_LIMIT:{name}:{info.file_size / info.compress_size:.2f}")
        unix_type = (info.external_attr >> 16) & 0o170000
        if info.create_system == 3 and unix_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
            problems.append(f"SPECIAL_FILE_TYPE:{name}:{oct(unix_type)}")
    if total > MAX_ARCHIVE_TOTAL_BYTES:
        problems.append(f"ARCHIVE_TOTAL_SIZE_LIMIT:{total}")
    return sorted(set(problems))


def build_release(root: Path = ROOT, archive: Path = ARCHIVE) -> tuple[Path, dict]:
    manifest = make_manifest(root)
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    root.joinpath("PACKAGE_MANIFEST.json").write_bytes(manifest_bytes)

    archive.unlink(missing_ok=True)
    prefix = root.name
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for entry in manifest["files"]:
            path = root / entry["path"]
            if path.is_symlink():
                raise ValueError(f"SOURCE_RELEASE_SYMLINK_NOT_ALLOWED:{entry['path']}")
            executable = bool(path.stat().st_mode & stat.S_IXUSR)
            info = _zip_info(f"{prefix}/{entry['path']}", executable=executable)
            zf.writestr(info, path.read_bytes())
        info = _zip_info(f"{prefix}/PACKAGE_MANIFEST.json")
        zf.writestr(info, manifest_bytes)
    return archive, manifest


def verify_archive(archive: Path = ARCHIVE) -> dict:
    forbidden: list[str] = []
    mismatches: list[str] = []
    with zipfile.ZipFile(archive, "r") as zf:
        safety_problems = scan_zip_safety(zf)
        if safety_problems:
            mismatches.extend(safety_problems)
        infos = zf.infolist()
        names = [info.filename for info in infos]
        for name in names:
            posix = Path(name)
            parts = posix.parts
            if name.startswith("/") or ".." in parts:
                forbidden.append(name)
            if any(part in EXCLUDED_DIRS for part in parts):
                forbidden.append(name)
            if posix.name in {".env", ".coverage"}:
                forbidden.append(name)
        manifest_candidates = [name for name in names if name.endswith("/PACKAGE_MANIFEST.json")]
        if len(manifest_candidates) != 1:
            return {"forbidden": sorted(set(forbidden)), "mismatches": sorted(set(mismatches + [f"MANIFEST_COUNT:{len(manifest_candidates)}"]))}
        manifest_name = manifest_candidates[0]
        manifest_info = zf.getinfo(manifest_name)
        if manifest_info.file_size > MAX_MANIFEST_BYTES:
            return {
                "forbidden": sorted(set(forbidden)),
                "mismatches": sorted(set(mismatches + [f"MANIFEST_SIZE_LIMIT:{manifest_info.file_size}"])),
            }
        prefix = manifest_name.removesuffix("/PACKAGE_MANIFEST.json")
        try:
            manifest = json.loads(zf.read(manifest_name))
        except Exception as exc:
            return {"forbidden": sorted(set(forbidden)), "mismatches": sorted(set(mismatches + [f"MANIFEST_INVALID:{type(exc).__name__}"]))}
        rows = manifest.get("files", [])
        expected = {entry["path"]: entry for entry in rows if isinstance(entry, dict) and isinstance(entry.get("path"), str)}
        if len(expected) != len(rows):
            mismatches.append("MANIFEST_DUPLICATE_OR_INVALID_PATH")
        if manifest.get("file_count") != len(rows):
            mismatches.append("MANIFEST_FILE_COUNT_MISMATCH")
        manifest_entry_invalid = False
        for rel, entry in expected.items():
            if _portable_path_problem(rel):
                mismatches.append(f"MANIFEST_PATH_NOT_PORTABLE:{rel}")
            if not isinstance(entry.get("sha256"), str) or not SHA256_RE.fullmatch(entry["sha256"]):
                mismatches.append(f"MANIFEST_HASH_INVALID:{rel}")
                manifest_entry_invalid = True
            if not isinstance(entry.get("size"), int) or isinstance(entry.get("size"), bool) or entry["size"] < 0:
                mismatches.append(f"MANIFEST_SIZE_INVALID:{rel}")
                manifest_entry_invalid = True
            if not isinstance(entry.get("executable", False), bool):
                mismatches.append(f"MANIFEST_EXECUTABLE_INVALID:{rel}")
                manifest_entry_invalid = True
        calculated_set = None
        if expected and not manifest_entry_invalid:
            try:
                calculated_set = _content_set_sha256(list(expected.values()))
            except (KeyError, TypeError, ValueError):
                mismatches.append("MANIFEST_CONTENT_SET_INPUT_INVALID")
        if manifest.get("content_set_sha256") != calculated_set:
            mismatches.append("CONTENT_SET_HASH_MISMATCH")
        expected_names = {f"{prefix}/{rel}" for rel in expected} | {manifest_name}
        for extra in sorted(set(names) - expected_names):
            mismatches.append(f"UNEXPECTED_MEMBER:{extra}")
        for missing in sorted(expected_names - set(names)):
            mismatches.append(f"MISSING_MEMBER:{missing}")
        for rel, entry in expected.items():
            member_name = f"{prefix}/{rel}"
            if member_name not in names:
                continue
            member = zf.getinfo(member_name)
            data = zf.read(member)
            if sha256_bytes(data) != entry.get("sha256") or len(data) != entry.get("size"):
                mismatches.append(rel)
                continue
            archived_mode = (member.external_attr >> 16) & 0o777
            archived_executable = bool(archived_mode & 0o111)
            if archived_executable != bool(entry.get("executable", False)):
                mismatches.append(f"{rel}:EXECUTABLE_MODE")
    return {"forbidden": sorted(set(forbidden)), "mismatches": sorted(set(mismatches))}


def main() -> None:
    archive, manifest = build_release()
    verification = verify_archive(archive)
    if verification["forbidden"] or verification["mismatches"]:
        raise RuntimeError(f"release archive verification failed: {verification}")
    digest = sha256_file(archive)
    CHECKSUM_FILE.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(json.dumps({
        "archive": str(archive),
        "sha256": digest,
        "file_count": manifest["file_count"] + 1,
        "verification": "PASS",
    }))


if __name__ == "__main__":
    main()
