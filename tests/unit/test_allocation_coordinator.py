from __future__ import annotations

from decimal import Decimal

from app.data.coordinator import MarketDataCoordinator, MarketSubscription
from app.risk.allocation import AllocationCandidate, AllocationState, CapitalAllocator


def _candidate(symbol: str, requested: str = "10000", edge: str = "20", stop: str = "0.02", **overrides):
    values = dict(
        symbol=symbol,
        requested_notional=Decimal(requested),
        expected_edge_bps=Decimal(edge),
        stop_risk_fraction=Decimal(stop),
        volatility_fraction=Decimal("0.02"),
        liquidity_score=Decimal("1"),
        correlation_penalty=Decimal("0"),
        strategy_health=Decimal("1"),
        drawdown_multiplier=Decimal("1"),
        regime_multiplier=Decimal("1"),
        quote_asset_multiplier=Decimal("1"),
    )
    values.update(overrides)
    return AllocationCandidate(**values)


def _state(**overrides):
    values = dict(
        account_equity=Decimal("100000"),
        free_cash=Decimal("80000"),
        portfolio_heat_fraction=Decimal("0.01"),
        max_portfolio_heat_fraction=Decimal("0.05"),
        risk_budget_remaining=Decimal("4000"),
        open_order_reserved=Decimal("5000"),
        reserve_fraction=Decimal("0.15"),
        cost_buffer_fraction=Decimal("0.005"),
        max_cycle_allocation_fraction=Decimal("0.20"),
        max_single_candidate_fraction=Decimal("0.10"),
    )
    values.update(overrides)
    return AllocationState(**values)


def test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers():
    decisions = CapitalAllocator.allocate_cycle(_state(), [_candidate("BTCUSDT", requested="50000"), _candidate("ETHUSDT", requested="50000")])
    allocated = sum(item.allocated_notional for item in decisions)
    assert allocated <= Decimal("20000")
    assert all(item.allocated_notional <= Decimal("10000") for item in decisions)


def test_capital_allocator_revalidates_remaining_risk_after_each_candidate():
    state = _state(risk_budget_remaining=Decimal("300"), max_portfolio_heat_fraction=Decimal("0.50"))
    decisions = CapitalAllocator.allocate_cycle(state, [_candidate("A", stop="0.02"), _candidate("B", stop="0.02")])
    assert decisions[0].allocated_notional == Decimal("10000")
    assert decisions[1].allocated_notional == Decimal("5000")
    assert sum(item.expected_stop_loss for item in decisions) == Decimal("300")


def test_capital_allocator_penalizes_correlation_and_unhealthy_strategy():
    healthy = _candidate("HEALTHY", correlation_penalty=Decimal("0.1"))
    unhealthy = _candidate("UNHEALTHY", strategy_health=Decimal("0.2"), correlation_penalty=Decimal("0.5"))
    decisions = CapitalAllocator.allocate_cycle(_state(), [unhealthy, healthy])
    assert decisions[0].symbol == "HEALTHY"
    assert decisions[0].score > decisions[1].score


def test_market_data_coordinator_shards_and_reconnects_deterministically():
    coordinator = MarketDataCoordinator(max_streams_per_connection=2)
    subs = [
        MarketSubscription("BTCUSDT", "trade"),
        MarketSubscription("ETHUSDT", "trade"),
        MarketSubscription("BTCUSDT", "kline", "1m"),
        MarketSubscription("ETHUSDT", "trade"),
    ]
    registry = coordinator.build_registry(subs)
    assert list(registry) == ["market-1", "market-2"]
    assert sum(len(items) for items in registry.values()) == 3
    assert coordinator.resubscribe_plan("market-1") == tuple(sorted(coordinator.resubscribe_plan("market-1")))


def test_market_data_coordinator_tracks_symbol_freshness_without_global_halt():
    coordinator = MarketDataCoordinator()
    coordinator.mark_symbol_fresh("BTCUSDT", 100)
    coordinator.mark_symbol_fresh("ETHUSDT", 108)
    assert coordinator.stale_symbols(now=110, max_age_seconds=5) == {"BTCUSDT"}
    assert coordinator.stale_risk_scope(False, True) == "BLOCK_SYMBOL"
    assert coordinator.stale_risk_scope(True, False) == "GLOBAL_RESTRICT"


def test_market_data_coordinator_preserves_high_priority_under_backpressure():
    coordinator = MarketDataCoordinator(queue_size=2)
    assert coordinator.enqueue("scanner_low", "low-1")
    assert coordinator.enqueue("scanner_low", "low-2")
    assert coordinator.enqueue("private_order_fill", "critical")
    payloads = {coordinator.queue.get().payload, coordinator.queue.get().payload}
    assert "critical" in payloads
    assert coordinator.queue.dropped == 1


def test_market_data_coordinator_runtime_rate_budget_and_jittered_reconciliation():
    coordinator = MarketDataCoordinator()
    coordinator.configure_runtime_budget("REQUEST_WEIGHT", limit=10, interval_seconds=60, now=0)
    assert coordinator.allow_rest("REQUEST_WEIGHT", weight=8, priority="normal", now=1)
    assert not coordinator.allow_rest("REQUEST_WEIGHT", weight=2, priority="low", now=2)
    telemetry = coordinator.rate_telemetry("REQUEST_WEIGHT")
    assert telemetry["used"] == 8
    assert telemetry["remaining"] == 2
    assert coordinator.reconciliation_delay(10, 0.2, 0.5) == 11


def test_market_data_priority_tiers_follow_v51_ordering():
    coordinator = MarketDataCoordinator(queue_size=6)
    categories = [
        "scanner_low",
        "candidate_market",
        "active_position_market",
        "best_bid_ask",
        "protective_position",
        "private_order_fill",
    ]
    for category in categories:
        assert coordinator.enqueue(category, category)
    popped = [coordinator.queue.get().payload for _ in categories]
    assert popped == [
        "private_order_fill",
        "protective_position",
        "best_bid_ask",
        "active_position_market",
        "candidate_market",
        "scanner_low",
    ]


def test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe():
    from app.data.coordinator import MarketDataCoordinator
    import pytest

    assert MarketDataCoordinator.rest_reconciliation_due(None, now=100.0, interval_seconds=30.0)
    assert not MarketDataCoordinator.rest_reconciliation_due(90.0, now=100.0, interval_seconds=30.0)
    assert MarketDataCoordinator.rest_reconciliation_due(70.0, now=100.0, interval_seconds=30.0)
    with pytest.raises(ValueError, match="clock moved backwards"):
        MarketDataCoordinator.rest_reconciliation_due(101.0, now=100.0, interval_seconds=30.0)
