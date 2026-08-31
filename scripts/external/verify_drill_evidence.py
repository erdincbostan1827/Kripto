from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.drill_evidence import (  # noqa: E402
    DrillEvidenceError,
    verify_ha_evidence,
    verify_restore_evidence,
    verify_worm_evidence,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify real external drill evidence")
    parser.add_argument("kind", choices=("pitr", "ha", "worm"))
    parser.add_argument("path")
    parser.add_argument("--max-age-hours", type=int, default=24)
    args = parser.parse_args()
    verifiers = {"pitr": verify_restore_evidence, "ha": verify_ha_evidence, "worm": verify_worm_evidence}
    try:
        data = verifiers[args.kind](Path(args.path), root=ROOT, max_age_hours=max(1, args.max_age_hours))
    except (DrillEvidenceError, OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True))
        return 2
    evidence_path = Path(args.path).resolve()
    try:
        rel = evidence_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        print(json.dumps({"status": "BLOCKED", "error": "evidence path must be inside project root"}, sort_keys=True))
        return 2
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    print(json.dumps({"status": "PASS", "drill_kind": data["drill_kind"], "git_commit_sha": data["git_commit_sha"], "evidence_artifact": rel, "evidence_sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
