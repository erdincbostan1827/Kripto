#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
for search_root in (BACKEND, ROOT):
    text = str(search_root)
    if text not in sys.path:
        sys.path.insert(0, text)

from app.release.campaign_collector import (
    ReadOnlyBinancePublicCollector,
    acceptance_blockers,
    collection_event_counts,
    derive_collection_metrics,
    load_collection,
)
from app.release.campaign_runtime_adapter import ProtectedCampaignRuntimeAdapter
from scripts.external.phase266_campaign_runtime import _context, _save, _utc_now


def qualify_shadow(
    ctx: dict[str, Any],
    *,
    symbol: str,
    timeout_seconds: float,
    minimum_pairs: int = 100,
) -> dict[str, Any]:
    if timeout_seconds <= 0 or timeout_seconds > 30:
        raise ValueError("timeout_seconds must be in (0, 30]")
    if minimum_pairs < 100:
        raise ValueError("Phase267 live-shadow reconciliation requires at least 100 paired real observations")

    adapter: ProtectedCampaignRuntimeAdapter = ctx["adapter"]
    before_rows = load_collection(ctx["collection"], telemetry_key=ctx["telemetry_key"])
    before_metrics = derive_collection_metrics(before_rows)
    shadow_metrics = before_metrics["live-shadow"]

    kill_switch_status = "ALREADY_PASS"
    if not shadow_metrics["kill_switch_tested"]:
        snapshot = ReadOnlyBinancePublicCollector(timeout_seconds=timeout_seconds).snapshot(symbol)
        adapter.run_isolated_live_shadow_kill_switch_drill(snapshot, observed_at=_utc_now())
        kill_switch_status = "PASS"

    reconciliation_status = "ALREADY_PASS"
    reconciled_pairs = int(shadow_metrics.get("observations", 0))
    if not shadow_metrics["reconciliation_passed"]:
        try:
            reconciled_pairs = adapter.record_live_shadow_reconciliation(
                observed_at=_utc_now(),
                minimum_pairs=minimum_pairs,
            )
            reconciliation_status = "PASS"
        except RuntimeError as exc:
            if "paired real observations" not in str(exc):
                raise
            reconciliation_status = "PENDING_MINIMUM_REAL_PAIRS"

    state_payload = _save(ctx)
    rows = load_collection(ctx["collection"], telemetry_key=ctx["telemetry_key"])
    metrics = derive_collection_metrics(rows)
    return {
        "schema_version": "1.0",
        "classification": "PHASE267_PROTECTED_LIVE_SHADOW_QUALIFICATION",
        "candidate_sha": ctx["candidate"],
        "symbol": symbol.strip().upper(),
        "kill_switch_status": kill_switch_status,
        "reconciliation_status": reconciliation_status,
        "reconciled_pairs": reconciled_pairs,
        "runtime_state_checkpoint": state_payload["collection_last_record_sha256"],
        "event_counts": collection_event_counts(rows),
        "blockers": acceptance_blockers(metrics),
        "live_enabled": False,
        "production_ready": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase267 protected campaign qualification drills")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--topology-hash", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    shadow = sub.add_parser("shadow-qualification")
    shadow.add_argument("--symbol", default="BTCUSDT")
    shadow.add_argument("--timeout-seconds", type=float, default=10.0)
    shadow.add_argument("--minimum-pairs", type=int, default=100)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        ctx = _context(args)
        if args.command == "shadow-qualification":
            payload = qualify_shadow(
                ctx,
                symbol=args.symbol,
                timeout_seconds=args.timeout_seconds,
                minimum_pairs=args.minimum_pairs,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        raise RuntimeError("unsupported Phase267 command")
    except Exception as exc:
        print(
            json.dumps(
                {
                    "classification": "PHASE267_PROTECTED_CAMPAIGN_QUALIFICATION_FAIL_CLOSED",
                    "error": type(exc).__name__,
                    "message": str(exc),
                    "live_enabled": False,
                    "production_ready": False,
                },
                sort_keys=True,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
