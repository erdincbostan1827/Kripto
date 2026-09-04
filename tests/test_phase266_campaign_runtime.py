from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.enums import Signal
from app.release.campaign_collector import collection_path, initialize_collection, load_collection
from app.release.campaign_runtime_adapter import LongIntent, ProtectedCampaignRuntimeAdapter
from app.release.campaign_runtime_state import restore_runtime_state, runtime_state_path, write_runtime_state
from scripts.external.phase266_campaign_runtime import (
    TESTNET_WS_API,
    derive_long_intent,
    normalize_binance_klines,
)

CANDIDATE = "a" * 40
ENV_HASH = "b" * 64
TOPOLOGY_HASH = "c" * 64
KEY = "phase266-runtime-state-telemetry-key-material-000000000001"


def _adapter(tmp_path: Path) -> tuple[ProtectedCampaignRuntimeAdapter, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    state_dir = (tmp_path / "state").resolve()
    collection = collection_path(state_dir, repository_root=repo, candidate_sha=CANDIDATE)
    initialize_collection(
        collection,
        repository_root=repo,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
    )
    state_path = runtime_state_path(state_dir, repository_root=repo, candidate_sha=CANDIDATE)
    return ProtectedCampaignRuntimeAdapter(collection=collection, telemetry_key=KEY), collection, state_path


def _snapshot(observation_id: str = "quote-1") -> dict[str, object]:
    return {
        "observation_id": observation_id,
        "symbol": "BTCUSDT",
        "bid_price": "100.00",
        "ask_price": "100.01",
        "market_data_origin": "REAL",
        "public_origin": "https://api.binance.com",
    }


def test_runtime_state_round_trip_preserves_paper_and_private_continuity(tmp_path: Path) -> None:
    adapter, collection, state_path = _adapter(tmp_path)
    now = datetime.now(timezone.utc)
    adapter.record_paper_quote(
        _snapshot(),
        market_regime="BULLISH_TREND",
        observed_at=now,
        long_intent=LongIntent(
            qty=Decimal("0.1"),
            stop_loss=Decimal("99.50"),
            take_profits=(Decimal("100.50"), Decimal("101.00"), Decimal("101.50")),
        ),
    )
    adapter.record_private_message(
        {
            "e": "executionReport",
            "E": int(now.timestamp() * 1000),
            "s": "BTCUSDT",
            "c": "ctp-phase266",
            "S": "BUY",
            "o": "MARKET",
            "x": "TRADE",
            "X": "PARTIALLY_FILLED",
            "i": 42,
            "l": "0.01",
            "z": "0.01",
            "L": "100.01",
            "n": "0.00001",
            "N": "BTC",
            "t": "phase266-trade-1",
        },
        observed_at=now,
    )
    rows = load_collection(collection, telemetry_key=KEY, now=now + timedelta(seconds=5))
    checkpoint = rows[-1]["record_sha256"]
    saved = write_runtime_state(
        state_path,
        adapter,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        telemetry_key=KEY,
        collection_last_record_sha256=checkpoint,
        now=now + timedelta(seconds=1),
    )

    restored_adapter = ProtectedCampaignRuntimeAdapter(collection=collection, telemetry_key=KEY)
    restored = restore_runtime_state(
        state_path,
        restored_adapter,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        telemetry_key=KEY,
        current_collection_last_record_sha256=checkpoint,
    )

    assert restored is not None
    assert restored["collection_last_record_sha256"] == checkpoint
    assert len(restored_adapter.paper_broker.fills) == 1
    assert restored_adapter.paper_broker.positions["BTCUSDT"].closed is False
    assert "phase266-trade-1" in restored_adapter.private_projector.seen_trades
    assert saved["live_enabled"] is False
    assert saved["production_ready"] is False


def test_runtime_state_tamper_and_wrong_checkpoint_fail_closed(tmp_path: Path) -> None:
    adapter, collection, state_path = _adapter(tmp_path)
    rows = load_collection(collection, telemetry_key=KEY)
    checkpoint = rows[-1]["record_sha256"]
    write_runtime_state(
        state_path,
        adapter,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        telemetry_key=KEY,
        collection_last_record_sha256=checkpoint,
    )

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    payload["paper"]["fee_bps"] = "0"
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="HMAC verification failed"):
        restore_runtime_state(
            state_path,
            ProtectedCampaignRuntimeAdapter(collection=collection, telemetry_key=KEY),
            candidate_sha=CANDIDATE,
            environment_hash=ENV_HASH,
            topology_hash=TOPOLOGY_HASH,
            telemetry_key=KEY,
            current_collection_last_record_sha256=checkpoint,
        )

    write_runtime_state(
        state_path,
        adapter,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        telemetry_key=KEY,
        collection_last_record_sha256=checkpoint,
    )
    with pytest.raises(ValueError, match="checkpoint mismatch"):
        restore_runtime_state(
            state_path,
            ProtectedCampaignRuntimeAdapter(collection=collection, telemetry_key=KEY),
            candidate_sha=CANDIDATE,
            environment_hash=ENV_HASH,
            topology_hash=TOPOLOGY_HASH,
            telemetry_key=KEY,
            current_collection_last_record_sha256="d" * 64,
        )


def test_runtime_state_never_persists_hmac_secret(tmp_path: Path) -> None:
    adapter, collection, state_path = _adapter(tmp_path)
    checkpoint = load_collection(collection, telemetry_key=KEY)[-1]["record_sha256"]
    write_runtime_state(
        state_path,
        adapter,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        telemetry_key=KEY,
        collection_last_record_sha256=checkpoint,
    )
    text = state_path.read_text(encoding="utf-8")
    assert KEY not in text
    assert "api_secret" not in text.lower()
    assert "api_key" not in text.lower()


def test_normalize_binance_klines_keeps_only_closed_history() -> None:
    now = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    start = now - timedelta(minutes=51)
    raw = []
    for index in range(51):
        opened = start + timedelta(minutes=index)
        closed = opened + timedelta(minutes=1) - timedelta(milliseconds=1)
        raw.append(
            [
                int(opened.timestamp() * 1000),
                "100",
                "101",
                "99",
                "100.5",
                "10",
                int(closed.timestamp() * 1000),
            ]
        )
    future_open = now
    raw.append(
        [
            int(future_open.timestamp() * 1000),
            "100",
            "101",
            "99",
            "100.5",
            "10",
            int((future_open + timedelta(minutes=1)).timestamp() * 1000),
        ]
    )
    candles = normalize_binance_klines(raw, now=now)
    assert len(candles) == 51
    assert all(row["closed"] is True for row in candles)
    assert candles[-1]["close_time"] <= now


def test_buy_signal_is_reanchored_to_real_snapshot_and_non_buy_never_opens() -> None:
    decision = SimpleNamespace(
        signal=Signal.BUY,
        entry=Decimal("100"),
        stop_loss=Decimal("98"),
        take_profits=(Decimal("102"), Decimal("104"), Decimal("106")),
    )
    intent = derive_long_intent(decision, _snapshot(), paper_notional=Decimal("10"))
    assert intent is not None
    ask = Decimal("100.01")
    assert intent.stop_loss == ask - Decimal("2")
    assert intent.take_profits == (
        ask + Decimal("2"),
        ask + Decimal("4"),
        ask + Decimal("6"),
    )
    assert intent.qty == Decimal("10") / ask

    hold = SimpleNamespace(
        signal=Signal.HOLD,
        entry=None,
        stop_loss=None,
        take_profits=(),
    )
    assert derive_long_intent(hold, _snapshot(), paper_notional=Decimal("10")) is None


def test_phase266_is_pinned_to_spot_testnet_websocket_and_has_no_order_surface() -> None:
    assert TESTNET_WS_API == "wss://ws-api.testnet.binance.vision/ws-api/v3"
    source = Path("scripts/external/phase266_campaign_runtime.py").read_text(encoding="utf-8")
    assert ".submit_order(" not in source
    assert ".cancel_order(" not in source
    assert "order.place" not in source
    assert "order.cancel" not in source
