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

from scripts.local_acceptance_runner import discover, select_shard
from scripts.bounded_subprocess import run_captured

REPORTS = ROOT / "reports" / "local_coverage"


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def _per_file_fallback(selected: list[str], data: Path, timeout: int) -> tuple[int | None, str, str | None]:
    """Re-run a timed-out shard file-by-file, requiring every pytest process and coverage write to succeed."""
    data.unlink(missing_ok=True)
    for stale in REPORTS.glob(data.name + ".*"):
        stale.unlink(missing_ok=True)
    chunks = ["SHARD_TIMEOUT_FALLBACK=PER_FILE\n"]
    per_file_timeout = max(30, min(timeout, 180))
    for test_file in selected:
        command = [
            "python", "-m", "coverage", "run", f"--data-file={data}", "--append",
            "-m", "pytest", "-q", test_file,
        ]
        chunks.append(f"\n=== {test_file} ===\n")
        try:
            proc = run_captured(command, cwd=ROOT, timeout=per_file_timeout)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode(errors="replace")
            chunks.append(output + "\nFILE_TIMEOUT\n")
            return None, "".join(chunks), f"FILE_TIMEOUT:{test_file}"
        chunks.append(proc.stdout or "")
        if proc.returncode != 0:
            return proc.returncode, "".join(chunks), f"FILE_EXIT_CODE:{test_file}:{proc.returncode}"
    if not data.is_file() or data.stat().st_size <= 0:
        return 0, "".join(chunks), "COVERAGE_DATA_MISSING_AFTER_FALLBACK"
    return 0, "".join(chunks), None


def run_shard(index: int, count: int, timeout: int) -> dict:
    REPORTS.mkdir(parents=True, exist_ok=True)
    all_files = discover()
    selected = select_shard(all_files, index, count)
    log = REPORTS / f"coverage_shard_{index:02d}_of_{count:02d}.log"
    data = REPORTS / f".coverage.{index:02d}_of_{count:02d}"
    data.unlink(missing_ok=True)
    for stale in REPORTS.glob(data.name + ".*"):
        stale.unlink(missing_ok=True)
    command = [
        "python", "-m", "coverage", "run", "--parallel-mode", f"--data-file={data}",
        "-m", "pytest", "-q", *selected,
    ]
    observed = datetime.now(timezone.utc).isoformat()
    try:
        proc = run_captured(command, cwd=ROOT, timeout=timeout)
        output = proc.stdout or ""
        exit_code = proc.returncode
        data_candidates = sorted(REPORTS.glob(data.name + ".*"))
        if data_candidates and not data.exists():
            if len(data_candidates) == 1:
                data_candidates[0].replace(data)
            else:
                env = dict(__import__('os').environ)
                env['COVERAGE_FILE'] = str(data)
                try:
                    combined = run_captured(
                        ["python", "-m", "coverage", "combine", *map(str, data_candidates)],
                        cwd=ROOT,
                        env=env,
                        timeout=max(30, min(timeout, 180)),
                    )
                except subprocess.TimeoutExpired as exc:
                    timed_out = exc.stdout or ""
                    if isinstance(timed_out, bytes):
                        timed_out = timed_out.decode(errors="replace")
                    output += "\nCOVERAGE_COMBINE_TIMEOUT\n" + timed_out
                else:
                    if combined.returncode != 0:
                        output += "\nCOVERAGE_COMBINE_FAILED\n" + (combined.stdout or "")
        status = "PASS" if exit_code == 0 and data.is_file() and data.stat().st_size > 0 else "FAIL"
        blocker = None if status == "PASS" else (f"EXIT_CODE:{exit_code}" if exit_code else "COVERAGE_DATA_MISSING")
    except subprocess.TimeoutExpired as exc:
        timed_out_output = exc.stdout or ""
        if isinstance(timed_out_output, bytes):
            timed_out_output = timed_out_output.decode(errors="replace")
        exit_code, fallback_output, fallback_blocker = _per_file_fallback(selected, data, timeout)
        output = timed_out_output + "\nSHARD_TIMEOUT\n" + fallback_output
        blocker = fallback_blocker
        status = "PASS" if exit_code == 0 and blocker is None and data.is_file() and data.stat().st_size > 0 else "BLOCKED"
    log.write_text(output, encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "classification": "LOCAL_COVERAGE_SHARD_EVIDENCE",
        "observed_at": observed,
        "git_commit_sha": _git_sha(),
        "shard_index": index,
        "shard_count": count,
        "discovered_file_count": len(all_files),
        "selected_files": selected,
        "status": status,
        "exit_code": exit_code,
        "blocker": blocker,
        "execution_mode": "PER_FILE_TIMEOUT_FALLBACK" if "SHARD_TIMEOUT_FALLBACK=PER_FILE" in output else "SHARD",
        "log": str(log.relative_to(ROOT)),
        "log_sha256": _sha(log),
        "coverage_data": str(data.relative_to(ROOT)) if data.is_file() else None,
        "coverage_data_sha256": _sha(data) if data.is_file() else None,
    }
    manifest = REPORTS / f"coverage_shard_{index:02d}_of_{count:02d}.json"
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard-index", type=int, required=True)
    ap.add_argument("--shard-count", type=int, default=24)
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()
    payload = run_shard(args.shard_index, args.shard_count, max(1, args.timeout))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
