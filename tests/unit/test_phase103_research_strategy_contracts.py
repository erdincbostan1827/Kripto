from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.enums import MarketType
from app.research.objective import CapitalPreservationObjective, ExecutionCosts, ObjectiveEvidence
from app.research.registry import ResearchHypothesis, ResearchTrialLedger
from app.strategies.spec import PositionSide, SignalContext, StrategyDecisionFlow, StrategySpec, TradeAction

UTC = timezone.utc


def _strategy_spec(**overrides) -> StrategySpec:
    values = dict(
        strategy_id="trend-v1",
        strategy_version="1.0.0",
        hypothesis="Multi-timeframe trend alignment has positive net expectancy after costs.",
        supported_market_types=("SPOT", "PERPETUAL"),
        supported_symbols=("BTCUSDT",),
        allowed_direction=("LONG",),
        required_timeframes=("5m", "1h"),
        required_features=("ema21", "ema50", "atr", "volume_ratio"),
        warmup=200,
        valid_regimes=("BULLISH_TREND",),
        invalid_regimes=("HIGH_VOLATILITY",),
        entry_rule="EMA21 > EMA50 and momentum confirmed",
        confirmation_rule="1h trend agrees with 5m entry",
        invalidation_rule="trend alignment breaks",
        exit_rule="signal invalidation or time exit",
        stop_rule="ATR stop",
        take_profit_rule="risk-multiple target with trailing protection",
        max_holding_time_seconds=86_400,
        cooldown_seconds=900,
        order_policy={"type": "LIMIT_OR_MARKET", "max_slippage_bps": 20},
        position_sizing_policy={"risk_per_trade": 0.005},
        risk_limits={"max_drawdown": 0.20, "max_position_fraction": 0.10},
        assumptions=("liquid market", "point-in-time data"),
        known_failure_modes=("gap", "regime shift"),
    )
    values.update(overrides)
    return StrategySpec(**values)


def _evidence(**overrides) -> ObjectiveEvidence:
    values = dict(
        capital=100_000.0,
        gross_pnl=10_000.0,
        trade_count=100,
        wins=55,
        permanent_loss_fraction=0.01,
        max_drawdown_fraction=0.08,
        tail_loss_fraction=0.04,
        data_integrity_score=1.0,
        execution_integrity_score=1.0,
        oos_reliability_score=0.95,
        live_execution_quality_score=0.92,
        costs=ExecutionCosts(
            trading_fees=1_000,
            spread_cost=500,
            realized_slippage=600,
            funding_cost=200,
            borrow_cost=100,
            other_direct_costs=100,
        ),
    )
    values.update(overrides)
    return ObjectiveEvidence(**values)


def test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs():
    objective = CapitalPreservationObjective()
    safe = _evidence()
    unsafe_high_gross = _evidence(
        gross_pnl=100_000,
        wins=99,
        permanent_loss_fraction=0.25,
        max_drawdown_fraction=0.45,
        tail_loss_fraction=0.30,
    )
    safe_assessment = objective.assess(safe)
    unsafe_assessment = objective.assess(unsafe_high_gross)
    assert safe_assessment.eligible is True
    assert unsafe_assessment.eligible is False
    assert "PERMANENT_LOSS_RISK_TOO_HIGH" in unsafe_assessment.blockers
    assert "MAX_DRAWDOWN_TOO_HIGH" in unsafe_assessment.blockers
    assert "TAIL_LOSS_TOO_HIGH" in unsafe_assessment.blockers
    assert objective.select_best([unsafe_high_gross, safe]) == 1
    assert safe.costs.total == 2500
    assert safe_assessment.net_pnl == 7500
    assert safe_assessment.net_expectancy_per_trade == 75
    assert set(safe_assessment.cost_breakdown) >= {
        "trading_fees",
        "spread_cost",
        "realized_slippage",
        "funding_cost",
        "borrow_cost",
        "other_direct_costs",
    }
    negative_after_costs = _evidence(gross_pnl=2_000)
    assert "NET_EXPECTANCY_NOT_POSITIVE" in objective.assess(negative_after_costs).blockers
    low_quality = _evidence(data_integrity_score=0.5, execution_integrity_score=0.5, oos_reliability_score=0.5, live_execution_quality_score=0.5)
    reasons = objective.assess(low_quality).blockers
    assert "DATA_INTEGRITY_BELOW_THRESHOLD" in reasons
    assert "EXECUTION_INTEGRITY_BELOW_THRESHOLD" in reasons
    assert "OOS_RELIABILITY_BELOW_THRESHOLD" in reasons
    assert "LIVE_EXECUTION_QUALITY_BELOW_THRESHOLD" in reasons
    assert safe_assessment.risk_adjusted_net_return > 0


def test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract():
    spec = _strategy_spec()
    machine = spec.to_machine_readable()
    human = spec.to_markdown()
    required = {
        "strategy_id",
        "strategy_version",
        "hypothesis",
        "supported_market_types",
        "supported_symbols",
        "allowed_direction",
        "required_timeframes",
        "required_features",
        "warmup",
        "valid_regimes",
        "invalid_regimes",
        "entry_rule",
        "confirmation_rule",
        "invalidation_rule",
        "exit_rule",
        "stop_rule",
        "take_profit_rule",
        "max_holding_time_seconds",
        "cooldown_seconds",
        "order_policy",
        "position_sizing_policy",
        "risk_limits",
        "assumptions",
        "known_failure_modes",
    }
    assert required <= set(machine)
    assert all(f"**{field}**" in human for field in required)
    with pytest.raises(ValueError, match="SHORT direction requires"):
        _strategy_spec(allowed_direction=("LONG", "SHORT"))
    with pytest.raises(ValueError, match="short_validation"):
        _strategy_spec(allowed_direction=("LONG", "SHORT"), allow_short=True)
    short_spec = _strategy_spec(
        allowed_direction=("LONG", "SHORT"),
        allow_short=True,
        short_validation={"max_short_exposure": 0.10, "liquidation_buffer": 0.20},
    )
    assert short_spec.allow_short is True


def test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit():
    spec = _strategy_spec()
    spot_buy = spec.interpret_signal(SignalContext("BUY", MarketType.SPOT, PositionSide.LONG, Decimal("0")))
    spot_sell_flat = spec.interpret_signal(SignalContext("SELL", MarketType.SPOT, PositionSide.LONG, Decimal("0")))
    spot_sell_inventory = spec.interpret_signal(SignalContext("SELL", MarketType.SPOT, PositionSide.LONG, Decimal("1")))
    assert spot_buy == TradeAction.INCREASE_LONG
    assert spot_sell_flat == TradeAction.NO_ACTION
    assert spot_sell_inventory == TradeAction.REDUCE_LONG_OR_EXIT
    with pytest.raises(PermissionError, match="SPOT position side"):
        spec.interpret_signal(SignalContext("SELL", MarketType.SPOT, PositionSide.SHORT, Decimal("0")))

    short_spec = _strategy_spec(
        allowed_direction=("LONG", "SHORT"),
        allow_short=True,
        short_validation={"max_short_exposure": 0.10, "liquidation_buffer": 0.20},
    )
    assert short_spec.interpret_signal(SignalContext("SELL", MarketType.PERPETUAL, PositionSide.SHORT, Decimal("0"))) == TradeAction.INCREASE_SHORT
    assert short_spec.interpret_signal(SignalContext("BUY", MarketType.PERPETUAL, PositionSide.SHORT, Decimal("2"))) == TradeAction.REDUCE_SHORT_OR_EXIT


def test_phase103_signal_riskapproved_orderintent_transition_cannot_skip_risk():
    flow = StrategyDecisionFlow(_strategy_spec())
    signal = flow.signal(
        symbol="BTCUSDT",
        context=SignalContext("BUY", MarketType.SPOT, PositionSide.LONG, Decimal("0")),
    )
    rejected = flow.approve_risk(signal, approved=False, reason="portfolio limit")
    with pytest.raises(PermissionError, match="RiskApproved"):
        flow.to_order_intent(rejected, intent_id="i-1", account_id="a-1", quantity=Decimal("0.01"))
    approved = flow.approve_risk(signal, approved=True, reason="all pretrade risk gates passed")
    intent = flow.to_order_intent(approved, intent_id="i-2", account_id="a-1", quantity=Decimal("0.01"))
    assert intent.side == "BUY"
    assert intent.strategy_id == "trend-v1"
    assert intent.client_order_id == "i-2"


def _periods(base: datetime):
    train = (base, base + timedelta(days=30))
    validation = (train[1], train[1] + timedelta(days=10))
    test = (validation[1], validation[1] + timedelta(days=10))
    return train, validation, test


def test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete():
    registered = datetime(2026, 1, 1, tzinfo=UTC)
    hypothesis = ResearchHypothesis(
        hypothesis_id="H-1",
        statement="Trend persistence survives execution costs.",
        primary_metric="oos_net_sharpe",
        test_set_hash="a" * 64,
        parameter_search_budget=3,
        researcher_agent="quant-agent",
        registered_at=registered,
    )
    ledger = ResearchTrialLedger()
    ledger.register_hypothesis(hypothesis)
    train, validation, test = _periods(registered + timedelta(days=1))
    entry = ledger.append_trial(
        trial_id="T-1",
        hypothesis_id="H-1",
        strategy_family="trend",
        tested_features=("ema", "atr"),
        tested_parameters={"ema_fast": 21, "ema_slow": 50},
        dataset_hash="b" * 64,
        train_period=train,
        validation_period=validation,
        test_period=test,
        metrics={"oos_net_sharpe": 1.2, "max_drawdown": 0.08},
        failure_reason=None,
        selected=True,
        researcher_agent="quant-agent",
        timestamp=test[1] + timedelta(seconds=1),
        primary_metric="oos_net_sharpe",
        test_set_hash="a" * 64,
    )
    assert entry.trial_id == "T-1"
    assert entry.hypothesis_id == "H-1"
    assert entry.strategy_family == "trend"
    assert entry.tested_features == ("ema", "atr")
    assert entry.tested_parameters["ema_fast"] == 21
    assert entry.dataset_hash == "b" * 64
    assert entry.train_period == train and entry.validation_period == validation and entry.test_period == test
    assert entry.metrics["oos_net_sharpe"] == 1.2
    assert entry.failure_reason is None and entry.selected is True
    assert entry.researcher_agent == "quant-agent" and entry.timestamp.tzinfo is not None
    assert entry.previous_hash == ledger.GENESIS_HASH
    assert len(entry.entry_hash) == 64
    assert ledger.verify_integrity() is True
    with pytest.raises(FrozenInstanceError):
        entry.selected = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="duplicate"):
        ledger.append_trial(
            trial_id="T-1",
            hypothesis_id="H-1",
            strategy_family="trend",
            tested_features=("ema",),
            tested_parameters={"ema_fast": 20},
            dataset_hash="b" * 64,
            train_period=train,
            validation_period=validation,
            test_period=test,
            metrics={"oos_net_sharpe": 1.0},
            failure_reason="duplicate",
            selected=False,
            researcher_agent="quant-agent",
            timestamp=test[1] + timedelta(seconds=2),
            primary_metric="oos_net_sharpe",
            test_set_hash="a" * 64,
        )


def test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget():
    registered = datetime(2026, 1, 1, tzinfo=UTC)
    ledger = ResearchTrialLedger()
    ledger.register_hypothesis(
        ResearchHypothesis(
            hypothesis_id="H-LOCK",
            statement="Pre-registered hypothesis.",
            primary_metric="net_expectancy",
            test_set_hash="c" * 64,
            parameter_search_budget=1,
            researcher_agent="agent-1",
            registered_at=registered,
        )
    )
    train, validation, test = _periods(registered + timedelta(days=1))
    common = dict(
        hypothesis_id="H-LOCK",
        strategy_family="mean-reversion",
        tested_features=("rsi",),
        tested_parameters={"rsi_low": 25},
        dataset_hash="d" * 64,
        train_period=train,
        validation_period=validation,
        test_period=test,
        metrics={"net_expectancy": -0.1},
        failure_reason="no positive net edge",
        selected=False,
        researcher_agent="agent-1",
        timestamp=test[1] + timedelta(seconds=1),
        primary_metric="net_expectancy",
        test_set_hash="c" * 64,
    )
    ledger.append_trial(trial_id="T-LOCK-1", **common)
    assert ledger.all()[0].search_ordinal == 1
    with pytest.raises(PermissionError, match="budget exceeded"):
        ledger.append_trial(trial_id="T-LOCK-2", **common)

    other = ResearchTrialLedger()
    other.register_hypothesis(ledger.hypotheses()[0])
    with pytest.raises(PermissionError, match="primary metric"):
        other.append_trial(trial_id="T-METRIC", **{**common, "primary_metric": "gross_return"})
    with pytest.raises(PermissionError, match="test set"):
        other.append_trial(trial_id="T-TESTSET", **{**common, "test_set_hash": "e" * 64})

    unregistered = ResearchTrialLedger()
    with pytest.raises(PermissionError, match="registered before"):
        unregistered.append_trial(trial_id="T-NO-H", **common)
