from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.backtest.dataset import reproducibility_manifest
from app.backtest.engine import BacktestResult, Trade
from app.release.campaign_collector import (
    PUBLIC_BINANCE_ORIGIN,
    collection_path,
    derive_collection_metrics,
    initialize_collection,
    load_collection,
)
from app.release.campaign_runtime_adapter import LongIntent, ProtectedCampaignRuntimeAdapter

CANDIDATE = "a" * 40
ENV_HASH = "b" * 64
TOPOLOGY_HASH = "c" * 64
KEY = "phase265-runtime-attestation-key-material-0001"


def _adapter(tmp_path: Path) -> tuple[ProtectedCampaignRuntimeAdapter, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    state = (tmp_path / "state").resolve()
    path = collection_path(state, repository_root=repo, candidate_sha=CANDIDATE)
    initialize_collection(
        path,
        repository_root=repo,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
    )
    return ProtectedCampaignRuntimeAdapter(collection=path, telemetry_key=KEY), path


def _execution(*, trade_id: str, event_time_ms: int, cumulative: str, status: str = "PARTIALLY_FILLED") -> dict:
    return {
        "e": "executionReport",
        "E": event_time_ms,
        "s": "BTCUSDT",
        "c": "ctp-runtime-1",
        "S": "BUY",
        "o": "MARKET",
        "x": "TRADE",
        "X": status,
        "i": 42,
        "l": "0.01",
        "z": cumulative,
        "L": "50000",
        "n": "0.00001",
        "N": "BTC",
        "t": trade_id,
    }


def _snapshot(observation_id: str, bid: str, ask: str) -> dict:
    return {
        "observation_id": observation_id,
        "symbol": "BTCUSDT",
        "bid_price": bid,
        "ask_price": ask,
        "market_data_origin": "REAL",
        "public_origin": PUBLIC_BINANCE_ORIGIN,
    }


def test_private_projector_outcomes_drive_attested_duplicate_and_out_of_order_events(tmp_path: Path) -> None:
    adapter, path = _adapter(tmp_path)
    now = datetime.now(timezone.utc)
    base_ms = int(now.timestamp() * 1000)

    first = adapter.record_private_message(
        _execution(trade_id="100", event_time_ms=base_ms, cumulative="0.01"), observed_at=now
    )
    duplicate = adapter.record_private_message(
        _execution(trade_id="100", event_time_ms=base_ms + 1, cumulative="0.01"),
        observed_at=now + timedelta(seconds=1),
    )
    stale = adapter.record_private_message(
        _execution(trade_id="101", event_time_ms=base_ms - 1, cumulative="0.005"),
        observed_at=now + timedelta(seconds=2),
    )

    assert first.classification == "KNOWN_PLATFORM_ACTIVITY"
    assert duplicate.classification == "DUPLICATE_FILL"
    assert stale.classification == "STALE_ORDER_EVENT"
    rows = load_collection(path, telemetry_key=KEY, now=now + timedelta(seconds=5))
    private = derive_collection_metrics(rows)["private-stream"]
    assert private["duplicate_event_idempotency_passed"] is True
    assert private["out_of_order_protection_passed"] is True
    assert private["secrets_redacted"] is True
    assert private["observed_events"] == 3


def test_private_reconciliation_is_derived_from_projected_balance_state(tmp_path: Path) -> None:
    adapter, path = _adapter(tmp_path)
    now = datetime.now(timezone.utc)
    adapter.record_private_message(
        {
            "e": "outboundAccountPosition",
            "E": int(now.timestamp() * 1000),
            "B": [{"a": "USDT", "f": "100.0", "l": "2.0"}],
        },
        observed_at=now,
    )
    adapter.record_private_rest_reconciliation(
        {"USDT": (Decimal("100.0"), Decimal("2.0"))}, observed_at=now + timedelta(seconds=1)
    )
    with pytest.raises(RuntimeError, match="does not match"):
        adapter.record_private_rest_reconciliation(
            {"USDT": (Decimal("99.0"), Decimal("2.0"))}, observed_at=now + timedelta(seconds=2)
        )
    rows = load_collection(path, telemetry_key=KEY, now=now + timedelta(seconds=5))
    assert derive_collection_metrics(rows)["private-stream"]["rest_reconciliation_passed"] is True


def test_paper_samples_are_derived_from_paperbroker_fills(tmp_path: Path) -> None:
    adapter, path = _adapter(tmp_path)
    now = datetime.now(timezone.utc)
    decision = adapter.record_paper_quote(
        _snapshot("quote-1", "100.00", "100.01"),
        market_regime="trend",
        observed_at=now,
        long_intent=LongIntent(
            qty=Decimal("0.1"),
            stop_loss=Decimal("99.80"),
            take_profits=(Decimal("100.02"), Decimal("100.04"), Decimal("100.06")),
        ),
    )
    exit_decision = adapter.record_paper_quote(
        _snapshot("quote-2", "100.03", "100.04"),
        market_regime="trend",
        observed_at=now + timedelta(seconds=1),
    )

    assert decision == "LONG"
    assert exit_decision == "EXIT"
    assert len(adapter.paper_broker.fills) >= 2
    rows = load_collection(path, telemetry_key=KEY, now=now + timedelta(seconds=5))
    paper = derive_collection_metrics(rows)["paper"]
    assert paper["long_examples"] == 1
    assert paper["exit_examples"] == 1
    assert paper["real_market_data"] is True


def test_live_shadow_has_no_submit_surface_and_kill_switch_is_behavioral(tmp_path: Path) -> None:
    adapter, path = _adapter(tmp_path)
    now = datetime.now(timezone.utc)
    snapshot = _snapshot("shadow-1", "100.00", "100.01")

    assert not hasattr(adapter, "submit_order")
    adapter.record_live_shadow_observation(snapshot, strategy_decision="HOLD", observed_at=now)
    adapter.test_live_shadow_kill_switch(snapshot, observed_at=now + timedelta(seconds=1))
    with pytest.raises(RuntimeError, match="kill-switch"):
        adapter.record_live_shadow_observation(
            _snapshot("shadow-2", "100.01", "100.02"),
            strategy_decision="HOLD",
            observed_at=now + timedelta(seconds=2),
        )

    rows = load_collection(path, telemetry_key=KEY, now=now + timedelta(seconds=5))
    shadow = derive_collection_metrics(rows)["live-shadow"]
    assert shadow["observations"] == 1
    assert shadow["real_orders_submitted"] == 0
    assert shadow["exchange_submit_calls"] == 0
    assert shadow["kill_switch_tested"] is True


def test_profitability_samples_require_hash_verified_exact_sha_oos_backtest(tmp_path: Path) -> None:
    adapter, path = _adapter(tmp_path)
    now = datetime.now(timezone.utc)
    rows = [
        {"open_time": (now - timedelta(days=2)).isoformat(), "open": "100", "high": "101", "low": "99", "close": "100"},
        {"open_time": (now - timedelta(days=1)).isoformat(), "open": "100", "high": "102", "low": "100", "close": "101"},
    ]
    manifest = reproducibility_manifest(
        exchange="BINANCE_SPOT",
        symbols=("BTCUSDT",),
        timeframe="1d",
        start=rows[0]["open_time"],
        end=rows[-1]["open_time"],
        source="binance-spot-point-in-time-archive",
        downloaded_at=now.isoformat(),
        rows=rows,
        missing_candle_count=0,
        preprocessing_version="1",
        strategy_version="1",
        config_hash="d" * 64,
        code_git_sha=CANDIDATE,
        random_seed=7,
        execution_model_version="1",
    )
    trade = Trade(
        entry_time=now - timedelta(days=1),
        exit_time=now,
        side="LONG",
        qty=Decimal("1"),
        entry=Decimal("100"),
        exit=Decimal("102"),
        fee=Decimal("0.10"),
        slippage=Decimal("0.05"),
        pnl=Decimal("1.90"),
        exit_reason="TP",
        symbol="BTCUSDT",
    )
    result = BacktestResult(
        trades=[trade], total_return=0.019, max_drawdown=0.0, win_rate=1.0, profit_factor=float("inf"), expectancy=1.9
    )
    emitted = adapter.record_profitability_backtest(
        manifest=manifest,
        rows=rows,
        result=result,
        oos_start=now - timedelta(days=2),
        observed_at=now,
    )
    assert emitted == 1
    loaded = load_collection(path, telemetry_key=KEY, now=now + timedelta(seconds=5))
    profitability = derive_collection_metrics(loaded)["profitability"]
    assert profitability["effective_sample_size"] == 1.0
    assert profitability["real_point_in_time_data"] is True
    assert profitability["independent_oos"] is True

    tampered = [dict(row) for row in rows]
    tampered[0]["close"] = "999"
    with pytest.raises(ValueError, match="manifest hash"):
        adapter.record_profitability_backtest(
            manifest=manifest,
            rows=tampered,
            result=result,
            oos_start=now - timedelta(days=2),
            observed_at=now,
        )
