from datetime import datetime, timedelta, timezone

import pytest

from app.data.envelope import MarketDataEnvelope, SequenceGuard


def test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency():
    exchange_time = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
    received_at = exchange_time + timedelta(milliseconds=125)
    envelope = MarketDataEnvelope(
        source="BINANCE_PUBLIC_WS",
        symbol="BTCUSDT",
        timeframe="1m",
        exchange_time=exchange_time,
        received_at=received_at,
        payload={"p": "64000"},
        sequence=42,
    )
    assert envelope.timestamp == exchange_time
    assert envelope.source == "BINANCE_PUBLIC_WS"
    assert envelope.symbol == "BTCUSDT"
    assert envelope.timeframe == "1m"
    assert envelope.exchange_time == exchange_time
    assert envelope.received_at == received_at
    assert envelope.latency_ms == pytest.approx(125.0)


def test_market_data_envelope_rejects_future_receive_order_and_naive_timestamps():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="received_at cannot precede"):
        MarketDataEnvelope("x", "BTCUSDT", "1m", now, now - timedelta(milliseconds=1), {})
    with pytest.raises(ValueError, match="timezone-aware"):
        MarketDataEnvelope("x", "BTCUSDT", "1m", datetime.now(), now, {})


def test_sequence_guard_rejects_duplicate_and_out_of_order_market_events():
    guard = SequenceGuard()
    guard.observe("btcusdt@depth", 100)
    guard.observe("btcusdt@depth", 101)
    assert guard.last("btcusdt@depth") == 101
    with pytest.raises(ValueError, match="duplicate"):
        guard.observe("btcusdt@depth", 101)
    with pytest.raises(ValueError, match="out-of-order"):
        guard.observe("btcusdt@depth", 99)
