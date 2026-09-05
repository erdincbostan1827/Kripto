from decimal import Decimal

import pytest

from app.backtest.stress_qualification import (
    StressScenario,
    evaluate_stress_matrix,
    evaluate_stress_scenario,
)
from app.backtest.transaction_costs import FeeSchedule, TransactionCostModel

D = Decimal


def _base_model() -> TransactionCostModel:
    return TransactionCostModel(
        fees=FeeSchedule(taker_buy_bps=D("10"), taker_sell_bps=D("10")),
        spread_bps=D("6"),
        slippage_bps=D("4"),
        impact_coefficient_bps=D("20"),
        max_market_impact_bps=D("50"),
    )


def test_cost_and_latency_stress_are_deducted_from_gross_edge() -> None:
    result = evaluate_stress_scenario(
        gross_edge_bps=D("100"),
        base_model=_base_model(),
        scenario=StressScenario(
            name="adverse",
            fee_multiplier=D("2"),
            spread_multiplier=D("2"),
            slippage_multiplier=D("3"),
            latency_penalty_bps=D("7"),
            participation_rate=D("0.10"),
        ),
        minimum_net_edge_bps=D("10"),
    )
    # 40 fees + 12 spread + 24 slippage + 4 impact + 7 latency = 87 bps.
    assert result.transaction_cost_bps == D("80.00")
    assert result.net_edge_bps == D("13.00")
    assert result.qualifies is True


def test_qualification_fails_closed_when_stress_erases_edge() -> None:
    result = evaluate_stress_scenario(
        gross_edge_bps=D("50"),
        base_model=_base_model(),
        scenario=StressScenario(name="latency", latency_penalty_bps=D("20")),
        minimum_net_edge_bps=D("5"),
    )
    assert result.net_edge_bps == D("16")
    assert result.qualifies is True

    failed = evaluate_stress_scenario(
        gross_edge_bps=D("35"),
        base_model=_base_model(),
        scenario=StressScenario(name="latency", latency_penalty_bps=D("20")),
        minimum_net_edge_bps=D("5"),
    )
    assert failed.net_edge_bps == D("1")
    assert failed.qualifies is False


def test_matrix_preserves_scenario_order() -> None:
    results = evaluate_stress_matrix(
        gross_edge_bps=D("100"),
        base_model=_base_model(),
        scenarios=(StressScenario(name="base"), StressScenario(name="slow", latency_penalty_bps=D("5"))),
    )
    assert tuple(result.scenario for result in results) == ("base", "slow")
    assert results[1].net_edge_bps < results[0].net_edge_bps


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fee_multiplier": D("-1")},
        {"spread_multiplier": D("-1")},
        {"slippage_multiplier": D("-1")},
        {"latency_penalty_bps": D("-1")},
        {"participation_rate": D("-1")},
    ],
)
def test_invalid_stress_inputs_fail_closed(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        StressScenario(name="invalid", **kwargs)
