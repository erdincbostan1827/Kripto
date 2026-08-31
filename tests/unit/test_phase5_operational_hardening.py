from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import threading
import time

import pytest

from app.core.enums import TradingMode
from app.data.coordinator import MarketDataCoordinator, MarketSubscription
from app.data.rate_limit import RateLimitBudget
from app.exchange.mock import MockExchange
from app.exchange.models import OrderIntent
from app.execution.isolation import AccountRiskLocks, SymbolRiskIsolation
from app.execution.reconciliation import AccountSnapshot
from app.execution.recovery import PrivateStreamRecoveryCoordinator
from app.execution.reservation import CapitalReservations
from app.execution.service import ExecutionService
from app.execution.leader import LeaderRegistry
from app.risk.state import RiskMachine


def _intent(intent_id='i1', symbol='BTCUSDT', account='a1'):
    return OrderIntent(intent_id, account, symbol, 'BUY', 'LIMIT', Decimal('0.01'), Decimal('60000') if symbol == 'BTCUSDT' else Decimal('3000'))


def test_account_level_risk_lock_serializes_same_account_critical_sections():
    locks = AccountRiskLocks()
    active = 0
    peak = 0
    guard = threading.Lock()

    def worker():
        nonlocal active, peak
        with locks.hold('account-1'):
            with guard:
                active += 1
                peak = max(peak, active)
            time.sleep(0.005)
            with guard:
                active -= 1

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: worker(), range(24)))
    assert peak == 1


def test_account_level_risk_lock_allows_independent_accounts():
    locks = AccountRiskLocks()
    entered = []
    barrier = threading.Barrier(2)

    def worker(account):
        with locks.hold(account):
            entered.append(account)
            barrier.wait(timeout=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, 'a1'), pool.submit(worker, 'a2')]
        for future in futures:
            future.result()
    assert set(entered) == {'a1', 'a2'}


def test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate():
    exchange = MockExchange()
    risk = RiskMachine()
    isolation = SymbolRiskIsolation()
    service = ExecutionService(exchange, risk, symbol_isolation=isolation)
    exchange.fail_mode = 'ambiguous'
    unknown = service.submit(_intent('bad', 'BTCUSDT'), Decimal('60000'), Decimal('100'))
    assert unknown.state.value == 'UNKNOWN'
    assert isolation.is_blocked('a1', 'BTCUSDT')
    assert risk.allow_new_risk()  # account is not globally halted by one isolated symbol
    exchange.fail_mode = None
    with pytest.raises(PermissionError, match='symbol isolated'):
        service.submit(_intent('retry', 'BTCUSDT'), Decimal('60000'), Decimal('100'))
    good = service.submit(_intent('good', 'ETHUSDT'), Decimal('3000'), Decimal('100'))
    assert good.exchange_order_id


def test_shared_balance_changed_between_ranking_and_live_submit_fails_closed():
    exchange = MockExchange()
    risk = RiskMachine()
    leader = LeaderRegistry()
    reservations = CapitalReservations()
    lease = leader.acquire('a1', 'node', ttl=100)
    reservations.reserve('i1', '90000', '100000', ttl=1000, asset='USDT', account_id='a1')
    exchange.balances['USDT'] = Decimal('50000')
    service = ExecutionService(exchange, risk, leader, reservations)
    with pytest.raises(PermissionError, match='shared balance changed'):
        service.submit(_intent(), Decimal('60000'), Decimal('100'), TradingMode.LIVE, 'node', lease.fencing_token)
    assert not exchange.orders
    assert not risk.allow_new_risk()


def test_reconnect_resubscribes_every_market_data_shard_without_loss():
    coordinator = MarketDataCoordinator(max_streams_per_connection=2)
    subs = [MarketSubscription(f'S{i}USDT', 'trade') for i in range(7)]
    registry = coordinator.build_registry(subs)
    plans = coordinator.reconnect_resubscribe_all()
    assert set(plans) == set(registry)
    assert {stream for shard in plans.values() for stream in shard} == {item.key for item in subs}
    assert all(coordinator.connection_generation[key] == 1 for key in registry)
    second = coordinator.reconnect_resubscribe_all()
    assert second == plans
    assert all(coordinator.connection_generation[key] == 2 for key in registry)


def test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed():
    budget = RateLimitBudget()
    budget.configure('PRIMARY', 2, 60, now=0)
    budget.configure('REST_FALLBACK', 1, 60, now=0)
    assert budget.allow_with_fallback('PRIMARY', 'REST_FALLBACK', now=1) == 'PRIMARY'
    assert budget.allow_with_fallback('PRIMARY', 'REST_FALLBACK', now=2) == 'PRIMARY'
    assert budget.allow_with_fallback('PRIMARY', 'REST_FALLBACK', now=3) == 'FALLBACK'
    assert budget.allow_with_fallback('PRIMARY', 'REST_FALLBACK', now=4) is None
    assert budget.remaining('PRIMARY') == 0
    assert budget.remaining('REST_FALLBACK') == 0


def test_rate_limit_clock_jump_fails_closed():
    budget = RateLimitBudget()
    budget.configure('PRIMARY', 10, 60, now=100)
    with pytest.raises(ValueError, match='clock moved backwards'):
        budget.allow('PRIMARY', now=99)


def test_private_stream_reconnect_performs_rest_reconciliation_before_recovery():
    exchange = MockExchange()
    local = AccountSnapshot(exchange.get_balance(), {}, set())
    risk = RiskMachine()
    coordinator = PrivateStreamRecoveryCoordinator(risk, lambda: local)
    coordinator.on_disconnect()
    assert not risk.allow_new_risk()
    evidence = coordinator.on_reconnect(exchange, stream_healthy=True)
    assert not evidence.reconciliation.drift
    assert not evidence.requires_human_review
    assert risk.state.value == 'RECOVERY_PENDING'
    assert not risk.allow_new_risk()


def test_private_stream_reconnect_drift_requires_manual_review():
    exchange = MockExchange()
    local = AccountSnapshot({'USDT': Decimal('99999')}, {}, set())
    risk = RiskMachine()
    coordinator = PrivateStreamRecoveryCoordinator(risk, lambda: local)
    coordinator.on_disconnect()
    evidence = coordinator.on_reconnect(exchange, stream_healthy=True)
    assert any(item.startswith('UNKNOWN_BALANCE_CHANGE:USDT') for item in evidence.reconciliation.drift)
    assert evidence.requires_human_review
    assert risk.state.value == 'MANUAL_REVIEW_REQUIRED'
