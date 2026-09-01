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

from scripts.bounded_subprocess import run_captured

REPORTS = ROOT / "reports" / "local_acceptance"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def discover() -> list[str]:
    files = sorted(
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in (ROOT / "tests").rglob("test_*.py")
        if "__pycache__" not in p.parts
    )
    return files


def select_shard(files: list[str], index: int, count: int) -> list[str]:
    if count < 1 or index < 0 or index >= count:
        raise ValueError("invalid shard index/count")
    return [path for i, path in enumerate(files) if i % count == index]


def run_shard(index: int, count: int, timeout: int) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    all_files = discover()
    selected = select_shard(all_files, index, count)
    log = REPORTS / f"shard_{index:02d}_of_{count:02d}.log"
    command = ["python", "-m", "pytest", "-q", *selected]
    observed = datetime.now(timezone.utc).isoformat()
    try:
        proc = run_captured(command, cwd=ROOT, timeout=timeout)
        output = proc.stdout or ""
        exit_code = proc.returncode
        status = "PASS" if proc.returncode == 0 else "FAIL"
        blocker = None if proc.returncode == 0 else f"EXIT_CODE:{proc.returncode}"
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        output += "\nTIMEOUT\n"
        exit_code = None
        status = "BLOCKED"
        blocker = "TIMEOUT"
    log.write_text(output, encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "classification": "LOCAL_TEST_SHARD_EVIDENCE",
        "observed_at": observed,
        "git_commit_sha": _git_sha(),
        "shard_index": index,
        "shard_count": count,
        "discovered_file_count": len(all_files),
        "selected_files": selected,
        "status": status,
        "exit_code": exit_code,
        "blocker": blocker,
        "log": str(log.relative_to(ROOT)),
        "log_sha256": _sha(log),
    }
    manifest = REPORTS / f"shard_{index:02d}_of_{count:02d}.json"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-index", type=int, required=True)
    ap.add_argument("--shard-count", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    payload = run_shard(args.shard_index, args.shard_count, max(1, args.timeout))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
