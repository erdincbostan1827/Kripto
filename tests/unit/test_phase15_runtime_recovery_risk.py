from dataclasses import replace
from decimal import Decimal

import pytest

from app.core.config_compat import ConfigCompatibilityRegistry
from app.monitoring.escalation import PersistentEscalationLedger
from app.recovery.runtime_checkpoint import create_runtime_checkpoint, evaluate_restore, verify_runtime_checkpoint
from app.risk.market_type_guard import MarketTypeRiskSnapshot, evaluate_market_type_risk


def test_runtime_checkpoint_signed_and_restore_requires_exact_config_event_state():
    secret = b"phase15-test-key"
    cp = create_runtime_checkpoint(
        secret=secret, created_at_unix=1000, risk_state="REDUCING_ONLY", config_hash="cfg1",
        last_event_sequence=41, positions={"BTCUSDT": "0.1"}, open_order_ids=["o2", "o1"],
        reservations={"USDT": "100"}, event_chain_hash="chain41",
    )
    assert verify_runtime_checkpoint(cp, secret=secret)
    ok = evaluate_restore(cp, secret=secret, now_unix=1010, current_config_hash="cfg1", current_event_sequence=41,
                          current_event_chain_hash="chain41", max_checkpoint_age_seconds=60)
    assert ok.allowed
    bad = evaluate_restore(cp, secret=secret, now_unix=1010, current_config_hash="cfg2", current_event_sequence=42,
                           current_event_chain_hash="chain42", max_checkpoint_age_seconds=60)
    assert not bad.allowed
    assert {"CONFIG_HASH_MISMATCH", "EVENT_SEQUENCE_MISMATCH", "EVENT_CHAIN_HASH_MISMATCH"}.issubset(bad.reasons)


def test_runtime_checkpoint_tampering_and_staleness_fail_closed():
    secret = b"phase15-test-key"
    cp = create_runtime_checkpoint(secret=secret, created_at_unix=1000, risk_state="ACTIVE", config_hash="cfg",
                                   last_event_sequence=1, positions={}, open_order_ids=[], reservations={}, event_chain_hash="x")
    tampered = replace(cp, risk_state="ACTIVE_BUT_TAMPERED")
    assert not verify_runtime_checkpoint(tampered, secret=secret)
    decision = evaluate_restore(cp, secret=secret, now_unix=2000, current_config_hash="cfg", current_event_sequence=1,
                                current_event_chain_hash="x", max_checkpoint_age_seconds=60)
    assert decision.reasons == ("CHECKPOINT_STALE",)


def test_alert_escalation_survives_restart_and_stops_after_ack(tmp_path):
    path = tmp_path / "alerts.db"
    first = PersistentEscalationLedger(path)
    first.record("PRIVATE_STREAM_STALE", "SEV1", now=100, escalation_seconds=10, evidence={"account": "A"})
    assert first.due(now=109) == []
    second = PersistentEscalationLedger(path)
    due = second.due(now=110)
    assert len(due) == 1 and due[0].alert_key == "PRIVATE_STREAM_STALE"
    escalated = second.mark_escalated("PRIVATE_STREAM_STALE", now=110, escalation_seconds=20)
    assert escalated.attempts == 1 and escalated.next_escalation_at == 130
    second.acknowledge("PRIVATE_STREAM_STALE")
    assert second.due(now=1000) == []


def test_alert_resolution_allows_fresh_occurrence(tmp_path):
    ledger = PersistentEscalationLedger(tmp_path / "alerts.db")
    ledger.record("DB_DOWN", "SEV1", now=10, escalation_seconds=5)
    ledger.resolve("DB_DOWN")
    new = ledger.record("DB_DOWN", "SEV1", now=20, escalation_seconds=5)
    assert not new.resolved and not new.acknowledged and new.first_seen_at == 20


def test_spot_forbids_liquidation_leverage_semantics_and_enforces_concentration():
    snapshot = MarketTypeRiskSnapshot("SPOT", Decimal("600"), Decimal("1000"), Decimal("200"), Decimal("500"), leverage=Decimal("2"))
    decision = evaluate_market_type_risk(snapshot, max_gross_exposure_ratio=Decimal("0.5"), max_single_symbol_ratio=Decimal("0.15"), max_quote_asset_ratio=Decimal("0.4"))
    assert not decision.allowed
    assert {"GROSS_EXPOSURE_LIMIT", "SINGLE_SYMBOL_CONCENTRATION", "QUOTE_ASSET_CONCENTRATION", "SPOT_DERIVATIVE_SEMANTICS_FORBIDDEN"}.issubset(decision.reasons)


def test_derivative_market_requires_liquidation_margin_and_leverage_buffers():
    snapshot = MarketTypeRiskSnapshot("FUTURES", Decimal("1500"), Decimal("1000"), Decimal("500"), Decimal("100"),
                                      liquidation_distance_pct=Decimal("0.05"), maintenance_margin_ratio=Decimal("0.8"), leverage=Decimal("5"))
    decision = evaluate_market_type_risk(snapshot, max_gross_exposure_ratio=Decimal("2"), max_single_symbol_ratio=Decimal("0.7"), max_quote_asset_ratio=Decimal("0.5"))
    assert not decision.allowed
    assert decision.reasons == ("LIQUIDATION_BUFFER_TOO_LOW", "MAINTENANCE_MARGIN_TOO_HIGH", "LEVERAGE_LIMIT")


def test_config_registry_migrates_sequentially_and_hashes_canonical_result():
    registry = ConfigCompatibilityRegistry(current_version=3)
    def rename_risk(c):
        value = c.pop("risk")
        return {**c, "risk_per_trade": value}
    registry.register(1, 2, "rename-risk", rename_risk)
    registry.register(2, 3, "add-mode", lambda c: {**c, "mode": c.get("mode", "PAPER")})
    result = registry.migrate({"schema_version": 1, "risk": "0.0025"})
    assert result.target_version == 3
    assert result.config == {"schema_version": 3, "risk_per_trade": "0.0025", "mode": "PAPER"}
    assert result.applied_migrations == ("rename-risk", "add-mode")
    assert len(result.config_hash) == 64


def test_config_registry_rejects_future_or_missing_migration():
    registry = ConfigCompatibilityRegistry(current_version=3)
    with pytest.raises(ValueError, match="future config"):
        registry.migrate({"schema_version": 4})
    with pytest.raises(ValueError, match="missing config migration"):
        registry.migrate({"schema_version": 1})

from app.recovery.operator_runbook import RecoveryEvidence, RecoveryStep, plan_operator_recovery


def test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection():
    evidence = RecoveryEvidence(
        database_read_ok=True, exchange_truth_ok=True, reconciliation_drift=("UNKNOWN_ORDER:o1",),
        open_risk_identified=True, protective_orders_ok=True, clock_ok=True, data_ok=True, human_approved=True,
    )
    plan = plan_operator_recovery(evidence)
    assert plan.target_state == "MANUAL_REVIEW_REQUIRED"
    assert "RECONCILIATION_DRIFT" in plan.reasons
    assert plan.steps[:4] == (
        RecoveryStep.RESTART_SERVICES, RecoveryStep.READ_DURABLE_DATABASE,
        RecoveryStep.FETCH_EXCHANGE_TRUTH, RecoveryStep.RECONCILE,
    )


def test_operator_recovery_never_resumes_active_without_human_approval():
    base = dict(database_read_ok=True, exchange_truth_ok=True, reconciliation_drift=(), open_risk_identified=True,
                protective_orders_ok=True, clock_ok=True, data_ok=True)
    pending = plan_operator_recovery(RecoveryEvidence(**base, human_approved=False))
    assert pending.target_state == "RECOVERY_PENDING"
    assert pending.steps[-1] == RecoveryStep.REQUIRE_HUMAN_APPROVAL
    active = plan_operator_recovery(RecoveryEvidence(**base, human_approved=True))
    assert active.target_state == "ACTIVE"
    assert active.steps[-2:] == (RecoveryStep.RESUME_REDUCING_ONLY, RecoveryStep.RESUME_ACTIVE)
