from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "lock-promotion" / "LOCK_INPUT_SNAPSHOT.json"
INPUTS = ("pyproject.toml", "frontend/package.json")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def snapshot(root: Path = ROOT, output: Path = OUT) -> dict:
    missing = [rel for rel in INPUTS if not (root / rel).is_file()]
    if missing:
        raise FileNotFoundError(",".join(missing))
    payload = {
        "schema_version": "1.0",
        "classification": "LOCK_INPUT_SNAPSHOT_REVIEW_EVIDENCE_NOT_SOURCE_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_git_sha": git_sha(root),
        "inputs": {
            rel: {"sha256": sha256_file(root / rel), "size": (root / rel).stat().st_size}
            for rel in INPUTS
        },
        "truth_policy": (
            "This snapshot proves only which dependency manifests were presented to lock resolution. "
            "It does not prove dependency integrity, vulnerability status, license acceptance, or production readiness."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify(path: Path = OUT, *, root: Path = ROOT, expected_source_sha: str | None = None) -> dict:
    problems: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"LOCK_INPUT_SNAPSHOT_INVALID:{type(exc).__name__}"]}
    if payload.get("schema_version") != "1.0":
        problems.append("LOCK_INPUT_SNAPSHOT_SCHEMA_UNSUPPORTED")
    if payload.get("classification") != "LOCK_INPUT_SNAPSHOT_REVIEW_EVIDENCE_NOT_SOURCE_ACCEPTANCE":
        problems.append("LOCK_INPUT_SNAPSHOT_CLASSIFICATION_INVALID")
    actual_sha = git_sha(root)
    declared_sha = payload.get("source_git_sha")
    if declared_sha != actual_sha:
        problems.append("LOCK_INPUT_SNAPSHOT_SOURCE_GIT_MISMATCH")
    if expected_source_sha and declared_sha != expected_source_sha:
        problems.append("LOCK_INPUT_SNAPSHOT_EXPECTED_SOURCE_GIT_MISMATCH")
    rows = payload.get("inputs")
    if not isinstance(rows, dict) or set(rows) != set(INPUTS):
        problems.append("LOCK_INPUT_SNAPSHOT_INPUT_SET_INVALID")
        rows = {}
    for rel in INPUTS:
        row = rows.get(rel)
        p = root / rel
        if not isinstance(row, dict):
            problems.append(f"LOCK_INPUT_SNAPSHOT_ROW_MISSING:{rel}")
            continue
        if not p.is_file():
            problems.append(f"LOCK_INPUT_MISSING:{rel}")
            continue
        if row.get("sha256") != sha256_file(p):
            problems.append(f"LOCK_INPUT_HASH_MISMATCH:{rel}")
        if row.get("size") != p.stat().st_size:
            problems.append(f"LOCK_INPUT_SIZE_MISMATCH:{rel}")
    return {
        "verified": not problems,
        "problems": problems,
        "source_git_sha": declared_sha,
        "snapshot_sha256": sha256_file(path) if path.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("snapshot", "verify"))
    parser.add_argument("--expected-source-sha")
    args = parser.parse_args()
    try:
        result = snapshot() if args.mode == "snapshot" else verify(expected_source_sha=args.expected_source_sha)
    except Exception as exc:
        print(json.dumps({"verified": False, "problems": [f"{type(exc).__name__}:{exc}"]}, sort_keys=True))
        return 2
    if args.mode == "snapshot":
        print(json.dumps({"created": True, "source_git_sha": result["source_git_sha"]}, sort_keys=True))
        return 0
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
