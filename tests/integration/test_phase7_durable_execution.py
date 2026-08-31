from datetime import datetime, timezone, timedelta
from dataclasses import replace
from decimal import Decimal

import pytest
from sqlalchemy.pool import StaticPool

from app.core.enums import OrderState, TradingMode
from app.database.models import ExchangeAccount
from app.database.session import init_db, make_engine, session_factory
from app.exchange.mock import MockExchange
from app.exchange.models import OrderIntent
from app.execution.persistent import (
    DatabaseExecutionFence,
    DatabaseLeaderRegistry,
    PersistentIntentLedger,
)
from app.execution.service import ExecutionService
from app.risk.state import RiskMachine


def db_setup(account='a1'):
    engine = make_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    init_db(engine)
    sf = session_factory(engine)
    with sf() as s:
        s.add(ExchangeAccount(
            id=account, exchange='MOCK', account_fingerprint='phase7',
            market_type='SPOT', capabilities={}, permission_snapshot={}, status='ACTIVE',
        ))
        s.commit()
    return engine, sf


def intent(intent_id='durable-1'):
    return OrderIntent(intent_id, 'a1', 'BTCUSDT', 'BUY', 'LIMIT', Decimal('0.01'), Decimal('60000'))


class CountingExchange(MockExchange):
    def __init__(self):
        super().__init__()
        self.submit_calls = 0

    def submit_order(self, order_intent):
        self.submit_calls += 1
        return super().submit_order(order_intent)


def test_durable_intent_idempotency_survives_service_restart_without_duplicate_submit():
    engine, sf = db_setup()
    exchange = CountingExchange()
    ledger = PersistentIntentLedger(sf)
    first_service = ExecutionService(exchange, RiskMachine(), persistent_intents=ledger)
    first = first_service.submit(intent(), Decimal('60000'), Decimal('100'))
    assert first.state == OrderState.ACKNOWLEDGED
    assert exchange.submit_calls == 1

    restarted_service = ExecutionService(exchange, RiskMachine(), persistent_intents=PersistentIntentLedger(sf))
    second = restarted_service.submit(intent(), Decimal('60000'), Decimal('100'))
    assert second.exchange_order_id == first.exchange_order_id
    assert exchange.submit_calls == 1
    engine.dispose()


def test_ambiguous_durable_intent_is_not_blindly_retried_after_restart():
    engine, sf = db_setup()
    exchange = CountingExchange()
    exchange.fail_mode = 'ambiguous'
    ledger = PersistentIntentLedger(sf)
    first = ExecutionService(exchange, RiskMachine(), persistent_intents=ledger).submit(
        intent('ambiguous-durable'), Decimal('60000'), Decimal('100')
    )
    assert first.state == OrderState.UNKNOWN
    assert exchange.submit_calls == 1

    exchange.fail_mode = None
    restarted = ExecutionService(exchange, RiskMachine(), persistent_intents=PersistentIntentLedger(sf))
    second = restarted.submit(intent('ambiguous-durable'), Decimal('60000'), Decimal('100'))
    assert second.state == OrderState.UNKNOWN
    assert exchange.submit_calls == 1
    engine.dispose()


def test_durable_submitted_intent_reconciles_by_client_order_id_before_any_resubmit():
    engine, sf = db_setup()
    exchange = CountingExchange()
    ledger = PersistentIntentLedger(sf)
    normalized = intent('precommitted')
    record, created = ledger.reserve_before_side_effect(normalized)
    assert created and record.state == OrderState.SUBMITTED

    # Model the exchange having accepted the request immediately before a process crash.
    remote = exchange.submit_order(replace(normalized, client_order_id=record.client_order_id))
    assert exchange.submit_calls == 1

    restarted = ExecutionService(exchange, RiskMachine(), persistent_intents=PersistentIntentLedger(sf))
    recovered = restarted.submit(normalized, Decimal('60000'), Decimal('100'))
    assert recovered.exchange_order_id == remote.exchange_order_id
    assert recovered.state == OrderState.ACKNOWLEDGED
    assert exchange.submit_calls == 1
    engine.dispose()


def test_database_execution_fence_rejects_expired_old_leader_after_takeover():
    engine, sf = db_setup()
    leaders = DatabaseLeaderRegistry(sf)
    now = datetime.now(timezone.utc)
    old = leaders.acquire('a1', 'node-old', ttl=1, now=now)
    new = leaders.acquire('a1', 'node-new', ttl=10, now=now + timedelta(seconds=2))
    assert new.fencing_token > old.fencing_token
    fence = DatabaseExecutionFence(leaders)
    with pytest.raises(PermissionError, match='stale or expired'):
        fence.require_current('a1', 'node-old', old.fencing_token, now=now + timedelta(seconds=2))
    fence.require_current('a1', 'node-new', new.fencing_token, now=now + timedelta(seconds=2))
    engine.dispose()


def test_live_submit_revalidates_fencing_immediately_at_exchange_side_effect_boundary():
    class TwoPhaseLeader:
        def __init__(self):
            self.calls = 0
        def validate(self, account_id, instance_id, token, now=None):
            self.calls += 1
            return self.calls == 1

    class Reservation:
        items = {'fenced': object()}
        def validate_live_balance(self, intent_id, balances):
            return True

    leader = TwoPhaseLeader()
    exchange = CountingExchange()
    service = ExecutionService(
        exchange,
        RiskMachine(),
        leader_registry=leader,
        reservations=Reservation(),
        side_effect_fence=DatabaseExecutionFence(leader),
    )
    live_intent = intent('fenced')
    with pytest.raises(PermissionError, match='side-effect boundary'):
        service.submit(live_intent, Decimal('60000'), Decimal('100'), TradingMode.LIVE, 'node-a', 7)
    assert exchange.submit_calls == 0


def test_persistent_leader_heartbeat_extends_same_token_and_expired_lease_cannot_renew():
    engine, sf = db_setup()
    leaders = DatabaseLeaderRegistry(sf)
    now = datetime.now(timezone.utc)
    lease = leaders.acquire('a1', 'node-live', ttl=2, now=now)
    renewed = leaders.heartbeat('a1', 'node-live', lease.fencing_token, ttl=5, now=now + timedelta(seconds=1))
    assert renewed.fencing_token == lease.fencing_token
    assert leaders.validate('a1', 'node-live', lease.fencing_token, now=now + timedelta(seconds=4))
    with pytest.raises(PermissionError, match='stale or expired'):
        leaders.heartbeat('a1', 'node-live', lease.fencing_token, ttl=5, now=now + timedelta(seconds=7))
    engine.dispose()


def test_durable_intent_id_collision_with_different_symbol_fails_closed_without_submit():
    engine, sf = db_setup()
    exchange = CountingExchange()
    ledger = PersistentIntentLedger(sf)
    service = ExecutionService(exchange, RiskMachine(), persistent_intents=ledger)
    service.submit(intent('collision'), Decimal('60000'), Decimal('100'))
    assert exchange.submit_calls == 1
    conflicting = OrderIntent('collision', 'a1', 'ETHUSDT', 'BUY', 'LIMIT', Decimal('0.01'), Decimal('3000'))
    restarted = ExecutionService(exchange, RiskMachine(), persistent_intents=PersistentIntentLedger(sf))
    with pytest.raises(ValueError, match='intent_id collision'):
        restarted.submit(conflicting, Decimal('3000'), Decimal('100'))
    assert exchange.submit_calls == 1
    engine.dispose()


def test_execution_lock_failure_prevents_exchange_side_effect():
    class BrokenLockContext:
        def __enter__(self):
            raise PermissionError('distributed lock unavailable')
        def __exit__(self, *_):
            return False
    class BrokenLocks:
        def hold(self, account_id):
            return BrokenLockContext()
    exchange = CountingExchange()
    service = ExecutionService(exchange, RiskMachine(), account_locks=BrokenLocks())
    with pytest.raises(PermissionError, match='lock unavailable'):
        service.submit(intent('lock-fail'), Decimal('60000'), Decimal('100'))
    assert exchange.submit_calls == 0
