from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath

MANIFEST = Path("PACKAGE_MANIFEST.json")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IGNORED_INVENTORY_DIRS = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", "node_modules"}
IGNORED_INVENTORY_NAMES = {"PACKAGE_MANIFEST.json"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _content_set_sha256(entries: list[dict]) -> str:
    normalized = [
        {
            "path": row["path"],
            "sha256": row["sha256"],
            "size": int(row["size"]),
            "executable": bool(row.get("executable", False)),
        }
        for row in sorted(entries, key=lambda item: item["path"])
    ]
    data = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _safe_rel(value: str) -> bool:
    p = PurePosixPath(value)
    return (
        bool(value)
        and "\\" not in value
        and "\x00" not in value
        and not p.is_absolute()
        and ".." not in p.parts
        and "." not in p.parts
        and "" not in p.parts
    )


def _inventory_files(root: Path) -> set[str]:
    result: set[str] = set()
    for path in root.rglob("*"):
        if not (path.is_file() or path.is_symlink()):
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_INVENTORY_DIRS for part in rel.parts):
            continue
        if rel.name in IGNORED_INVENTORY_NAMES:
            continue
        result.add(rel.as_posix())
    return result


def verify_source_package_identity(
    root: Path = Path("."),
    *,
    verify_all_files: bool = True,
    verify_inventory: bool = True,
) -> dict:
    manifest_path = root / MANIFEST
    problems: list[str] = []
    # A source release archive intentionally excludes Git metadata.  If .git
    # appears after extraction, treating it as ignorable would allow a
    # packaged source identity to be silently upgraded to attacker-controlled
    # Git provenance.  Fail closed before any package identity can be trusted.
    dot_git = root / ".git"
    if dot_git.exists() or dot_git.is_symlink():
        problems.append("PACKAGE_DOT_GIT_PRESENT")
    if not manifest_path.is_file():
        return {
            "verified": False,
            "identity_mode": "UNAVAILABLE",
            "content_set_sha256": None,
            "git_commit_sha": None,
            "problems": ["PACKAGE_MANIFEST_MISSING"],
            "entries": {},
        }
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "verified": False,
            "identity_mode": "PACKAGE_MANIFEST",
            "content_set_sha256": None,
            "git_commit_sha": None,
            "problems": [f"PACKAGE_MANIFEST_INVALID:{type(exc).__name__}"],
            "entries": {},
        }

    if manifest.get("schema_version") not in {1, "1.0", 2, "2.0"}:
        problems.append("PACKAGE_MANIFEST_SCHEMA_UNSUPPORTED")
    if manifest.get("package_role") != "SOURCE_RELEASE_ARCHIVE":
        problems.append("PACKAGE_ROLE_INVALID")
    rows = manifest.get("files")
    if not isinstance(rows, list):
        rows = []
        problems.append("PACKAGE_MANIFEST_FILES_INVALID")

    entries: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append("PACKAGE_MANIFEST_ENTRY_INVALID")
            continue
        rel = row.get("path")
        if not isinstance(rel, str) or not _safe_rel(rel):
            problems.append(f"PACKAGE_MANIFEST_PATH_UNSAFE:{rel!r}")
            continue
        if rel in entries:
            problems.append(f"PACKAGE_MANIFEST_DUPLICATE_PATH:{rel}")
            continue
        if not isinstance(row.get("sha256"), str) or not SHA256_RE.fullmatch(row["sha256"]):
            problems.append(f"PACKAGE_MANIFEST_HASH_INVALID:{rel}")
            continue
        if not isinstance(row.get("size"), int) or isinstance(row.get("size"), bool) or row["size"] < 0:
            problems.append(f"PACKAGE_MANIFEST_SIZE_INVALID:{rel}")
            continue
        if not isinstance(row.get("executable", False), bool):
            problems.append(f"PACKAGE_MANIFEST_EXECUTABLE_INVALID:{rel}")
            continue
        entries[rel] = row

    if manifest.get("file_count") != len(rows):
        problems.append("PACKAGE_MANIFEST_FILE_COUNT_MISMATCH")

    calculated_set = _content_set_sha256(list(entries.values())) if entries else None
    expected_set = manifest.get("content_set_sha256")
    if expected_set != calculated_set:
        problems.append("PACKAGE_CONTENT_SET_HASH_MISMATCH")

    if verify_all_files:
        for rel, row in entries.items():
            path = root / rel
            if path.is_symlink():
                problems.append(f"PACKAGE_FILE_SYMLINK:{rel}")
                continue
            if not path.is_file():
                problems.append(f"PACKAGE_FILE_MISSING:{rel}")
                continue
            if path.stat().st_size != row["size"]:
                problems.append(f"PACKAGE_FILE_SIZE_MISMATCH:{rel}")
                continue
            if _sha256_file(path) != row["sha256"]:
                problems.append(f"PACKAGE_FILE_HASH_MISMATCH:{rel}")
            actual_exec = bool(path.stat().st_mode & stat.S_IXUSR)
            if actual_exec != bool(row.get("executable", False)):
                problems.append(f"PACKAGE_FILE_MODE_MISMATCH:{rel}")

    if verify_inventory:
        actual_inventory = _inventory_files(root)
        expected_inventory = set(entries)
        for rel in sorted(actual_inventory - expected_inventory):
            problems.append(f"PACKAGE_UNEXPECTED_FILE:{rel}")
        for rel in sorted(expected_inventory - actual_inventory):
            if not (root / rel).is_file():
                problems.append(f"PACKAGE_FILE_MISSING:{rel}")

    source_identity = manifest.get("source_identity") if isinstance(manifest.get("source_identity"), dict) else {}
    git_commit_sha = source_identity.get("git_commit_sha")
    if git_commit_sha is not None and (not isinstance(git_commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", git_commit_sha)):
        problems.append("PACKAGE_GIT_SHA_INVALID")
    return {
        "verified": not problems,
        "identity_mode": "PACKAGE_MANIFEST",
        "content_set_sha256": calculated_set,
        "git_commit_sha": git_commit_sha,
        "problems": sorted(set(problems)),
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an extracted source package against PACKAGE_MANIFEST.json")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Extracted source package root containing PACKAGE_MANIFEST.json (default: current directory).",
    )
    args = parser.parse_args()
    result = verify_source_package_identity(args.root.resolve())
    print(json.dumps({k: v for k, v in result.items() if k != "entries"}, indent=2, sort_keys=True))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
