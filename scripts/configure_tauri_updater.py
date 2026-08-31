from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def build_updater_fragment(*, public_key: str, endpoint: str) -> dict:
    key = public_key.strip()
    if len(key) < 32 or "REPLACE" in key.upper():
        raise ValueError("a real Tauri signer public key is required")
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("production updater endpoint must use HTTPS")
    if parsed.username or parsed.password:
        raise ValueError("updater endpoint must not contain URL credentials")
    return {
        "bundle": {"createUpdaterArtifacts": True},
        "plugins": {
            "updater": {
                "pubkey": key,
                "endpoints": [endpoint],
                "dangerousInsecureTransportProtocol": False,
                "dangerousAcceptInvalidCerts": False,
                "dangerousAcceptInvalidHostnames": False,
            }
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a fail-closed Tauri signed-updater config fragment")
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fragment = build_updater_fragment(public_key=args.public_key, endpoint=args.endpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fragment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
