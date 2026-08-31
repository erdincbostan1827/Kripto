from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.app.release.campaign_acceptance import verify_campaign_evidence

DEFAULTS = {
    "private-stream": "reports/external_acceptance/campaign/private_stream.json",
    "paper": "reports/external_acceptance/campaign/paper_campaign.json",
    "live-shadow": "reports/external_acceptance/campaign/live_shadow.json",
    "profitability": "reports/external_acceptance/campaign/profitability.json",
}


def main() -> int:
    p = argparse.ArgumentParser(description="Validate release-bound real campaign/private-stream evidence")
    p.add_argument("kind", choices=tuple(DEFAULTS))
    p.add_argument("--evidence")
    p.add_argument("--max-age-hours", type=int, default=168)
    args = p.parse_args()
    path = ROOT / (args.evidence or DEFAULTS[args.kind])
    result = verify_campaign_evidence(path, kind=args.kind, root=ROOT, max_age_hours=max(1, args.max_age_hours), strict_external=True)
    receipt = {**result, "evidence_artifact": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)}
    print(json.dumps(receipt, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
