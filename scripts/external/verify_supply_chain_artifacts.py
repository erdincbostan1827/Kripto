from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.supply_chain_evidence import verify_supply_chain_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Semantically verify CycloneDX SBOM and dependency license report")
    parser.add_argument("--sbom", default="reports/external_acceptance/sbom.cdx.json")
    parser.add_argument("--licenses", default="reports/external_acceptance/dependency_licenses.json")
    args = parser.parse_args()
    result = verify_supply_chain_artifacts(ROOT / args.sbom, ROOT / args.licenses)
    out = ROOT / "reports" / "external_acceptance" / "supply_chain_artifact_verification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
