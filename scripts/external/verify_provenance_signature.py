from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.provenance_signature_evidence import verify_provenance_signature_evidence

DEFAULT = ROOT / "reports" / "external_acceptance" / "provenance_signature_verification.json"


def main() -> int:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT
    result = verify_provenance_signature_evidence(path, root=ROOT, strict_external=True)
    payload = {**result, "evidence_artifact": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)}
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.get("verified") else 2


if __name__ == "__main__":
    raise SystemExit(main())
