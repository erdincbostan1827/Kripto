from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.data.coordinator import MarketDataCoordinator, MarketSubscription
from app.risk.allocation import (
    AllocationCandidate,
    AllocationState,
    ConcurrentAllocationCoordinator,
)
from app.universe.manager import SymbolEligibility, SymbolMetadataHistory
from app.universe.scanner import DynamicUniverseScanner


def _t(day: int) -> datetime:
    return datetime(2026, 1, day, tzinfo=timezone.utc)


def _eligible(symbol: str, **overrides):
    values = dict(
        symbol=symbol,
        listing_age_days=100,
        quote_volume_24h=Decimal('10000000'),
        spread_bps=Decimal('2'),
        depth_notional=Decimal('500000'),
        history_bars=500,
        data_fresh=True,
        active=True,
        suspended=False,
    )
    values.update(overrides)
    return SymbolEligibility(**values)


def _candidate(symbol: str):
    return AllocationCandidate(
        symbol=symbol,
        requested_notional=Decimal('10000'),
        expected_edge_bps=Decimal('20'),
        stop_risk_fraction=Decimal('0.02'),
        volatility_fraction=Decimal('0.02'),
        liquidity_score=Decimal('1'),
        correlation_penalty=Decimal('0'),
        strategy_health=Decimal('1'),
        drawdown_multiplier=Decimal('1'),
        regime_multiplier=Decimal('1'),
        quote_asset_multiplier=Decimal('1'),
    )


def _state():
    return AllocationState(
        account_equity=Decimal('100000'),
        free_cash=Decimal('20000'),
        portfolio_heat_fraction=Decimal('0'),
        max_portfolio_heat_fraction=Decimal('0.05'),
        risk_budget_remaining=Decimal('400'),
        open_order_reserved=Decimal('0'),
        reserve_fraction=Decimal('0'),
        cost_buffer_fraction=Decimal('0'),
        max_cycle_allocation_fraction=Decimal('0.20'),
        max_single_candidate_fraction=Decimal('0.10'),
    )


def test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe():
    history = SymbolMetadataHistory()
    v1 = history.record(
        'BTCUSDT',
        effective_at=_t(1),
        metadata_source='exchangeInfo',
        filters={'tickSize': '0.10', 'stepSize': '0.001'},
        price_precision=1,
        quantity_precision=3,
    )
    v2 = history.record(
        'BTCUSDT',
        effective_at=_t(10),
        metadata_source='exchangeInfo',
        filters={'tickSize': '0.01', 'stepSize': '0.0001'},
        price_precision=2,
        quantity_precision=4,
    )
    assert v1.version != v2.version
    assert history.version_at('BTCUSDT', _t(5)).version == v1.version
    assert history.version_at('BTCUSDT', _t(15)).version == v2.version
    assert history.changed_between('BTCUSDT', _t(5), _t(15))
    with pytest.raises(LookupError):
        history.version_at('BTCUSDT', datetime(2025, 12, 31, tzinfo=timezone.utc))


def test_symbol_metadata_version_is_stable_and_conflict_at_same_timestamp_fails_closed():
    history = SymbolMetadataHistory()
    first = history.record(
        'ETHUSDT', effective_at=_t(1), metadata_source='exchangeInfo',
        filters={'stepSize': '0.001', 'tickSize': '0.01'}, price_precision=2, quantity_precision=3,
    )
    duplicate = history.record(
        'ETHUSDT', effective_at=_t(1), metadata_source='exchangeInfo',
        filters={'tickSize': '0.01', 'stepSize': '0.001'}, price_precision=2, quantity_precision=3,
    )
    assert duplicate.version == first.version
    with pytest.raises(ValueError, match='conflicting metadata'):
        history.record(
            'ETHUSDT', effective_at=_t(1), metadata_source='exchangeInfo',
            filters={'tickSize': '0.10', 'stepSize': '0.001'}, price_precision=1, quantity_precision=3,
        )


def test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max():
    scanner = DynamicUniverseScanner(configured_max_symbols=3)
    states = [_eligible(f'S{i}USDT') for i in range(5)] + [_eligible('BADUSDT', data_fresh=False)]
    symbols, telemetry = scanner.discover(states, snapshot_id='u-1', started_at=100.0, now=100.25)
    assert symbols == ['S0USDT', 'S1USDT', 'S2USDT']
    assert telemetry.universe_size == 6
    assert telemetry.eligible_size == 3
    assert telemetry.candidates_total == 3
    assert telemetry.snapshot_id == 'u-1'
    assert telemetry.cycle_duration_seconds == pytest.approx(0.25)
    assert scanner.healthy(now=101.0, max_cycle_age_seconds=2.0)
    assert not scanner.healthy(now=103.0, max_cycle_age_seconds=2.0)


def test_dynamic_universe_scanner_counts_bad_records_without_poisoning_entire_cycle():
    scanner = DynamicUniverseScanner(configured_max_symbols=10)
    symbols, telemetry = scanner.discover([_eligible('BTCUSDT'), object()], snapshot_id='u-2', started_at=10.0, now=11.0)
    assert symbols == ['BTCUSDT']
    assert telemetry.refresh_failures == 1
    assert scanner.refresh_failures == 1
    assert not scanner.healthy(now=11.0, max_cycle_age_seconds=10.0)
    with pytest.raises(ValueError, match='clock moved backwards'):
        scanner.discover([], snapshot_id='u-3', started_at=12.0, now=11.0)


def test_configured_max_universe_websocket_subscription_coverage_is_exact():
    coordinator = MarketDataCoordinator(max_streams_per_connection=2)
    symbols = {f'S{i}USDT' for i in range(5)}
    coordinator.build_registry([MarketSubscription(symbol, 'trade') for symbol in symbols])
    assert coordinator.validate_subscription_coverage(symbols)
    with pytest.raises(RuntimeError, match='incomplete market-data subscription coverage'):
        coordinator.validate_subscription_coverage(symbols | {'MISSINGUSDT'})


def test_concurrent_candidate_reconciliation_never_double_allocates_shared_cycle_budget():
    coordinator = ConcurrentAllocationCoordinator()
    state = _state()

    def worker(index: int):
        return coordinator.reconcile_and_allocate('cycle-1', state, [_candidate(f'S{index}USDT')])

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(worker, range(8)))
    allocated = sum((decision.allocated_notional for result in results for decision in result), Decimal('0'))
    risk = sum((decision.expected_stop_loss for result in results for decision in result), Decimal('0'))
    assert allocated <= Decimal('20000')
    assert risk <= Decimal('400')
    telemetry = coordinator.telemetry()
    assert telemetry['allocated_notional'] == allocated
    assert telemetry['allocated_risk'] == risk


def test_allocation_cycle_reset_does_not_leak_previous_cycle_budget():
    coordinator = ConcurrentAllocationCoordinator()
    state = _state()
    first = coordinator.reconcile_and_allocate('cycle-1', state, [_candidate('BTCUSDT')])
    second = coordinator.reconcile_and_allocate('cycle-2', state, [_candidate('ETHUSDT')])
    assert first[0].allocated_notional == Decimal('10000')
    assert second[0].allocated_notional == Decimal('10000')
    assert coordinator.telemetry()['cycle_id'] == 'cycle-2'


def test_dynamic_universe_policy_applies_allowlist_blocklist_and_quote_filter():
    scanner = DynamicUniverseScanner(configured_max_symbols=10)
    states = [_eligible('BTCUSDT'), _eligible('ETHUSDC'), _eligible('DOGEBTC'), _eligible('XRPUSDT')]
    symbols, telemetry = scanner.discover(
        states,
        snapshot_id='u-policy',
        started_at=1.0,
        now=2.0,
        allowlist={'BTCUSDT', 'ETHUSDC', 'DOGEBTC', 'XRPUSDT'},
        blocklist={'XRPUSDT'},
        approved_quotes=('USDT', 'USDC'),
    )
    assert symbols == ['BTCUSDT', 'ETHUSDC']
    assert telemetry.excluded_size == 2


def test_market_data_subscription_telemetry_is_bounded_and_matches_registry():
    coordinator = MarketDataCoordinator(max_streams_per_connection=2)
    symbols = [f'S{i}USDT' for i in range(5)]
    coordinator.build_registry([MarketSubscription(symbol, 'trade') for symbol in symbols])
    telemetry = coordinator.subscription_telemetry()
    assert telemetry == {'websocket_subscriptions': 5, 'websocket_shards': 3, 'unique_symbols': 5}
