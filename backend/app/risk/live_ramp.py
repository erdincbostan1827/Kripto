from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Mapping

STAGES = ("LIVE_STAGE_0", "LIVE_STAGE_1", "LIVE_STAGE_2", "LIVE_STAGE_3")
DEFAULT_STAGE_MULTIPLIERS: Mapping[str, Decimal] = {
    "LIVE_STAGE_0": Decimal("0.10"),
    "LIVE_STAGE_1": Decimal("0.25"),
    "LIVE_STAGE_2": Decimal("0.50"),
    "LIVE_STAGE_3": Decimal("1.00"),
}


@dataclass(frozen=True)
class LiveRampEvidence:
    reconciliation_pass: bool
    unresolved_critical_incidents: int
    protective_order_success_rate: Decimal
    live_slippage_bps: Decimal
    live_shadow_divergence_bps: Decimal
    net_expectancy: Decimal
    expectancy_lower_confidence_bound: Decimal
    drawdown: Decimal
    effective_sample_size: Decimal
    market_conditions_observed: int
    strategy_degraded: bool


@dataclass(frozen=True)
class LiveRampPolicy:
    min_protective_success_rate: Decimal = Decimal("0.995")
    max_live_slippage_bps: Decimal = Decimal("25")
    max_live_shadow_divergence_bps: Decimal = Decimal("35")
    max_drawdown: Decimal = Decimal("0.10")
    min_effective_sample_size: Decimal = Decimal("30")
    min_market_conditions: int = 2
    require_non_negative_expectancy_lcb: bool = True
    stage_multipliers: Mapping[str, Decimal] = field(default_factory=lambda: dict(DEFAULT_STAGE_MULTIPLIERS))

    def __post_init__(self) -> None:
        if tuple(self.stage_multipliers) != STAGES:
            raise ValueError("stage multipliers must define LIVE_STAGE_0..3 in order")
        values = tuple(Decimal(str(self.stage_multipliers[s])) for s in STAGES)
        if any(v <= 0 or v > 1 for v in values):
            raise ValueError("stage multipliers must be in (0,1]")
        if tuple(sorted(values)) != values:
            raise ValueError("stage multipliers must be monotonic")

    def blockers(self, evidence: LiveRampEvidence) -> tuple[str, ...]:
        blockers: list[str] = []
        if not evidence.reconciliation_pass:
            blockers.append("RECONCILIATION_NOT_PASS")
        if evidence.unresolved_critical_incidents != 0:
            blockers.append("CRITICAL_INCIDENTS_UNRESOLVED")
        if evidence.protective_order_success_rate < self.min_protective_success_rate:
            blockers.append("PROTECTIVE_ORDER_SUCCESS_TOO_LOW")
        if evidence.live_slippage_bps > self.max_live_slippage_bps:
            blockers.append("LIVE_SLIPPAGE_TOO_HIGH")
        if evidence.live_shadow_divergence_bps > self.max_live_shadow_divergence_bps:
            blockers.append("LIVE_SHADOW_DIVERGENCE_TOO_HIGH")
        expectancy_floor = evidence.expectancy_lower_confidence_bound if self.require_non_negative_expectancy_lcb else evidence.net_expectancy
        if expectancy_floor < 0:
            blockers.append("NET_EXPECTANCY_UNACCEPTABLE")
        if evidence.drawdown > self.max_drawdown:
            blockers.append("DRAWDOWN_TOO_HIGH")
        if evidence.effective_sample_size < self.min_effective_sample_size:
            blockers.append("EFFECTIVE_SAMPLE_TOO_SMALL")
        if evidence.market_conditions_observed < self.min_market_conditions:
            blockers.append("INSUFFICIENT_MARKET_CONDITIONS")
        if evidence.strategy_degraded:
            blockers.append("STRATEGY_DEGRADED")
        return tuple(blockers)

    def eligible(self, evidence: LiveRampEvidence) -> bool:
        return not self.blockers(evidence)


@dataclass
class LiveRamp:
    stage: str = "LIVE_STAGE_0"
    policy: LiveRampPolicy = field(default_factory=LiveRampPolicy)

    def __post_init__(self) -> None:
        if self.stage not in STAGES:
            raise ValueError("unknown LIVE ramp stage")

    @property
    def risk_multiplier(self) -> Decimal:
        return Decimal(str(self.policy.stage_multipliers[self.stage]))

    def increase(self, evidence: LiveRampEvidence | dict, human_approved: bool = False) -> str:
        # Backward-compatible dict input remains accepted for existing callers/tests.
        if isinstance(evidence, dict):
            required = (
                "reconciliation", "critical_incidents_clear", "protective_success", "slippage_bound",
                "shadow_divergence_bound", "expectancy_acceptable", "drawdown_bound", "effective_sample",
                "multiple_conditions", "strategy_healthy",
            )
            if not all(evidence.get(k, False) for k in required):
                raise PermissionError("live ramp evidence incomplete")
        else:
            blockers = self.policy.blockers(evidence)
            if blockers:
                raise PermissionError("live ramp evidence incomplete: " + ",".join(blockers))
        if not human_approved:
            raise PermissionError("automatic live risk increase disabled")
        i = STAGES.index(self.stage)
        if i < len(STAGES) - 1:
            self.stage = STAGES[i + 1]
        return self.stage

    def decrease(self) -> str:
        i = STAGES.index(self.stage)
        self.stage = STAGES[max(0, i - 1)]
        return self.stage
