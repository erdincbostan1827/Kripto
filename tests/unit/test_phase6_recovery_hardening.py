from decimal import Decimal
import pytest

from app.core.enums import RiskState
from app.exchange.mock import MockExchange
from app.execution.persistent import FencingTokenGuard
from app.execution.reconciliation import AccountSnapshot, reconcile, validate_protective_coverage
from app.execution.recovery import PrivateStreamRecoveryCoordinator, RestartRecoveryCoordinator
from app.risk.state import RecoveryChecks, RecoveryHysteresisGate, RiskMachine


def green():
    return RecoveryChecks(
        data_healthy=True, exchange_healthy=True, private_stream_healthy=True,
        reconciliation_ok=True, no_orphan_orders=True, protective_orders_ok=True,
        risk_limits_ok=True, clock_ok=True, strategy_health_ok=True,
    )


def test_recovery_hysteresis_rejects_single_transient_green_sample():
    gate = RecoveryHysteresisGate(min_healthy_seconds=10, min_consecutive_successes=3)
    assert not gate.observe(green(), now=100)
    assert not gate.observe(green(), now=105)
    assert gate.observe(green(), now=110)


def test_recovery_hysteresis_failure_resets_dwell_and_count():
    gate = RecoveryHysteresisGate(min_healthy_seconds=5, min_consecutive_successes=2)
    assert not gate.observe(green(), now=10)
    bad = RecoveryChecks(**{**green().__dict__, 'exchange_healthy': False})
    assert not gate.observe(bad, now=14)
    assert not gate.observe(green(), now=20)
    assert gate.observe(green(), now=25)


def test_recovery_hysteresis_clock_regression_fails_closed():
    gate = RecoveryHysteresisGate(min_healthy_seconds=0, min_consecutive_successes=1)
    assert gate.observe(green(), now=100)
    with pytest.raises(ValueError, match='clock moved backwards'):
        gate.observe(green(), now=99)


def test_reconciliation_detects_local_order_missing_on_exchange():
    local = AccountSnapshot({}, {}, {'local-open'})
    remote = AccountSnapshot({}, {}, set())
    result = reconcile(local, remote)
    assert 'MISSING_EXCHANGE_ORDER:local-open' in result.drift
    assert result.risk_state == RiskState.MANUAL_REVIEW_REQUIRED


def test_restart_recovery_missing_exchange_order_blocks_no_orphan_gate():
    risk = RiskMachine(state=RiskState.STARTING)
    coordinator = RestartRecoveryCoordinator(risk)
    evidence = coordinator.evaluate(
        local=AccountSnapshot({}, {}, {'local-open'}),
        exchange=AccountSnapshot({}, {}, set()),
        checks=green(), human_approved=True,
    )
    assert not evidence.checks.no_orphan_orders
    assert risk.state == RiskState.MANUAL_REVIEW_REQUIRED


def test_protective_coverage_fails_for_any_exposed_symbol_without_guard():
    result = validate_protective_coverage({'BTCUSDT': Decimal('0.2'), 'ETHUSDT': Decimal('-1'), 'SOLUSDT': Decimal('0')}, {'BTCUSDT'})
    assert not result.ok
    assert result.uncovered_symbols == ('ETHUSDT',)


def test_private_stream_auth_expiry_requires_fresh_auth_before_healthy_reconnect():
    exchange = MockExchange()
    local = AccountSnapshot(exchange.get_balance(), {}, set())
    risk = RiskMachine()
    c = PrivateStreamRecoveryCoordinator(risk, lambda: local)
    c.on_auth_expired()
    assert not risk.allow_new_risk()
    ev = c.on_reconnect(exchange, stream_healthy=True, auth_refreshed=False)
    assert not ev.stream_healthy
    assert ev.requires_human_review
    assert risk.state == RiskState.RECOVERY_PENDING


def test_private_stream_auth_refresh_still_requires_recovery_approval():
    exchange = MockExchange()
    local = AccountSnapshot(exchange.get_balance(), {}, set())
    risk = RiskMachine()
    c = PrivateStreamRecoveryCoordinator(risk, lambda: local)
    c.on_auth_expired()
    ev = c.on_reconnect(exchange, stream_healthy=True, auth_refreshed=True)
    assert ev.stream_healthy
    assert not ev.requires_human_review
    assert risk.state == RiskState.RECOVERY_PENDING
    assert not risk.allow_new_risk()


def test_fencing_guard_never_accepts_older_token_after_newer_seen():
    guard = FencingTokenGuard()
    assert guard.accept('a1', 10)
    assert guard.accept('a1', 11)
    assert not guard.accept('a1', 10)
    with pytest.raises(PermissionError, match='stale fencing token'):
        guard.require('a1', 9)


def test_fencing_guard_is_account_scoped():
    guard = FencingTokenGuard()
    assert guard.accept('a1', 8)
    assert guard.accept('a2', 1)
    assert not guard.accept('a1', 7)
