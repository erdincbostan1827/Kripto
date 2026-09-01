from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from secrets import token_hex
import json
import os
from scripts.bounded_subprocess import run_captured
from typing import Any

from backend.app.release.acceptance_contract import acceptance_contract_sha256
from backend.app.release.path_integrity import PathIntegrityError, resolve_without_symlink_components, strict_regular_file

CURRENT_CHALLENGE_SCHEMA = "2.3"
GIT_STATUS_UNAVAILABLE_MARKER = "__GIT_STATUS_UNAVAILABLE__"


def _git_sha(root: Path) -> str:
    try:
        proc = run_captured(["git", "rev-parse", "HEAD"], cwd=root, timeout=10)
        return proc.stdout.strip() if proc.returncode == 0 else "UNAVAILABLE"
    except Exception:
        return "UNAVAILABLE"


def _git_tree_sha(root: Path) -> str:
    try:
        proc = run_captured(["git", "rev-parse", "HEAD^{tree}"], cwd=root, timeout=10)
        return proc.stdout.strip() if proc.returncode == 0 else "UNAVAILABLE"
    except Exception:
        return "UNAVAILABLE"


def _tracked_source_dirty_paths(root: Path, *, extra_ignored: set[str] | None = None) -> list[str]:
    """Return release-relevant worktree changes while ignoring runtime evidence outputs.

    The acceptance process itself writes under reports/ and frontend/dist/, so those
    locations are excluded. Untracked source-like files elsewhere remain blockers;
    this prevents a clean HEAD SHA from masking executable worktree substitutions.
    """
    try:
        proc = run_captured(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root, timeout=10,
        )
        if proc.returncode != 0:
            return [GIT_STATUS_UNAVAILABLE_MARKER]
    except Exception:
        return [GIT_STATUS_UNAVAILABLE_MARKER]
    dirty: list[str] = []
    for raw in (proc.stdout or "").splitlines():
        if len(raw) < 4:
            continue
        status = raw[:2]
        path = raw[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        normalized = path.replace("\\", "/")
        if extra_ignored and normalized in extra_ignored:
            continue
        if normalized.startswith("reports/") or normalized.startswith("frontend/dist/"):
            continue
        if normalized.startswith(".pytest_cache/") or "/__pycache__/" in f"/{normalized}" or normalized.startswith(".coverage"):
            continue
        if status == "??":
            # Runtime acceptance creates logs/JSON receipts outside reports in some
            # deployments. Only untracked files that can alter executable/build
            # behavior are treated as source substitutions.
            name = Path(normalized).name.lower()
            suffix = Path(normalized).suffix.lower()
            source_suffixes = {".py", ".pyi", ".sh", ".bash", ".ps1", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".toml", ".yaml", ".yml", ".ini", ".cfg"}
            source_names = {"dockerfile", "makefile", "package.json", "pyproject.toml", "alembic.ini", ".env", ".env.local"}
            if suffix not in source_suffixes and name not in source_names:
                continue
        dirty.append(normalized)
    return sorted(set(dirty))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def create_challenge(root: Path, output: Path) -> dict[str, Any]:
    output = resolve_without_symlink_components(root, output)
    git_commit_sha = _git_sha(root)
    git_tree_sha = _git_tree_sha(root)
    git_identity_available = git_commit_sha != "UNAVAILABLE" and git_tree_sha != "UNAVAILABLE"
    payload = {
        "schema_version": CURRENT_CHALLENGE_SCHEMA,
        "classification": "EXTERNAL_ACCEPTANCE_RELEASE_CHALLENGE",
        "challenge_id": token_hex(16),
        "git_commit_sha": git_commit_sha,
        "git_tree_sha": git_tree_sha,
        "git_identity_available_at_creation": git_identity_available,
        "source_worktree_clean_at_creation": bool(git_identity_available and not _tracked_source_dirty_paths(root)),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "release_campaign_bound": True,
        "acceptance_contract_sha256": acceptance_contract_sha256(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**payload, "sha256": _sha(output)}


def verify_challenge(path: Path, *, root: Path, max_age_hours: int = 24, require_trust: bool | None = None) -> dict[str, Any]:
    try:
        path = strict_regular_file(root, path)
    except PathIntegrityError as exc:
        if "not a regular file" in str(exc):
            return {"verified": False, "problems": ["CHALLENGE_MISSING"]}
        return {"verified": False, "problems": ["CHALLENGE_PATH_INTEGRITY_INVALID"]}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"CHALLENGE_INVALID_JSON:{type(exc).__name__}"]}
    problems: list[str] = []
    try:
        challenge_rel = str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
        challenge_ignored = {challenge_rel}
    except ValueError:
        challenge_ignored = set()
    if payload.get("classification") != "EXTERNAL_ACCEPTANCE_RELEASE_CHALLENGE":
        problems.append("CHALLENGE_INVALID_CLASSIFICATION")
    schema_version = str(payload.get("schema_version") or "")
    if schema_version == "1.0":
        if payload.get("single_release_use") is not True:
            problems.append("CHALLENGE_V1_RELEASE_BINDING_INVALID")
    elif schema_version in {"2.0", "2.1", "2.2", "2.3"}:
        if payload.get("release_campaign_bound") is not True:
            problems.append("CHALLENGE_RELEASE_CAMPAIGN_BINDING_INVALID")
        if "single_release_use" in payload:
            problems.append("CHALLENGE_DEPRECATED_SINGLE_USE_FIELD_PRESENT")
        if schema_version in {"2.1", "2.2", "2.3"}:
            expected_tree = _git_tree_sha(root)
            if expected_tree != "UNAVAILABLE" and payload.get("git_tree_sha") != expected_tree:
                problems.append("CHALLENGE_GIT_TREE_MISMATCH")
            if payload.get("source_worktree_clean_at_creation") is not True:
                problems.append("CHALLENGE_SOURCE_DIRTY_AT_CREATION")
            dirty_now = _tracked_source_dirty_paths(root, extra_ignored=challenge_ignored)
            if GIT_STATUS_UNAVAILABLE_MARKER in dirty_now:
                problems.append("CHALLENGE_SOURCE_STATUS_UNAVAILABLE")
            if dirty_now:
                problems.append("CHALLENGE_SOURCE_WORKTREE_DIRTY")
        if schema_version in {"2.2", "2.3"}:
            current_git = _git_sha(root)
            current_tree = _git_tree_sha(root)
            if payload.get("git_identity_available_at_creation") is not True:
                problems.append("CHALLENGE_GIT_IDENTITY_UNAVAILABLE_AT_CREATION")
            if current_git == "UNAVAILABLE" or current_tree == "UNAVAILABLE":
                problems.append("CHALLENGE_GIT_IDENTITY_UNAVAILABLE")
            if payload.get("git_commit_sha") == "UNAVAILABLE" or payload.get("git_tree_sha") == "UNAVAILABLE":
                problems.append("CHALLENGE_NOT_GIT_BOUND")
        if schema_version == "2.3":
            current_contract = acceptance_contract_sha256()
            if payload.get("acceptance_contract_sha256") != current_contract:
                problems.append("CHALLENGE_ACCEPTANCE_CONTRACT_MISMATCH")
    else:
        problems.append("CHALLENGE_SCHEMA_UNSUPPORTED")
    if not isinstance(payload.get("challenge_id"), str) or len(payload["challenge_id"]) < 16:
        problems.append("CHALLENGE_ID_INVALID")
    expected_git = _git_sha(root)
    if expected_git != "UNAVAILABLE" and payload.get("git_commit_sha") != expected_git:
        problems.append("CHALLENGE_GIT_MISMATCH")
    trust_required = (os.getenv("ACCEPTANCE_REQUIRE_CHALLENGE_TRUST", "").strip().lower() in {"1", "true", "yes"}) if require_trust is None else bool(require_trust)
    if trust_required and schema_version != CURRENT_CHALLENGE_SCHEMA:
        problems.append("CHALLENGE_CURRENT_SCHEMA_REQUIRED")
    trust_command = os.getenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "").strip()
    trust_status = "NOT_CONFIGURED"
    if trust_command:
        env = dict(os.environ)
        env["ACCEPTANCE_CHALLENGE_PATH"] = str(path.resolve())
        try:
            proc = run_captured(["bash", "-lc", trust_command], cwd=root, env=env, timeout=60)
            if proc.returncode == 0:
                trust_status = "VERIFIED_BY_EXTERNAL_COMMAND"
            else:
                trust_status = "EXTERNAL_COMMAND_REJECTED"
                problems.append("CHALLENGE_TRUST_VERIFICATION_FAILED")
        except Exception as exc:
            trust_status = f"EXTERNAL_COMMAND_ERROR:{type(exc).__name__}"
            problems.append("CHALLENGE_TRUST_VERIFICATION_ERROR")
    elif trust_required:
        problems.append("CHALLENGE_TRUST_VERIFIER_MISSING")

    try:
        created = datetime.fromisoformat(str(payload.get("created_at")).replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1:
            problems.append("CHALLENGE_FROM_FUTURE")
        elif age > max_age_hours:
            problems.append("CHALLENGE_STALE")
    except Exception:
        problems.append("CHALLENGE_TIMESTAMP_INVALID")
    return {
        "verified": not problems,
        "problems": problems,
        "challenge_id": payload.get("challenge_id"),
        "git_commit_sha": payload.get("git_commit_sha"),
        "git_tree_sha": payload.get("git_tree_sha"),
        "git_identity_available_at_creation": payload.get("git_identity_available_at_creation"),
        "source_worktree_clean_at_creation": payload.get("source_worktree_clean_at_creation"),
        "source_worktree_dirty_paths": _tracked_source_dirty_paths(root, extra_ignored=challenge_ignored),
        "schema_version": payload.get("schema_version"),
        "acceptance_contract_sha256": payload.get("acceptance_contract_sha256"),
        "release_campaign_bound": bool(
            payload.get("release_campaign_bound") is True
            or (payload.get("schema_version") == "1.0" and payload.get("single_release_use") is True)
        ),
        "sha256": _sha(path),
        "trust_required": trust_required,
        "trust_status": trust_status,
        "trust_verified": trust_status == "VERIFIED_BY_EXTERNAL_COMMAND",
    }
