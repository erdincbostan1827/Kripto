#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
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

from app.core.enums import Signal
from app.exchange.private_stream import signature_subscription_request
from app.release.campaign_collector import (
    PUBLIC_BINANCE_ORIGIN,
    ReadOnlyBinancePublicCollector,
    acceptance_blockers,
    collection_event_counts,
    collection_path,
    derive_collection_metrics,
    environment_id_hash,
    initialize_collection,
    load_collection,
)
from app.release.campaign_runtime_adapter import LongIntent, ProtectedCampaignRuntimeAdapter
from app.release.campaign_runtime_state import restore_runtime_state, runtime_state_path, write_runtime_state
from app.services.pipeline import analyze

TELEMETRY_KEY_ENV = "PHASE265_TELEMETRY_HMAC_KEY"
TESTNET_API_KEY_ENV = "BINANCE_TESTNET_API_KEY"
TESTNET_API_SECRET_ENV = "BINANCE_TESTNET_API_SECRET"
TESTNET_WS_API = "wss://ws-api.testnet.binance.vision/ws-api/v3"
TESTNET_REST = "https://testnet.binance.vision"
ALLOWED_TIMEFRAMES = frozenset({"1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"})
BUY_SIGNALS = frozenset({Signal.BUY, Signal.STRONG_BUY})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _git_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    value = (proc.stdout or "").strip().lower()
    if proc.returncode != 0 or len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise RuntimeError("Phase266 could not resolve exact git HEAD")
    return value


def _required_env(name: str, *, min_bytes: int = 1) -> str:
    value = os.getenv(name, "")
    if len(value.encode("utf-8")) < min_bytes:
        raise ValueError(f"{name} is required and must contain at least {min_bytes} UTF-8 bytes")
    return value


def _context(args: argparse.Namespace) -> dict[str, Any]:
    candidate = str(args.candidate).strip().lower()
    if _git_sha() != candidate:
        raise PermissionError("Phase266 candidate must equal exact current git HEAD")
    state_dir = Path(args.state_dir)
    if not state_dir.is_absolute():
        raise ValueError("Phase266 state directory must be absolute")
    environment_id = str(args.environment_id).strip()
    topology_hash = str(args.topology_hash).strip().lower()
    telemetry_key = _required_env(TELEMETRY_KEY_ENV, min_bytes=32)
    environment_hash = environment_id_hash(environment_id)
    collection = collection_path(state_dir, repository_root=ROOT, candidate_sha=candidate)
    if not collection.exists():
        initialize_collection(
            collection,
            repository_root=ROOT,
            candidate_sha=candidate,
            environment_hash=environment_hash,
            topology_hash=topology_hash,
        )
    rows = load_collection(
        collection,
        candidate_sha=candidate,
        environment_hash=environment_hash,
        topology_hash=topology_hash,
        telemetry_key=telemetry_key,
    )
    adapter = ProtectedCampaignRuntimeAdapter(collection=collection, telemetry_key=telemetry_key)
    runtime_state = runtime_state_path(state_dir, repository_root=ROOT, candidate_sha=candidate)
    restored = restore_runtime_state(
        runtime_state,
        adapter,
        candidate_sha=candidate,
        environment_hash=environment_hash,
        topology_hash=topology_hash,
        telemetry_key=telemetry_key,
        current_collection_last_record_sha256=rows[-1]["record_sha256"],
    )
    if restored is None:
        acceptance_paper = [
            row
            for row in rows
            if row.get("record_type") == "event"
            and row.get("kind") == "paper_sample"
            and row.get("_phase265_attestation_verified") is True
        ]
        if acceptance_paper:
            raise RuntimeError(
                "Phase266 runtime state is missing while attested PAPER events already exist; "
                "refusing to reset broker continuity"
            )
    return {
        "candidate": candidate,
        "state_dir": state_dir,
        "environment_hash": environment_hash,
        "topology_hash": topology_hash,
        "telemetry_key": telemetry_key,
        "collection": collection,
        "runtime_state": runtime_state,
        "adapter": adapter,
        "restored": restored is not None,
    }


def _save(ctx: dict[str, Any]) -> dict[str, Any]:
    rows = load_collection(
        ctx["collection"],
        candidate_sha=ctx["candidate"],
        environment_hash=ctx["environment_hash"],
        topology_hash=ctx["topology_hash"],
        telemetry_key=ctx["telemetry_key"],
    )
    return write_runtime_state(
        ctx["runtime_state"],
        ctx["adapter"],
        candidate_sha=ctx["candidate"],
        environment_hash=ctx["environment_hash"],
        topology_hash=ctx["topology_hash"],
        telemetry_key=ctx["telemetry_key"],
        collection_last_record_sha256=rows[-1]["record_sha256"],
    )


def normalize_binance_klines(raw: Any, *, now: datetime | None = None) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise ValueError("Binance kline response must be a list")
    reference = (now or _utc_now()).astimezone(timezone.utc)
    out: list[dict[str, Any]] = []
    for index, row in enumerate(raw):
        if not isinstance(row, list) or len(row) < 7:
            raise ValueError(f"Binance kline row {index} is malformed")
        open_ms = int(row[0])
        close_ms = int(row[6])
        open_time = datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc)
        close_time = datetime.fromtimestamp(close_ms / 1000, tz=timezone.utc)
        if close_time > reference:
            continue
        out.append(
            {
                "open_time": open_time,
                "close_time": close_time,
                "open": Decimal(str(row[1])),
                "high": Decimal(str(row[2])),
                "low": Decimal(str(row[3])),
                "close": Decimal(str(row[4])),
                "volume": Decimal(str(row[5])),
                "closed": True,
            }
        )
    if len(out) < 50:
        raise ValueError("fewer than 50 closed Binance candles are available")
    return out


def fetch_strategy_decision(symbol: str, timeframe: str, *, timeout_seconds: float) -> Any:
    normalized_symbol = symbol.strip().upper()
    normalized_timeframe = timeframe.strip()
    if not normalized_symbol.isalnum() or len(normalized_symbol) > 20:
        raise ValueError("invalid Binance symbol")
    if normalized_timeframe not in ALLOWED_TIMEFRAMES:
        raise ValueError("unsupported Phase266 timeframe")
    if timeout_seconds <= 0 or timeout_seconds > 30:
        raise ValueError("timeout_seconds must be in (0, 30]")
    with httpx.Client(base_url=PUBLIC_BINANCE_ORIGIN, timeout=timeout_seconds, follow_redirects=False) as client:
        response = client.get(
            "/api/v3/klines",
            params={"symbol": normalized_symbol, "interval": normalized_timeframe, "limit": 250},
        )
        response.raise_for_status()
        raw = response.json()
    candles = normalize_binance_klines(raw)
    return analyze(candles, normalized_timeframe)


def derive_long_intent(
    decision: Any,
    snapshot: dict[str, Any],
    *,
    paper_notional: Decimal,
) -> LongIntent | None:
    if decision.signal not in BUY_SIGNALS:
        return None
    if paper_notional <= 0 or paper_notional > Decimal("1000"):
        raise ValueError("paper_notional must be >0 and <=1000")
    ask = Decimal(str(snapshot["ask_price"]))
    entry = decision.entry
    stop_loss = decision.stop_loss
    take_profits = tuple(decision.take_profits)
    if entry is None or stop_loss is None or len(take_profits) != 3:
        raise ValueError("BUY signal is missing protective levels")
    risk_distance = Decimal(str(entry)) - Decimal(str(stop_loss))
    if risk_distance <= 0:
        raise ValueError("BUY signal has non-positive protective risk distance")
    qty = paper_notional / ask
    if qty <= 0:
        raise ValueError("derived PAPER quantity is non-positive")
    return LongIntent(
        qty=qty,
        stop_loss=ask - risk_distance,
        take_profits=(
            ask + risk_distance,
            ask + risk_distance * Decimal("2"),
            ask + risk_distance * Decimal("3"),
        ),
    )


def strategy_cycle(
    ctx: dict[str, Any],
    *,
    symbol: str,
    timeframe: str,
    paper_notional: Decimal,
    latency_ms: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    if latency_ms < 0 or latency_ms > 60_000:
        raise ValueError("latency_ms must be in [0, 60000]")
    adapter: ProtectedCampaignRuntimeAdapter = ctx["adapter"]
    collector = ReadOnlyBinancePublicCollector(timeout_seconds=timeout_seconds)
    observed_at = _utc_now()
    snapshot = collector.snapshot(symbol)
    decision = fetch_strategy_decision(symbol, timeframe, timeout_seconds=timeout_seconds)
    position = adapter.paper_broker.positions.get(symbol.strip().upper())
    has_open_position = position is not None and not position.closed
    long_intent = None if has_open_position else derive_long_intent(
        decision,
        snapshot,
        paper_notional=paper_notional,
    )
    paper_decision = adapter.record_paper_quote(
        snapshot,
        market_regime=str(decision.regime),
        observed_at=observed_at,
        long_intent=long_intent,
        latency_ms=latency_ms,
    )
    shadow_decision = paper_decision if paper_decision in {"LONG", "EXIT"} else "HOLD"
    adapter.record_live_shadow_observation(
        snapshot,
        strategy_decision=shadow_decision,
        observed_at=observed_at,
    )
    state_payload = _save(ctx)
    rows = load_collection(ctx["collection"], telemetry_key=ctx["telemetry_key"])
    metrics = derive_collection_metrics(rows)
    return {
        "schema_version": "1.0",
        "classification": "PHASE266_PROTECTED_STRATEGY_CAMPAIGN_CYCLE",
        "candidate_sha": ctx["candidate"],
        "symbol": symbol.strip().upper(),
        "timeframe": timeframe,
        "strategy_signal": str(decision.signal),
        "strategy_score": int(decision.score),
        "strategy_confidence": float(decision.confidence),
        "market_regime": str(decision.regime),
        "paper_decision": paper_decision,
        "live_shadow_decision": shadow_decision,
        "runtime_state_checkpoint": state_payload["collection_last_record_sha256"],
        "event_counts": collection_event_counts(rows),
        "blockers": acceptance_blockers(metrics),
        "live_enabled": False,
        "production_ready": False,
    }


def _recv_json(ws: Any, *, timeout_seconds: float) -> dict[str, Any]:
    raw = ws.recv(timeout=timeout_seconds)
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("Binance WebSocket frame must be a JSON object")
    return loaded


def _await_response(
    ws: Any,
    *,
    request_id: str,
    adapter: ProtectedCampaignRuntimeAdapter,
    timeout_seconds: float,
    require_termination: bool = False,
) -> tuple[dict[str, Any], bool]:
    deadline = time.monotonic() + timeout_seconds
    response: dict[str, Any] | None = None
    termination = False
    while time.monotonic() < deadline:
        remaining = max(0.1, deadline - time.monotonic())
        message = _recv_json(ws, timeout_seconds=remaining)
        event = message.get("event")
        if isinstance(event, dict):
            adapter.record_private_message(message, observed_at=_utc_now())
            if event.get("e") == "eventStreamTerminated":
                termination = True
        if str(message.get("id", "")) == request_id:
            response = message
            status = int(message.get("status", 0))
            if status != 200:
                raise RuntimeError(f"Binance WebSocket request failed with status={status}")
        if response is not None and (termination or not require_termination):
            return response, termination
    raise TimeoutError("timed out waiting for Binance WebSocket response/termination")


def private_reconnect_drill(ctx: dict[str, Any], *, timeout_seconds: float) -> dict[str, Any]:
    if timeout_seconds <= 0 or timeout_seconds > 60:
        raise ValueError("private reconnect timeout must be in (0, 60]")
    api_key = _required_env(TESTNET_API_KEY_ENV)
    api_secret = _required_env(TESTNET_API_SECRET_ENV)
    adapter: ProtectedCampaignRuntimeAdapter = ctx["adapter"]

    from websockets.sync.client import connect

    with connect(TESTNET_WS_API, open_timeout=timeout_seconds, close_timeout=5) as ws:
        first = signature_subscription_request(api_key, api_secret)
        ws.send(json.dumps(first, separators=(",", ":")))
        first_ack, _ = _await_response(
            ws,
            request_id=str(first["id"]),
            adapter=adapter,
            timeout_seconds=timeout_seconds,
        )
        result = first_ack.get("result")
        if not isinstance(result, dict) or result.get("subscriptionId") is None:
            raise RuntimeError("Binance TESTNET subscription acknowledgement is incomplete")
        adapter.record_private_auth_request(first, testnet_origin=TESTNET_REST, observed_at=_utc_now())

        unsubscribe_id = str(uuid.uuid4())
        ws.send(json.dumps({"id": unsubscribe_id, "method": "userDataStream.unsubscribe"}, separators=(",", ":")))
        _, terminated = _await_response(
            ws,
            request_id=unsubscribe_id,
            adapter=adapter,
            timeout_seconds=timeout_seconds,
            require_termination=True,
        )
        if not terminated or adapter.private_projector.terminated is not True:
            raise RuntimeError("Binance TESTNET did not produce eventStreamTerminated")

        second = signature_subscription_request(api_key, api_secret)
        ws.send(json.dumps(second, separators=(",", ":")))
        second_ack, _ = _await_response(
            ws,
            request_id=str(second["id"]),
            adapter=adapter,
            timeout_seconds=timeout_seconds,
        )
        second_result = second_ack.get("result")
        if not isinstance(second_result, dict) or second_result.get("subscriptionId") is None:
            raise RuntimeError("Binance TESTNET resubscription acknowledgement is incomplete")
        adapter.record_private_reconnect(second, testnet_origin=TESTNET_REST, observed_at=_utc_now())

    state_payload = _save(ctx)
    rows = load_collection(ctx["collection"], telemetry_key=ctx["telemetry_key"])
    metrics = derive_collection_metrics(rows)
    return {
        "schema_version": "1.0",
        "classification": "PHASE266_BINANCE_TESTNET_PRIVATE_RECONNECT_DRILL",
        "candidate_sha": ctx["candidate"],
        "testnet_origin": TESTNET_REST,
        "websocket_origin": TESTNET_WS_API,
        "auth_lifecycle_passed": metrics["private-stream"]["auth_lifecycle_passed"],
        "reconnect_passed": metrics["private-stream"]["reconnect_passed"],
        "secrets_recorded": False,
        "runtime_state_checkpoint": state_payload["collection_last_record_sha256"],
        "event_counts": collection_event_counts(rows),
        "blockers": acceptance_blockers(metrics),
        "live_enabled": False,
        "production_ready": False,
    }


def runtime_status(ctx: dict[str, Any]) -> dict[str, Any]:
    rows = load_collection(ctx["collection"], telemetry_key=ctx["telemetry_key"])
    metrics = derive_collection_metrics(rows)
    position_rows = {
        symbol: {
            "open": not position.closed,
            "remaining_qty": str(position.remaining_qty),
            "triggered_take_profits": sorted(position.triggered_tps),
        }
        for symbol, position in sorted(ctx["adapter"].paper_broker.positions.items())
    }
    return {
        "schema_version": "1.0",
        "classification": "PHASE266_PROTECTED_CAMPAIGN_RUNTIME_STATUS_NOT_ACCEPTANCE_EVIDENCE",
        "candidate_sha": ctx["candidate"],
        "runtime_state_restored": ctx["restored"],
        "collection_path": str(ctx["collection"].resolve()),
        "runtime_state_path": str(ctx["runtime_state"].resolve()),
        "event_counts": collection_event_counts(rows),
        "metrics": metrics,
        "paper_positions": position_rows,
        "blockers": acceptance_blockers(metrics),
        "live_enabled": False,
        "production_ready": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase266 protected real campaign runtime")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--topology-hash", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    cycle = sub.add_parser("strategy-cycle")
    cycle.add_argument("--symbol", default="BTCUSDT")
    cycle.add_argument("--timeframe", default="1h")
    cycle.add_argument("--paper-notional", type=Decimal, default=Decimal("10"))
    cycle.add_argument("--latency-ms", type=int, default=50)
    cycle.add_argument("--timeout-seconds", type=float, default=10.0)

    loop = sub.add_parser("strategy-loop")
    loop.add_argument("--symbol", default="BTCUSDT")
    loop.add_argument("--timeframe", default="1h")
    loop.add_argument("--paper-notional", type=Decimal, default=Decimal("10"))
    loop.add_argument("--latency-ms", type=int, default=50)
    loop.add_argument("--timeout-seconds", type=float, default=10.0)
    loop.add_argument("--interval-seconds", type=float, default=300.0)
    loop.add_argument("--max-cycles", type=int, default=0)

    private = sub.add_parser("private-reconnect-drill")
    private.add_argument("--timeout-seconds", type=float, default=20.0)

    sub.add_parser("status")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        ctx = _context(args)
        if args.command == "strategy-cycle":
            payload = strategy_cycle(
                ctx,
                symbol=args.symbol,
                timeframe=args.timeframe,
                paper_notional=args.paper_notional,
                latency_ms=args.latency_ms,
                timeout_seconds=args.timeout_seconds,
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "strategy-loop":
            interval = float(args.interval_seconds)
            if interval < 30 or interval > 86_400:
                raise ValueError("strategy-loop interval_seconds must be in [30, 86400]")
            max_cycles = int(args.max_cycles)
            if max_cycles < 0:
                raise ValueError("max_cycles cannot be negative")
            completed = 0
            while max_cycles == 0 or completed < max_cycles:
                payload = strategy_cycle(
                    ctx,
                    symbol=args.symbol,
                    timeframe=args.timeframe,
                    paper_notional=args.paper_notional,
                    latency_ms=args.latency_ms,
                    timeout_seconds=args.timeout_seconds,
                )
                print(json.dumps(payload, sort_keys=True), flush=True)
                completed += 1
                if max_cycles and completed >= max_cycles:
                    break
                time.sleep(interval)
            return 0
        if args.command == "private-reconnect-drill":
            payload = private_reconnect_drill(ctx, timeout_seconds=args.timeout_seconds)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "status":
            print(json.dumps(runtime_status(ctx), indent=2, sort_keys=True))
            return 0
        raise RuntimeError("unsupported Phase266 command")
    except Exception as exc:
        print(
            json.dumps(
                {
                    "classification": "PHASE266_PROTECTED_CAMPAIGN_RUNTIME_FAIL_CLOSED",
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
