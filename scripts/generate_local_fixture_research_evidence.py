from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.research.final_evidence import build_local_fixture_evidence

OUT = ROOT / "reports" / "LOCAL_FIXTURE_RESEARCH_EVIDENCE.json"


def _fixture_returns(n: int = 90) -> list[float]:
    pattern = [0.0030, -0.0010, 0.0020, -0.0005, 0.0015, 0.0002]
    return [pattern[i % len(pattern)] for i in range(n)]


def build_payload() -> dict[str, object]:
    returns = _fixture_returns()
    benchmark = [x * 0.25 for x in returns]
    evidence = build_local_fixture_evidence(returns, benchmark_returns=benchmark)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": evidence.classification,
        "truth_policy": (
            "This deterministic fixture report validates research/reporting code paths only. "
            "It MUST NOT satisfy real-market PAPER, TESTNET, LIVE-shadow, or production profitability gates."
        ),
        "fixture": {
            "observations": len(returns),
            "deterministic": True,
            "real_market_data": False,
            "credentialed_exchange": False,
        },
        "evidence": evidence.as_dict(),
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        shown = OUT.relative_to(ROOT)
    except ValueError:
        shown = OUT
    print(shown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
