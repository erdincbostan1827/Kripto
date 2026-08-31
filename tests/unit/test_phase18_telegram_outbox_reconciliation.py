from decimal import Decimal

import pytest

from app.core.enums import RiskState
from app.database.idempotent_consumer import IdempotentConsumer, InMemoryReceiptStore
from app.execution.reconciliation import AccountSnapshot, CompositeReconciliationEvidence, reconcile_composite
from app.monitoring.telegram_security import TelegramCommandContext, TelegramCommandSecurity, TelegramSecurityError


def _telegram_security(*, enabled: bool = True, nonce="nonce-1"):
    return TelegramCommandSecurity(
        allowed_chat_ids={"100"},
        allowed_user_ids={"200", "201"},
        signing_key=b"0123456789abcdef0123456789abcdef",
        state_changing_commands_enabled=enabled,
        live_nonce_ttl_seconds=60,
        nonce_factory=lambda: nonce,
    )


def test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off():
    disabled = _telegram_security(enabled=False)
    good = TelegramCommandContext("100", "200", "/live", 1_000)
    with pytest.raises(TelegramSecurityError, match="STATE_CHANGING_COMMANDS_DISABLED"):
        disabled.authorize(good, state_changing=True)
    enabled = _telegram_security(enabled=True)
    with pytest.raises(TelegramSecurityError, match="CHAT_NOT_ALLOWED"):
        enabled.authorize(TelegramCommandContext("999", "200", "/status", 1_000))
    with pytest.raises(TelegramSecurityError, match="USER_NOT_ALLOWED"):
        enabled.authorize(TelegramCommandContext("100", "999", "/status", 1_000))


def test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary():
    security = _telegram_security(enabled=True)
    ctx = TelegramCommandContext("100", "200", "/live", 1_000)
    confirmation = security.issue_live_confirmation(ctx, symbol="btcusdt", side="buy", max_notional="250", mode="LIVE")
    assert confirmation.summary == "BTCUSDT BUY max_notional=250 mode=LIVE"
    consumed = security.consume_live_confirmation(ctx, nonce=confirmation.nonce, digest=confirmation.digest)
    assert consumed == confirmation
    with pytest.raises(TelegramSecurityError, match="REPLAY"):
        security.consume_live_confirmation(ctx, nonce=confirmation.nonce, digest=confirmation.digest)


def test_telegram_live_confirmation_rejects_expired_or_wrong_principal():
    security = _telegram_security(enabled=True)
    issued = TelegramCommandContext("100", "200", "/live", 1_000)
    confirmation = security.issue_live_confirmation(issued, symbol="ETHUSDT", side="SELL", max_notional="100", mode="LIVE")
    with pytest.raises(TelegramSecurityError, match="PRINCIPAL_MISMATCH"):
        security.consume_live_confirmation(TelegramCommandContext("100", "201", "/live", 1_001), nonce=confirmation.nonce, digest=confirmation.digest)
    with pytest.raises(TelegramSecurityError, match="EXPIRED"):
        security.consume_live_confirmation(TelegramCommandContext("100", "200", "/live", 1_061), nonce=confirmation.nonce, digest=confirmation.digest)


def test_idempotent_consumer_applies_duplicate_event_once_and_releases_failed_claim_for_retry():
    store = InMemoryReceiptStore()
    seen = []
    consumer = IdempotentConsumer("portfolio", store, lambda payload: seen.append(payload["value"]))
    first = consumer.consume(event_id="e1", payload={"value": 7})
    duplicate = consumer.consume(event_id="e1", payload={"value": 99})
    assert first.applied and not first.duplicate
    assert duplicate.duplicate and not duplicate.applied
    assert seen == [7]

    attempts = {"n": 0}
    def flaky(payload):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("temporary")
        seen.append(payload["value"])
    retryable = IdempotentConsumer("risk", store, flaky)
    with pytest.raises(RuntimeError, match="temporary"):
        retryable.consume(event_id="e2", payload={"value": 8})
    assert retryable.consume(event_id="e2", payload={"value": 8}).applied
    assert seen == [7, 8]


def _snap(balance="100", position="1", orders=None):
    return AccountSnapshot(
        balances={"USDT": Decimal(balance)},
        positions={"BTCUSDT": Decimal(position)},
        open_order_ids=set(orders or {"o1"}),
    )


def test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks():
    result = reconcile_composite(CompositeReconciliationEvidence(_snap(), _snap(), True, True, False, True))
    assert not result.complete
    assert result.risk_state == RiskState.MANUAL_REVIEW_REQUIRED
    assert result.missing_checks == ("EXCHANGE_OPEN_ORDERS",)


def test_composite_reconciliation_detects_drift_across_exchange_and_local_truth():
    result = reconcile_composite(CompositeReconciliationEvidence(_snap(), _snap(balance="90", orders={"o2"}), True, True, True, True))
    assert not result.complete
    assert result.risk_state == RiskState.MANUAL_REVIEW_REQUIRED
    assert "UNKNOWN_BALANCE_CHANGE:USDT" in result.drift
    assert "UNKNOWN_ORDER:o2" in result.drift
    assert "MISSING_EXCHANGE_ORDER:o1" in result.drift


def test_composite_reconciliation_is_complete_only_when_all_truth_domains_match():
    result = reconcile_composite(CompositeReconciliationEvidence(_snap(), _snap(), True, True, True, True))
    assert result.complete
    assert result.risk_state == RiskState.NORMAL
    assert result.drift == ()
