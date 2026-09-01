from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

try:
    from scripts.bounded_subprocess import run_captured_bytes
except ModuleNotFoundError:
    from bounded_subprocess import run_captured_bytes

try:
    from scripts.verify_source_package_identity import verify_source_package_identity
except ModuleNotFoundError:
    from verify_source_package_identity import verify_source_package_identity

ROOT = Path(__file__).resolve().parents[1]
LOCKS = ("uv.lock", "frontend/package-lock.json")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return run_captured_bytes(["git", *args], cwd=root, timeout=10)


def _repository_identity(root: Path) -> tuple[bool, str | None, str | None]:
    """Return repository availability, HEAD SHA and a fail-closed diagnostic."""
    try:
        inside = _git(root, "rev-parse", "--is-inside-work-tree")
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as exc:
        return False, None, f"GIT_UNAVAILABLE:{type(exc).__name__}"
    if inside.returncode != 0 or inside.stdout.strip() != b"true":
        return False, None, "GIT_REPOSITORY_UNAVAILABLE"
    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return False, None, "GIT_HEAD_UNAVAILABLE"
    sha = head.stdout.decode("ascii", errors="ignore").strip()
    if len(sha) != 40:
        return False, None, "GIT_HEAD_INVALID"
    return True, sha, None


def verify_source_locks(root: Path = ROOT) -> dict:
    rows: list[dict] = []
    problems: list[str] = []
    repository_verified, git_head, repository_problem = _repository_identity(root)
    package_identity = None
    identity_mode = "GIT_HEAD" if repository_verified else "UNAVAILABLE"
    if not repository_verified:
        package_identity = verify_source_package_identity(root, verify_all_files=True)
        if package_identity.get("verified"):
            identity_mode = "PACKAGE_MANIFEST"
        elif repository_problem:
            problems.append(repository_problem)
            problems.extend(f"PACKAGE_IDENTITY:{x}" for x in package_identity.get("problems", []))

    identity_verified = repository_verified or bool(package_identity and package_identity.get("verified"))
    manifest_entries = package_identity.get("entries", {}) if package_identity else {}

    for rel in LOCKS:
        path = root / rel
        exists = path.is_file()
        tracked = False
        matches_head = False
        package_manifest_bound = False
        working_sha = _sha256(path.read_bytes()) if exists else None
        head_sha = None

        if exists and repository_verified:
            tracked_check = _git(root, "ls-files", "--error-unmatch", "--", rel)
            tracked = tracked_check.returncode == 0
        if tracked:
            head = _git(root, "show", f"HEAD:{rel}")
            if head.returncode == 0:
                head_bytes = head.stdout
                head_sha = _sha256(head_bytes)
                matches_head = path.read_bytes() == head_bytes
        elif exists and identity_mode == "PACKAGE_MANIFEST":
            entry = manifest_entries.get(rel)
            if isinstance(entry, dict):
                package_manifest_bound = working_sha == entry.get("sha256") and path.stat().st_size == entry.get("size")

        compliant = bool((repository_verified and exists and tracked and matches_head) or (identity_mode == "PACKAGE_MANIFEST" and exists and package_manifest_bound))
        if not compliant:
            if not exists:
                reason = "MISSING"
            elif not identity_verified:
                reason = "SOURCE_IDENTITY_UNVERIFIED"
            elif identity_mode == "GIT_HEAD" and not tracked:
                reason = "NOT_TRACKED_IN_HEAD"
            elif identity_mode == "GIT_HEAD":
                reason = "DIFFERS_FROM_HEAD"
            else:
                reason = "NOT_BOUND_TO_PACKAGE_MANIFEST"
            problems.append(f"{rel}:{reason}")

        rows.append({
            "path": rel,
            "exists": exists,
            "tracked": tracked,
            "matches_head": matches_head,
            "package_manifest_bound": package_manifest_bound,
            "working_tree_sha256": working_sha,
            "head_sha256": head_sha,
            "source_compliant": compliant,
        })

    return {
        "verified": not problems,
        "identity_verified": identity_verified,
        "identity_mode": identity_mode,
        "repository_verified": repository_verified,
        "git_head": git_head or (package_identity or {}).get("git_commit_sha"),
        "package_content_set_sha256": (package_identity or {}).get("content_set_sha256"),
        "problems": sorted(set(problems)),
        "locks": rows,
    }


def main() -> int:
    result = verify_source_locks()
    print(f"SOURCE_LOCKS={'PASS' if result['verified'] else 'FAIL'}")
    print(f"identity_verified={result['identity_verified']} identity_mode={result['identity_mode']} repository_verified={result['repository_verified']} git_head={result['git_head']}")
    for row in result["locks"]:
        print(
            f"{row['path']} tracked={row['tracked']} matches_head={row['matches_head']} "
            f"sha256={row['working_tree_sha256']}"
        )
    for problem in result["problems"]:
        print(f"- {problem}")
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
