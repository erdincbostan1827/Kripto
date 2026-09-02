from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bounded_subprocess import run_captured_split

DEFAULT = ROOT / "reports" / "local_coverage" / "full_coverage_manifest.json"
GIT_PROBE_TIMEOUT_SECONDS = 10


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    try:
        proc = run_captured_split(["git", "rev-parse", "HEAD"], cwd=root, timeout=GIT_PROBE_TIMEOUT_SECONDS)
    except (subprocess.TimeoutExpired, OSError):
        return "UNAVAILABLE"
    value = (proc.stdout or "").strip()
    return value if proc.returncode == 0 and value else "UNAVAILABLE"


def verify(path: Path = DEFAULT, *, root: Path = ROOT) -> dict:
    if not path.is_file():
        return {"verified": False, "status": "NOT_TESTED", "problems": ["MANIFEST_MISSING"], "coverage_percent": None, "manifest_sha256": None}
    problems: list[str] = []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"verified": False, "status": "BLOCKED", "problems": ["MANIFEST_INVALID_JSON"], "coverage_percent": None, "manifest_sha256": _sha(path)}
    current = _git_sha(root)
    if current == "UNAVAILABLE":
        problems.append("GIT_IDENTITY_UNAVAILABLE")
    if doc.get("classification") != "LOCAL_FULL_COVERAGE_EVIDENCE": problems.append("CLASSIFICATION_INVALID")
    if doc.get("git_commit_sha") != current: problems.append("GIT_COMMIT_MISMATCH")
    if doc.get("status") != "PASS" or doc.get("problems") not in ([], None): problems.append("MERGED_STATUS_NOT_PASS")
    percent = doc.get("coverage_percent")
    if not isinstance(percent, (int, float)) or isinstance(percent, bool) or not 0 <= float(percent) <= 100: problems.append("COVERAGE_PERCENT_INVALID")
    cov_ref = doc.get("coverage_json")
    cov_path = root / cov_ref if isinstance(cov_ref, str) else None
    if not cov_path or not cov_path.is_file() or _sha(cov_path) != doc.get("coverage_json_sha256"):
        problems.append("COVERAGE_JSON_HASH_INVALID")
    shards = doc.get("shards") if isinstance(doc.get("shards"), list) else []
    if len(shards) != doc.get("shard_count"): problems.append("SHARD_COUNT_MISMATCH")
    for item in shards:
        ref = item.get("manifest") if isinstance(item, dict) else None
        exp = item.get("manifest_sha256") if isinstance(item, dict) else None
        shard_path = root / ref if isinstance(ref, str) else None
        if not shard_path or not shard_path.is_file() or _sha(shard_path) != exp:
            problems.append(f"SHARD_MANIFEST_HASH_INVALID:{ref}")
            continue
        try: shard = json.loads(shard_path.read_text(encoding="utf-8"))
        except Exception:
            problems.append(f"SHARD_MANIFEST_INVALID:{ref}"); continue
        if shard.get("git_commit_sha") != current: problems.append(f"SHARD_GIT_MISMATCH:{ref}")
        data_ref = shard.get("coverage_data")
        data_path = root / data_ref if isinstance(data_ref, str) else None
        if not data_path or not data_path.is_file() or _sha(data_path) != shard.get("coverage_data_sha256"):
            problems.append(f"SHARD_COVERAGE_DATA_INVALID:{ref}")
    return {
        "verified": not problems,
        "status": "PASS" if not problems else "BLOCKED",
        "problems": sorted(set(problems)),
        "coverage_percent": float(percent) if isinstance(percent, (int, float)) and not isinstance(percent, bool) else None,
        "manifest_sha256": _sha(path),
        "git_commit_sha": current,
    }


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
