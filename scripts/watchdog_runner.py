from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

from app.monitoring.watchdog import HeartbeatSigner


def validate_http_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("watchdog URLs must use HTTP(S) and include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("watchdog URLs must not contain embedded credentials")
    # Force port parsing here so malformed/out-of-range ports fail before any request.
    _ = parsed.port
    return url


def fetch_json(url: str, timeout: float = 4.0) -> dict:
    response = httpx.get(
        validate_http_url(url),
        timeout=timeout,
        follow_redirects=False,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("watchdog endpoint must return a JSON object")
    return payload


def emit_alert(message: str) -> None:
    webhook = os.getenv("CRITICAL_FALLBACK_WEBHOOK", "").strip()
    payload = json.dumps(
        {
            "severity": "SEV1",
            "message": message,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    ).encode("utf-8")
    if webhook:
        try:
            response = httpx.post(
                validate_http_url(webhook),
                content=payload,
                headers={"Content-Type": "application/json"},
                timeout=5.0,
                follow_redirects=False,
            )
            response.raise_for_status()
            return
        except Exception as exc:
            print(f"WATCHDOG_ALERT_DELIVERY_FAILED:{type(exc).__name__}", file=sys.stderr)
    print(f"WATCHDOG_CRITICAL:{message}", file=sys.stderr)


def main() -> None:
    target = os.getenv("WATCHDOG_TARGET_URL", "http://app:8000").rstrip("/")
    interval = max(5, int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "15")))
    threshold = max(1, int(os.getenv("WATCHDOG_FAILURE_THRESHOLD", "3")))
    key = os.getenv("HEARTBEAT_HMAC_KEY", "watchdog-local-nonprod").encode()
    signer = HeartbeatSigner(key)
    failures = 0
    while True:
        try:
            health = fetch_json(f"{target}/health")
            ready = health.get("ready_for_new_risk", False)
            message = {
                "target": target,
                "ready_for_new_risk": ready,
                "checked_at": time.time(),
            }
            signature = signer.sign(message)
            print(
                json.dumps({"heartbeat": message, "signature": signature}, sort_keys=True),
                flush=True,
            )
            if not ready:
                failures += 1
            else:
                failures = 0
        except Exception as exc:
            failures += 1
            print(f"WATCHDOG_PROBE_FAILED:{type(exc).__name__}", file=sys.stderr)
        if failures >= threshold:
            emit_alert(f"Trading platform watchdog failure threshold reached ({failures}).")
            failures = 0
        time.sleep(interval)


if __name__ == "__main__":
    main()
