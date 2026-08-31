from __future__ import annotations
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.app.release.evidence_ledger_checkpoint import DEFAULT_PATH, verify_ledger_checkpoint

def main() -> int:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (ROOT / DEFAULT_PATH)
    env = {
        "acceptance_environment_id_hash": __import__("hashlib").sha256(__import__("os").environ.get("ACCEPTANCE_ENVIRONMENT_ID", "").encode()).hexdigest() if __import__("os").environ.get("ACCEPTANCE_ENVIRONMENT_ID") else None,
        "topology_hash": __import__("os").environ.get("ACCEPTANCE_TOPOLOGY_HASH", "").lower() or None,
    }
    result = verify_ledger_checkpoint(path, root=ROOT, expected_environment=env, require_external_trust=True)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("verified") else 2
if __name__ == "__main__":
    raise SystemExit(main())
