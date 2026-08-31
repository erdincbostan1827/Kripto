from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.app.release.acceptance_challenge import create_challenge

if __name__ == "__main__":
    path = ROOT / "reports" / "external_acceptance" / "release_challenge.json"
    print(json.dumps(create_challenge(ROOT, path), indent=2, sort_keys=True))
