from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bounded_subprocess import run_captured_split

REPORTS = ROOT / "reports" / "local_acceptance"
GIT_PROBE_TIMEOUT_SECONDS = 10


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        proc = run_captured_split(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=GIT_PROBE_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        return "UNAVAILABLE"
    value = (proc.stdout or "").strip()
    return value if proc.returncode == 0 and value else "UNAVAILABLE"


def discover() -> list[str]:
    return sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "tests").rglob("test_*.py") if "__pycache__" not in p.parts)


def merge(shard_count: int) -> dict:
    expected_files = discover()
    expected_git = _git_sha()
    problems: list[str] = []
    if expected_git == "UNAVAILABLE":
        problems.append("GIT_IDENTITY_UNAVAILABLE")
    covered: list[str] = []
    shards = []
    for index in range(shard_count):
        path = REPORTS / f"shard_{index:02d}_of_{shard_count:02d}.json"
        if not path.is_file():
            problems.append(f"SHARD_MISSING:{index}")
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            problems.append(f"SHARD_INVALID_JSON:{index}")
            continue
        log = ROOT / str(row.get("log"))
        if row.get("git_commit_sha") != expected_git:
            problems.append(f"SHARD_GIT_MISMATCH:{index}")
        if row.get("status") != "PASS" or row.get("exit_code") != 0:
            problems.append(f"SHARD_NOT_PASS:{index}")
        if not log.is_file() or _sha(log) != row.get("log_sha256"):
            problems.append(f"SHARD_LOG_HASH_INVALID:{index}")
        selected = row.get("selected_files") if isinstance(row.get("selected_files"), list) else []
        covered.extend(str(x) for x in selected)
        shards.append({"index": index, "manifest": str(path.relative_to(ROOT)), "manifest_sha256": _sha(path), "status": row.get("status")})
    if sorted(covered) != expected_files:
        problems.append("TEST_FILE_COVERAGE_MISMATCH")
    if len(covered) != len(set(covered)):
        problems.append("DUPLICATE_TEST_FILE_COVERAGE")
    payload = {
        "schema_version": "1.0",
        "classification": "LOCAL_FULL_REGRESSION_EVIDENCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": expected_git,
        "shard_count": shard_count,
        "test_file_count": len(expected_files),
        "covered_test_file_count": len(covered),
        "status": "PASS" if not problems else "BLOCKED",
        "problems": problems,
        "shards": shards,
    }
    out = REPORTS / "full_regression_manifest.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-count", type=int, default=8)
    args = ap.parse_args()
    payload = merge(args.shard_count)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
