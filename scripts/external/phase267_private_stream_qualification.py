#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
for search_root in (BACKEND, ROOT):
    text = str(search_root)
    if text not in sys.path:
        sys.path.insert(0, text)

from app.exchange.private_stream import signature_subscription_request
from app.release.campaign_collector import acceptance_blockers, collection_event_counts, derive_collection_metrics, load_collection
from app.release.campaign_runtime_adapter import ProtectedCampaignRuntimeAdapter
from scripts.external.phase266_campaign_runtime import TESTNET_REST, TESTNET_WS_API, _context, _save, _utc_now

API_KEY_ENV = "BINANCE_TESTNET_API_KEY"
SIGNING_ENV = "BINANCE_TESTNET_API_SECRET"


def _required_env(name: str) -> str:
    value = os.getenv(name, "")
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _signed_query(params: dict[str, Any], signing_material: str) -> str:
    canonical = urllib.parse.urlencode(sorted((str(key), str(value)) for key, value in params.items()))
    signature = hmac.new(signing_material.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{canonical}&signature={signature}"


def _server_time(client: httpx.Client) -> int:
    response = client.get("/api/v3/time")
    response.raise_for_status()
    payload = response.json()
    timestamp = int(payload.get("serverTime", 0))
    if timestamp <= 0:
        raise RuntimeError("Binance TESTNET serverTime is invalid")
    return timestamp


def _signed_rest(
    client: httpx.Client,
    *,
    method: str,
    path: str,
    api_key: str,
    signing_material: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    signed = _signed_query(params, signing_material)
    response = client.request(method, f"{path}?{signed}", headers={"X-MBX-APIKEY": api_key})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Binance TESTNET signed REST response must be an object")
    return payload


def _rest_balances(payload: dict[str, Any]) -> dict[str, tuple[Decimal, Decimal]]:
    rows = payload.get("balances")
    if not isinstance(rows, list):
        raise RuntimeError("Binance TESTNET account response has no balances array")
    out: dict[str, tuple[Decimal, Decimal]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        asset = str(row.get("asset", "")).strip()
        if not asset:
            continue
        free = Decimal(str(row.get("free", "0")))
        locked = Decimal(str(row.get("locked", "0")))
        out[asset] = (free, locked)
    if not out:
        raise RuntimeError("Binance TESTNET account response contained no assets")
    return out


def _recv_json(ws: Any, *, timeout_seconds: float) -> dict[str, Any]:
    raw = ws.recv(timeout=timeout_seconds)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("Binance TESTNET private frame must be an object")
    return payload


def _await_request_response(
    ws: Any,
    *,
    request_id: str,
    adapter: ProtectedCampaignRuntimeAdapter,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        message = _recv_json(ws, timeout_seconds=max(0.1, deadline - time.monotonic()))
        if isinstance(message.get("event"), dict):
            adapter.record_private_message(message, observed_at=_utc_now())
        if str(message.get("id", "")) == request_id:
            status = int(message.get("status", 0))
            if status != 200:
                raise RuntimeError(f"Binance TESTNET WebSocket request failed with status={status}")
            return message
    raise TimeoutError("timed out waiting for Binance TESTNET subscription response")


def qualify_private_stream(
    ctx: dict[str, Any],
    *,
    symbol: str,
    max_notional: Decimal,
    timeout_seconds: float,
) -> dict[str, Any]:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol.isalnum() or len(normalized_symbol) > 20:
        raise ValueError("invalid Binance TESTNET symbol")
    if max_notional < Decimal("5") or max_notional > Decimal("15"):
        raise ValueError("Phase267 TESTNET max_notional must be in [5,15]")
    if timeout_seconds <= 0 or timeout_seconds > 60:
        raise ValueError("timeout_seconds must be in (0,60]")

    api_key = _required_env(API_KEY_ENV)
    signing_material = _required_env(SIGNING_ENV)
    adapter: ProtectedCampaignRuntimeAdapter = ctx["adapter"]

    from websockets.sync.client import connect

    execution_messages: list[dict[str, Any]] = []
    balance_snapshot_seen = False
    client_order_id = f"ctp-p267-{uuid.uuid4().hex[:20]}"

    with connect(TESTNET_WS_API, open_timeout=timeout_seconds, close_timeout=5) as ws:
        subscribe = signature_subscription_request(api_key, signing_material)
        ws.send(json.dumps(subscribe, separators=(",", ":")))
        ack = _await_request_response(
            ws,
            request_id=str(subscribe["id"]),
            adapter=adapter,
            timeout_seconds=timeout_seconds,
        )
        result = ack.get("result")
        if not isinstance(result, dict) or result.get("subscriptionId") is None:
            raise RuntimeError("Binance TESTNET private subscription acknowledgement is incomplete")
        adapter.record_private_auth_request(subscribe, testnet_origin=TESTNET_REST, observed_at=_utc_now())

        with httpx.Client(base_url=TESTNET_REST, timeout=timeout_seconds, follow_redirects=False) as client:
            timestamp = _server_time(client)
            order = _signed_rest(
                client,
                method="POST",
                path="/api/v3/order",
                api_key=api_key,
                signing_material=signing_material,
                params={
                    "newClientOrderId": client_order_id,
                    "quoteOrderQty": str(max_notional),
                    "recvWindow": 5000,
                    "side": "BUY",
                    "symbol": normalized_symbol,
                    "timestamp": timestamp,
                    "type": "MARKET",
                },
            )
            if str(order.get("clientOrderId", "")) != client_order_id:
                raise RuntimeError("Binance TESTNET order response clientOrderId mismatch")

            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                message = _recv_json(ws, timeout_seconds=max(0.1, deadline - time.monotonic()))
                event = message.get("event") if isinstance(message.get("event"), dict) else message
                if not isinstance(event, dict) or not event.get("e"):
                    continue
                adapter.record_private_message(message, observed_at=_utc_now())
                if event.get("e") == "executionReport" and str(event.get("c", "")) == client_order_id:
                    execution_messages.append(message)
                if event.get("e") == "outboundAccountPosition":
                    balance_snapshot_seen = True
                if len(execution_messages) >= 2 and balance_snapshot_seen:
                    break

            if len(execution_messages) < 2:
                raise RuntimeError(
                    "private qualification requires at least two real TESTNET executionReport transitions for out-of-order replay"
                )
            if not balance_snapshot_seen or not adapter.private_projector.balances:
                raise RuntimeError("private qualification did not observe a real TESTNET outboundAccountPosition snapshot")

            duplicate = adapter.record_private_message(execution_messages[-1], observed_at=_utc_now())
            if duplicate.classification not in {"DUPLICATE_FILL", "DUPLICATE_ORDER_EVENT"}:
                raise RuntimeError(f"duplicate replay was not rejected idempotently: {duplicate.classification}")

            stale = adapter.record_private_message(execution_messages[0], observed_at=_utc_now())
            if stale.classification not in {"STALE_ORDER_EVENT", "OUT_OF_ORDER_ORDER_EVENT"}:
                raise RuntimeError(f"out-of-order replay was not rejected: {stale.classification}")

            account = _signed_rest(
                client,
                method="GET",
                path="/api/v3/account",
                api_key=api_key,
                signing_material=signing_material,
                params={"omitZeroBalances": "false", "recvWindow": 5000, "timestamp": _server_time(client)},
            )
            all_rest_balances = _rest_balances(account)
            projected_assets = set(adapter.private_projector.balances)
            if not projected_assets:
                raise RuntimeError("private qualification projected no assets for REST reconciliation")
            missing = sorted(projected_assets - set(all_rest_balances))
            if missing:
                raise RuntimeError(f"REST reconciliation is missing projected assets: {','.join(missing)}")
            rest_subset = {asset: all_rest_balances[asset] for asset in projected_assets}
            adapter.record_private_rest_reconciliation(rest_subset, observed_at=_utc_now())

    state_payload = _save(ctx)
    rows = load_collection(ctx["collection"], telemetry_key=ctx["telemetry_key"])
    metrics = derive_collection_metrics(rows)
    private = metrics["private-stream"]
    if not all(
        (
            private["credentialed_testnet"],
            private["auth_lifecycle_passed"],
            private["rest_reconciliation_passed"],
            private["duplicate_event_idempotency_passed"],
            private["out_of_order_protection_passed"],
            private["secrets_redacted"],
        )
    ):
        raise RuntimeError("Phase267 private qualification metrics did not close all non-reconnect private controls")

    return {
        "schema_version": "1.0",
        "classification": "PHASE267_BINANCE_TESTNET_PRIVATE_STREAM_QUALIFICATION",
        "candidate_sha": ctx["candidate"],
        "testnet_origin": TESTNET_REST,
        "symbol": normalized_symbol,
        "max_notional": str(max_notional),
        "real_execution_reports": len(execution_messages),
        "projected_assets_reconciled": len(adapter.private_projector.balances),
        "duplicate_replay_passed": True,
        "out_of_order_replay_passed": True,
        "rest_reconciliation_passed": True,
        "secrets_recorded": False,
        "runtime_state_checkpoint": state_payload["collection_last_record_sha256"],
        "event_counts": collection_event_counts(rows),
        "blockers": acceptance_blockers(metrics),
        "live_enabled": False,
        "production_ready": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase267 real Binance TESTNET private-stream qualification")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--topology-hash", required=True)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--max-notional", type=Decimal, default=Decimal("5"))
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        ctx = _context(args)
        payload = qualify_private_stream(
            ctx,
            symbol=args.symbol,
            max_notional=args.max_notional,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "classification": "PHASE267_PRIVATE_STREAM_QUALIFICATION_FAIL_CLOSED",
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
