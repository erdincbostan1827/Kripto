from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for search_root in (ROOT, BACKEND):
    search_root_text = str(search_root)
    if search_root_text not in sys.path:
        sys.path.insert(0, search_root_text)
from backend.app.release.acceptance_challenge import create_challenge

if __name__ == "__main__":
    path = ROOT / "reports" / "external_acceptance" / "release_challenge.json"
    print(json.dumps(create_challenge(ROOT, path), indent=2, sort_keys=True))
