from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "reports/local_acceptance/full_regression_manifest.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def verify_local_acceptance(path: Path = DEFAULT_MANIFEST, root: Path = ROOT) -> dict:
    problems: list[str] = []
    if not path.is_file():
        return {"verified": False, "status": "NOT_TESTED", "problems": ["MANIFEST_MISSING"], "manifest_sha256": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"verified": False, "status": "BLOCKED", "problems": ["MANIFEST_INVALID_JSON"], "manifest_sha256": _sha(path)}
    current_git = _git_sha(root)
    if data.get("classification") != "LOCAL_FULL_REGRESSION_EVIDENCE":
        problems.append("CLASSIFICATION_INVALID")
    if data.get("git_commit_sha") != current_git:
        problems.append("GIT_COMMIT_MISMATCH")
    if data.get("status") != "PASS" or data.get("problems") not in ([], None):
        problems.append("MERGED_STATUS_NOT_PASS")
    shards = data.get("shards") if isinstance(data.get("shards"), list) else []
    if not shards:
        problems.append("SHARDS_MISSING")
    for item in shards:
        ref = item.get("manifest") if isinstance(item, dict) else None
        expected = item.get("manifest_sha256") if isinstance(item, dict) else None
        if not isinstance(ref, str):
            problems.append("SHARD_REFERENCE_MISSING")
            continue
        shard_path = root / ref
        if not shard_path.is_file():
            problems.append(f"SHARD_MANIFEST_MISSING:{ref}")
            continue
        if _sha(shard_path) != expected:
            problems.append(f"SHARD_MANIFEST_HASH_MISMATCH:{ref}")
            continue
        try:
            shard = json.loads(shard_path.read_text(encoding="utf-8"))
        except Exception:
            problems.append(f"SHARD_MANIFEST_INVALID_JSON:{ref}")
            continue
        if shard.get("git_commit_sha") != current_git:
            problems.append(f"SHARD_GIT_MISMATCH:{ref}")
        if shard.get("status") != "PASS" or shard.get("exit_code") != 0:
            problems.append(f"SHARD_NOT_PASS:{ref}")
        log_ref = shard.get("log")
        if not isinstance(log_ref, str):
            problems.append(f"SHARD_LOG_REFERENCE_MISSING:{ref}")
            continue
        log_path = root / log_ref
        if not log_path.is_file() or _sha(log_path) != shard.get("log_sha256"):
            problems.append(f"SHARD_LOG_HASH_INVALID:{ref}")
    verified = not problems
    return {
        "verified": verified,
        "status": "PASS" if verified else "BLOCKED",
        "problems": sorted(set(problems)),
        "manifest_sha256": _sha(path),
        "git_commit_sha": current_git,
        "test_file_count": data.get("test_file_count"),
        "shard_count": data.get("shard_count"),
    }


def main() -> int:
    result = verify_local_acceptance()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
