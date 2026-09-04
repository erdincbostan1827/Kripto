from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from app.backtest.dataset import ReproducibilityManifest, verify_reproducibility_manifest
from app.backtest.engine import BacktestResult
from app.exchange.private_stream import PrivateStreamProjector, ProjectionResult, parse_user_event
from app.paper.engine import PaperBroker
from app.release.campaign_collector import (
    PUBLIC_BINANCE_ORIGIN,
    append_attested_runtime_event,
    load_collection,
)

D = Decimal


@dataclass(frozen=True)
class LongIntent:
    qty: Decimal
    stop_loss: Decimal
    take_profits: tuple[Decimal, Decimal, Decimal]


class ProtectedCampaignRuntimeAdapter:
    """Bridge real runtime outcomes into Phase265 attested campaign telemetry.

    The adapter deliberately has no exchange order client and exposes no generic
    `append(kind, payload)` method. Acceptance-eligible events are derived from
    concrete runtime primitives: PrivateStreamProjector, PaperBroker, read-only
    Binance snapshots, and hash-verified reproducibility/backtest objects.
    """

    def __init__(self, *, collection: Path, telemetry_key: str) -> None:
        self._collection = collection
        self._telemetry_key = telemetry_key
        self._private = PrivateStreamProjector()
        self._paper = PaperBroker()
        self._shadow_halted = False

    @property
    def private_projector(self) -> PrivateStreamProjector:
        return self._private

    @property
    def paper_broker(self) -> PaperBroker:
        return self._paper

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("runtime observation timestamps must be timezone-aware")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _snapshot(snapshot: dict[str, Any]) -> tuple[str, Decimal, Decimal]:
        if str(snapshot.get("market_data_origin", "")).upper() != "REAL":
            raise ValueError("runtime market snapshot must be REAL")
        if str(snapshot.get("public_origin", "")) != PUBLIC_BINANCE_ORIGIN:
            raise ValueError("runtime market snapshot must come from the pinned read-only Binance origin")
        symbol = str(snapshot.get("symbol", "")).strip().upper()
        bid = D(str(snapshot.get("bid_price")))
        ask = D(str(snapshot.get("ask_price")))
        if not symbol or bid <= 0 or ask <= 0 or ask < bid:
            raise ValueError("runtime market snapshot is invalid")
        return symbol, bid, ask

    def _emit(self, *, kind: str, payload: dict[str, Any], observed_at: datetime, producer: str) -> dict[str, Any]:
        return append_attested_runtime_event(
            self._collection,
            kind=kind,
            payload=payload,
            observed_at=self._utc(observed_at),
            producer=producer,
            telemetry_key=self._telemetry_key,
        )

    def record_private_message(self, message: dict[str, Any], *, observed_at: datetime) -> ProjectionResult:
        event = parse_user_event(message)
        result = cast(ProjectionResult, self._private.project(event))
        canonical = json.dumps(message, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        event_id = hashlib.sha256(canonical).hexdigest()
        self._emit(
            kind="private_event",
            payload={"event_id": event_id, "classification": result.classification, "action": result.action},
            observed_at=observed_at,
            producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
        )
        if result.classification in {"DUPLICATE_FILL", "DUPLICATE_ORDER_EVENT"}:
            self._emit(
                kind="private_duplicate_idempotency",
                payload={"classification": result.classification, "action": result.action},
                observed_at=observed_at,
                producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
            )
        if result.classification in {"STALE_ORDER_EVENT", "OUT_OF_ORDER_ORDER_EVENT"}:
            self._emit(
                kind="private_out_of_order",
                payload={"classification": result.classification, "action": result.action},
                observed_at=observed_at,
                producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
            )
        self._emit(
            kind="private_redaction",
            payload={"recorded_fields": ["event_id", "classification", "action"], "raw_credentials_recorded": False},
            observed_at=observed_at,
            producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
        )
        return result

    def record_private_auth_request(self, request: dict[str, Any], *, testnet_origin: str, observed_at: datetime) -> None:
        params = request.get("params")
        if request.get("method") != "userDataStream.subscribe.signature" or not isinstance(params, dict):
            raise ValueError("private auth lifecycle requires an actual signed subscription request")
        if not all(str(params.get(field, "")).strip() for field in ("apiKey", "signature", "timestamp")):
            raise ValueError("private auth lifecycle request is incomplete")
        normalized_origin = testnet_origin.rstrip("/").lower()
        if "testnet.binance.vision" not in normalized_origin:
            raise ValueError("private campaign credentials must target Binance Spot TESTNET")
        self._emit(
            kind="private_auth_lifecycle",
            payload={"method": request["method"], "target": "BINANCE_SPOT_TESTNET", "credential_material_recorded": False},
            observed_at=observed_at,
            producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
        )

    def record_private_reconnect(self, request: dict[str, Any], *, testnet_origin: str, observed_at: datetime) -> None:
        if self._private.terminated is not True:
            raise RuntimeError("private reconnect evidence requires an observed stream termination")
        self.record_private_auth_request(request, testnet_origin=testnet_origin, observed_at=observed_at)
        self._emit(
            kind="private_reconnect",
            payload={"termination_observed": True, "resubscription_validated": True},
            observed_at=observed_at,
            producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
        )

    def record_private_rest_reconciliation(
        self,
        rest_balances: dict[str, tuple[Decimal, Decimal]],
        *,
        observed_at: datetime,
    ) -> None:
        normalized = {str(asset): (D(free), D(locked)) for asset, (free, locked) in rest_balances.items()}
        if normalized != self._private.balances:
            raise RuntimeError("private REST reconciliation does not match projected stream balances")
        self._emit(
            kind="private_rest_reconciliation",
            payload={"assets_compared": len(normalized), "exact_match": True},
            observed_at=observed_at,
            producer="PROTECTED_PRIVATE_STREAM_RUNTIME",
        )

    def record_paper_quote(
        self,
        snapshot: dict[str, Any],
        *,
        market_regime: str,
        observed_at: datetime,
        long_intent: LongIntent | None = None,
        latency_ms: int = 50,
    ) -> str:
        symbol, bid, ask = self._snapshot(snapshot)
        before = len(self._paper.fills)
        if long_intent is not None:
            take_profits = (
                D(long_intent.take_profits[0]),
                D(long_intent.take_profits[1]),
                D(long_intent.take_profits[2]),
            )
            self._paper.open_long(
                symbol,
                D(long_intent.qty),
                bid,
                ask,
                D(long_intent.stop_loss),
                take_profits,
                latency_ms=latency_ms,
            )
            decision = "LONG"
        else:
            generated = self._paper.on_quote(symbol, bid, ask, latency_ms=latency_ms)
            decision = "EXIT" if generated else "HOLD"
        new_fills = self._paper.fills[before:]
        mid = (bid + ask) / D("2")
        divergence = max(
            (abs(fill.price - mid) / mid * D("10000") for fill in new_fills),
            default=D("0"),
        )
        sample_seed = f"{symbol}|{snapshot.get('observation_id', '')}|{decision}|{len(self._paper.fills)}"
        self._emit(
            kind="paper_sample",
            payload={
                "sample_id": hashlib.sha256(sample_seed.encode("utf-8")).hexdigest(),
                "decision": decision,
                "market_regime": str(market_regime).strip().upper(),
                "market_data_origin": "REAL",
                "execution_divergence_bps": float(divergence),
                "paper_fill_count": len(new_fills),
            },
            observed_at=observed_at,
            producer="PROTECTED_PAPER_RUNTIME",
        )
        return decision

    def record_live_shadow_observation(
        self,
        snapshot: dict[str, Any],
        *,
        strategy_decision: str,
        observed_at: datetime,
    ) -> None:
        if self._shadow_halted:
            raise RuntimeError("live-shadow kill-switch is active")
        symbol, bid, ask = self._snapshot(snapshot)
        decision = str(strategy_decision).strip().upper()
        if decision not in {"LONG", "EXIT", "HOLD"}:
            raise ValueError("spot live-shadow strategy decision must be LONG, EXIT, or HOLD")
        observation_id = str(snapshot.get("observation_id", "")).strip()
        if not observation_id:
            observation_id = hashlib.sha256(f"{symbol}|{bid}|{ask}|{observed_at.isoformat()}".encode("utf-8")).hexdigest()
        self._emit(
            kind="live_shadow_observation",
            payload={
                "observation_id": observation_id,
                "symbol": symbol,
                "strategy_decision": decision,
                "market_data_origin": "REAL",
                "submit_capability_present": False,
            },
            observed_at=observed_at,
            producer="PROTECTED_LIVE_SHADOW_RUNTIME",
        )

    def test_live_shadow_kill_switch(self, snapshot: dict[str, Any], *, observed_at: datetime) -> None:
        self._shadow_halted = True
        refused = False
        try:
            self.record_live_shadow_observation(snapshot, strategy_decision="HOLD", observed_at=observed_at)
        except RuntimeError:
            refused = True
        if not refused:
            raise RuntimeError("live-shadow kill-switch did not refuse observation processing")
        self._emit(
            kind="live_shadow_kill_switch_pass",
            payload={"refused_while_halted": True, "submit_capability_present": False},
            observed_at=observed_at,
            producer="PROTECTED_LIVE_SHADOW_RUNTIME",
        )

    def record_profitability_backtest(
        self,
        *,
        manifest: ReproducibilityManifest,
        rows: list[dict[str, Any]],
        result: BacktestResult,
        oos_start: datetime,
        observed_at: datetime,
    ) -> int:
        collection_rows = load_collection(self._collection, telemetry_key=self._telemetry_key)
        candidate = str(collection_rows[0]["candidate_sha"])
        if not verify_reproducibility_manifest(manifest, rows):
            raise ValueError("profitability dataset manifest hash verification failed")
        if manifest.code_git_sha.lower() != candidate:
            raise ValueError("profitability dataset manifest is bound to a different code SHA")
        if not manifest.source.strip() or "synthetic" in manifest.source.lower() or "mock" in manifest.source.lower():
            raise ValueError("profitability dataset source is not eligible as real PIT input")
        cutoff = self._utc(oos_start)
        emitted = 0
        for index, trade in enumerate(result.trades):
            entry_time = trade.entry_time
            if not isinstance(entry_time, datetime) or entry_time.tzinfo is None:
                raise ValueError("profitability trade entry_time must be timezone-aware datetime")
            if entry_time.astimezone(timezone.utc) < cutoff:
                raise ValueError("profitability result contains an in-sample trade")
            notional = D(trade.entry) * D(trade.qty)
            if notional <= 0:
                raise ValueError("profitability trade notional must be positive")
            net_return_bps = float(D(trade.pnl) / notional * D("10000"))
            self._emit(
                kind="profitability_sample",
                payload={
                    "sample_id": f"{manifest.dataset_hash}:{index}",
                    "net_return_bps": net_return_bps,
                    "data_origin": "REAL_PIT",
                    "split": "OOS",
                    "dataset_hash": manifest.dataset_hash,
                },
                observed_at=entry_time,
                producer="PROTECTED_PIT_RUNTIME",
            )
            emitted += 1
        if emitted:
            self._emit(
                kind="profitability_oos_pass",
                payload={"dataset_hash": manifest.dataset_hash, "oos_trade_count": emitted, "cutoff": cutoff.isoformat()},
                observed_at=observed_at,
                producer="PROTECTED_PIT_RUNTIME",
            )
        return emitted
