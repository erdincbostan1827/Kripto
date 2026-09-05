from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.backtest.transaction_costs import FeeSchedule, TransactionCostModel

D = Decimal


@dataclass(frozen=True)
class StressScenario:
    name: str
    fee_multiplier: D = D("1")
    spread_multiplier: D = D("1")
    slippage_multiplier: D = D("1")
    latency_penalty_bps: D = D("0")
    participation_rate: D = D("0")

    def __post_init__(self) -> None:
        for name, value in (
            ("fee_multiplier", self.fee_multiplier),
            ("spread_multiplier", self.spread_multiplier),
            ("slippage_multiplier", self.slippage_multiplier),
            ("latency_penalty_bps", self.latency_penalty_bps),
            ("participation_rate", self.participation_rate),
        ):
            if D(value) < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True)
class StressResult:
    scenario: str
    gross_edge_bps: D
    transaction_cost_bps: D
    latency_penalty_bps: D
    net_edge_bps: D
    qualifies: bool


def evaluate_stress_scenario(
    *,
    gross_edge_bps: D,
    base_model: TransactionCostModel,
    scenario: StressScenario,
    minimum_net_edge_bps: D = D("0"),
) -> StressResult:
    """Evaluate a hypothetical edge without asserting real PAPER/OOS evidence.

    This is deliberately a pure calculation. A PASS here is only a scenario-level
    mathematical result; campaign/OOS/profitability qualification must consume
    independently collected real evidence before any production conclusion.
    """
    gross = D(gross_edge_bps)
    minimum = D(minimum_net_edge_bps)
    fees = FeeSchedule(
        maker_buy_bps=base_model.fees.maker_buy_bps * scenario.fee_multiplier,
        maker_sell_bps=base_model.fees.maker_sell_bps * scenario.fee_multiplier,
        taker_buy_bps=base_model.fees.taker_buy_bps * scenario.fee_multiplier,
        taker_sell_bps=base_model.fees.taker_sell_bps * scenario.fee_multiplier,
    )
    stressed = TransactionCostModel(
        fees=fees,
        spread_bps=base_model.spread_bps * scenario.spread_multiplier,
        slippage_bps=base_model.slippage_bps * scenario.slippage_multiplier,
        impact_coefficient_bps=base_model.impact_coefficient_bps,
        max_market_impact_bps=base_model.max_market_impact_bps,
    )
    costs = stressed.round_trip_cost_bps(participation_rate=scenario.participation_rate)
    latency = D(scenario.latency_penalty_bps)
    net = gross - costs - latency
    return StressResult(
        scenario=scenario.name,
        gross_edge_bps=gross,
        transaction_cost_bps=costs,
        latency_penalty_bps=latency,
        net_edge_bps=net,
        qualifies=net >= minimum,
    )


def evaluate_stress_matrix(
    *,
    gross_edge_bps: D,
    base_model: TransactionCostModel,
    scenarios: Iterable[StressScenario],
    minimum_net_edge_bps: D = D("0"),
) -> tuple[StressResult, ...]:
    return tuple(
        evaluate_stress_scenario(
            gross_edge_bps=gross_edge_bps,
            base_model=base_model,
            scenario=scenario,
            minimum_net_edge_bps=minimum_net_edge_bps,
        )
        for scenario in scenarios
    )
