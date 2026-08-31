from decimal import Decimal
from pathlib import Path

import yaml

from app.execution.sleeves import PositionSide, StrategySleeveBook
from app.risk.perpetual import PerpetualRiskLimits, PerpetualRiskSnapshot, evaluate_perpetual_risk


def test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net():
    book = StrategySleeveBook(hedging_supported=True)
    first = book.allocate_fill(strategy_id="trend", symbol="BTCUSDT", side="LONG", quantity=Decimal("2"), entry_price=Decimal("100"), source_order_id="o1", source_fill_id="f1", fee=Decimal("0.2"), funding=Decimal("0.1"))
    book.allocate_fill(strategy_id="mean", symbol="BTCUSDT", side="SHORT", quantity=Decimal("0.5"), entry_price=Decimal("110"), source_order_id="o2", source_fill_id="f2")
    pnl = book.close(strategy_id="trend", symbol="BTCUSDT", side="LONG", quantity=Decimal("1"), exit_price=Decimal("120"), exit_fee=Decimal("0.3"), funding=Decimal("0.2"))
    assert pnl == Decimal("19.5")
    assert first.realized_pnl == Decimal("19.5")
    assert first.fees == Decimal("0.5")
    assert first.funding == Decimal("0.3")
    assert book.strategy_virtual_sleeve("trend", "BTCUSDT") == Decimal("1")
    assert book.strategy_virtual_sleeve("mean", "BTCUSDT") == Decimal("-0.5")
    assert book.account_net_position("BTCUSDT") == Decimal("0.5")
    assert book.reconcile_account_net(symbol="BTCUSDT", exchange_account_net_quantity=Decimal("0.5")).consistent


def test_strategy_sleeve_conflict_policy_blocks_cross_strategy_exit_and_unapproved_transfer():
    book = StrategySleeveBook()
    lot = book.allocate_fill(strategy_id="a", symbol="ETHUSDT", side="LONG", quantity=Decimal("1"), entry_price=Decimal("2000"), source_order_id="o", source_fill_id="f")
    try:
        book.close(strategy_id="b", symbol="ETHUSDT", side="LONG", quantity=Decimal("1"), exit_price=Decimal("2100"))
        raise AssertionError("cross-strategy exit must fail")
    except ValueError:
        pass
    try:
        book.transfer_ownership(lot_id=lot.lot_id, from_strategy="a", to_strategy="b")
        raise AssertionError("unapproved ownership transfer must fail")
    except PermissionError:
        pass


def test_strategy_sleeve_hedging_policy_is_explicit_and_fail_closed_when_unsupported():
    book = StrategySleeveBook(hedging_supported=False)
    book.allocate_fill(strategy_id="a", symbol="SOLUSDT", side="LONG", quantity=Decimal("1"), entry_price=Decimal("100"), source_order_id="o1", source_fill_id="f1")
    try:
        book.allocate_fill(strategy_id="b", symbol="SOLUSDT", side="SHORT", quantity=Decimal("1"), entry_price=Decimal("101"), source_order_id="o2", source_fill_id="f2")
        raise AssertionError("unsupported hedge must fail")
    except ValueError as exc:
        assert "hedging conflict" in str(exc)


def _limits():
    return PerpetualRiskLimits(
        max_leverage=Decimal("5"), leverage_per_symbol={"BTCUSDT": Decimal("3")},
        min_liquidation_distance_pct=Decimal("0.10"), max_maintenance_margin_ratio=Decimal("0.70"),
        max_margin_ratio=Decimal("0.75"), max_abs_funding_rate=Decimal("0.002"),
        max_expected_funding_cost=Decimal("25"), max_mark_index_divergence_pct=Decimal("0.01"),
        max_open_interest=Decimal("1000000000"), max_liquidation_spike_ratio=Decimal("2"), max_funding_age_ms=60000,
    )


def _snapshot(**overrides):
    values = dict(symbol="BTCUSDT", leverage=Decimal("2"), liquidation_distance_pct=Decimal("0.20"), maintenance_margin_ratio=Decimal("0.20"), margin_ratio=Decimal("0.30"), funding_rate=Decimal("0.0001"), funding_timestamp_ms=990000, expected_funding_cost=Decimal("2"), mark_price=Decimal("100"), index_price=Decimal("100"), open_interest=Decimal("100000"), liquidation_spike_ratio=Decimal("1"), reduce_only=True, position_reducing=True)
    values.update(overrides)
    return PerpetualRiskSnapshot(**values)


def test_perpetual_risk_engine_accepts_complete_safe_snapshot():
    decision = evaluate_perpetual_risk(_snapshot(), _limits(), now_ms=1_000_000)
    assert decision.allowed and decision.reasons == ()


def test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes():
    decision = evaluate_perpetual_risk(_snapshot(leverage=Decimal("4"), liquidation_distance_pct=Decimal("0.05"), maintenance_margin_ratio=Decimal("0.8"), margin_ratio=Decimal("0.9"), funding_rate=Decimal("0.01"), funding_timestamp_ms=1, expected_funding_cost=Decimal("30"), mark_price=Decimal("105"), open_interest=Decimal("2000000000"), liquidation_spike_ratio=Decimal("3")), _limits(), now_ms=1_000_000)
    expected = {"LEVERAGE_LIMIT", "LIQUIDATION_BUFFER_TOO_LOW", "MAINTENANCE_MARGIN_TOO_HIGH", "MARGIN_RATIO_TOO_HIGH", "FUNDING_RATE_LIMIT", "FUNDING_DATA_STALE", "EXPECTED_FUNDING_COST_LIMIT", "MARK_INDEX_DIVERGENCE", "OPEN_INTEREST_LIMIT", "LIQUIDATION_SPIKE"}
    assert not decision.allowed
    assert expected.issubset(set(decision.reasons))


def test_perpetual_reduce_only_enforcement_rejects_position_increase():
    decision = evaluate_perpetual_risk(_snapshot(reduce_only=True, position_reducing=False), _limits(), now_ms=1_000_000)
    assert decision.reasons == ("REDUCE_ONLY_WOULD_INCREASE_POSITION",)


def test_canonical_architecture_profile_and_adrs_cover_required_decision_fields():
    profile = yaml.safe_load(Path("architecture_profile.yaml").read_text())
    assert "Python" in profile["runtime"]["language"]
    assert "async" in profile["runtime"]["async_model"].lower()
    assert "PostgreSQL" in profile["scheduler_worker"]["financial_event_truth"]
    assert "PostgreSQL" in profile["persistence"]["database"]
    assert profile["cache"]["redis"]
    assert "cache" in profile["cache"]["role"].lower()
    assert profile["proxy"]["selected"].startswith("nginx")
    assert profile["frontend"]["package_manager"].startswith("npm")
    assert "session" in profile["security"]
    assert profile["security"]["secret_provider_prod"]
    assert profile["deployment"]["default"]
    assert profile["observability"]["metrics"] and profile["observability"]["dashboard"]
    assert profile["exchange_matrix"]
    adr = Path("ARCHITECTURE_DECISIONS.md").read_text()
    for field in ("ADR_ID", "selected_option", "alternatives_considered", "rationale", "operational_tradeoff", "security_tradeoff", "rollback/migration impact"):
        assert field in adr
