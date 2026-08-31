from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "lock-promotion" / "LOCK_PROMOTION_MANIFEST.json"
LOCKS = ("uv.lock", "frontend/package-lock.json")
INPUTS = ("pyproject.toml", "frontend/package.json")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_version(command: list[str], *, root: Path) -> str:
    out = subprocess.check_output(command, cwd=root, text=True, stderr=subprocess.STDOUT).strip()
    return out.splitlines()[0] if out else ""


def git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def create(root: Path = ROOT, output: Path | None = None) -> dict:
    missing = [rel for rel in (*INPUTS, *LOCKS) if not (root / rel).is_file()]
    if missing:
        raise FileNotFoundError(",".join(missing))
    out = output or (root / "reports" / "lock-promotion" / "LOCK_PROMOTION_MANIFEST.json")
    payload = {
        "schema_version": "1.1",
        "classification": "LOCK_PROMOTION_REVIEW_EVIDENCE_NOT_SOURCE_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_git_sha": git_sha(root),
        "inputs": {
            rel: {
                "sha256": sha256_file(root / rel),
                "size": (root / rel).stat().st_size,
            }
            for rel in INPUTS
        },
        "locks": {
            rel: {
                "sha256": sha256_file(root / rel),
                "size": (root / rel).stat().st_size,
            }
            for rel in LOCKS
        },
        "toolchain": {
            "python": cmd_version(["python", "--version"], root=root),
            "uv": cmd_version(["uv", "--version"], root=root),
            "node": cmd_version(["node", "--version"], root=root),
            "npm": cmd_version(["npm", "--version"], root=root),
        },
        "truth_policy": (
            "Generated locks are review evidence only. They become source-compliant only after "
            "explicit review and commit to a new immutable candidate."
        ),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify(path: Path = OUT, *, root: Path = ROOT, expected_source_sha: str | None = None) -> dict:
    problems: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"LOCK_PROMOTION_MANIFEST_INVALID:{type(exc).__name__}"]}

    if payload.get("schema_version") != "1.1":
        problems.append("LOCK_PROMOTION_SCHEMA_UNSUPPORTED")
    if payload.get("classification") != "LOCK_PROMOTION_REVIEW_EVIDENCE_NOT_SOURCE_ACCEPTANCE":
        problems.append("LOCK_PROMOTION_CLASSIFICATION_INVALID")
    actual_sha = git_sha(root)
    declared_sha = payload.get("source_git_sha")
    if declared_sha != actual_sha:
        problems.append("LOCK_PROMOTION_SOURCE_GIT_MISMATCH")
    if expected_source_sha and declared_sha != expected_source_sha:
        problems.append("LOCK_PROMOTION_EXPECTED_SOURCE_GIT_MISMATCH")

    inputs = payload.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != set(INPUTS):
        problems.append("LOCK_PROMOTION_INPUT_SET_INVALID")
        inputs = {}
    for rel in INPUTS:
        row = inputs.get(rel)
        path_obj = root / rel
        if not isinstance(row, dict):
            problems.append(f"LOCK_PROMOTION_INPUT_ROW_MISSING:{rel}")
            continue
        if not path_obj.is_file():
            problems.append(f"LOCK_PROMOTION_INPUT_MISSING:{rel}")
            continue
        if row.get("sha256") != sha256_file(path_obj):
            problems.append(f"LOCK_PROMOTION_INPUT_HASH_MISMATCH:{rel}")
        if row.get("size") != path_obj.stat().st_size:
            problems.append(f"LOCK_PROMOTION_INPUT_SIZE_MISMATCH:{rel}")

    locks = payload.get("locks")
    if not isinstance(locks, dict) or set(locks) != set(LOCKS):
        problems.append("LOCK_PROMOTION_LOCK_SET_INVALID")
        locks = {}
    for rel in LOCKS:
        row = locks.get(rel)
        path_obj = root / rel
        if not isinstance(row, dict):
            problems.append(f"LOCK_PROMOTION_LOCK_ROW_MISSING:{rel}")
            continue
        if not path_obj.is_file():
            problems.append(f"LOCK_PROMOTION_LOCK_MISSING:{rel}")
            continue
        if row.get("sha256") != sha256_file(path_obj):
            problems.append(f"LOCK_PROMOTION_LOCK_HASH_MISMATCH:{rel}")
        if row.get("size") != path_obj.stat().st_size:
            problems.append(f"LOCK_PROMOTION_LOCK_SIZE_MISMATCH:{rel}")

    toolchain = payload.get("toolchain")
    if not isinstance(toolchain, dict) or set(toolchain) != {"python", "uv", "node", "npm"}:
        problems.append("LOCK_PROMOTION_TOOLCHAIN_INVALID")
    elif any(not isinstance(v, str) or not v.strip() for v in toolchain.values()):
        problems.append("LOCK_PROMOTION_TOOLCHAIN_VALUE_INVALID")

    return {
        "verified": not problems,
        "problems": problems,
        "source_git_sha": declared_sha,
        "manifest_sha256": sha256_file(path) if path.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("create", "verify"))
    parser.add_argument("--expected-source-sha")
    args = parser.parse_args()
    try:
        result = create() if args.mode == "create" else verify(expected_source_sha=args.expected_source_sha)
    except Exception as exc:
        print(json.dumps({"verified": False, "problems": [f"{type(exc).__name__}:{exc}"]}, sort_keys=True))
        return 2
    if args.mode == "create":
        print(json.dumps({"created": True, "source_git_sha": result["source_git_sha"]}, sort_keys=True))
        return 0
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
