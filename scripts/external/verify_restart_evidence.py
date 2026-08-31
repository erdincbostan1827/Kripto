from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.runtime_restart_evidence import verify_restart_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify semantic Redis/PostgreSQL runtime restart evidence")
    parser.add_argument("path")
    parser.add_argument("--max-age-hours", type=int, default=24)
    args = parser.parse_args()
    evidence_path = Path(args.path).resolve()
    try:
        evidence_path.relative_to(ROOT.resolve())
    except ValueError:
        print(json.dumps({"status": "BLOCKED", "error": "evidence path must be inside project root"}, sort_keys=True))
        return 2
    result = verify_restart_evidence(evidence_path, root=ROOT, max_age_hours=max(1, args.max_age_hours))
    if not result.get("verified"):
        print(json.dumps({"status": "BLOCKED", "problems": result.get("problems", [])}, sort_keys=True))
        return 2
    rel = evidence_path.relative_to(ROOT.resolve()).as_posix()
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    print(json.dumps({"status": "PASS", "evidence_artifact": rel, "evidence_sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
