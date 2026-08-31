from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperCampaignPolicy:
    min_effective_sample_size: float = 100.0
    min_calendar_days: int = 30
    min_market_regimes: int = 2
    min_long_examples: int = 20
    min_exit_examples: int = 20
    min_short_examples: int = 0
    require_cost_stress: bool = True
    require_latency_stress: bool = True
    require_independent_oos: bool = True
    max_execution_divergence_bps: float = 25.0

    def validate(self) -> "PaperCampaignPolicy":
        if self.min_effective_sample_size <= 0:
            raise ValueError("minimum effective sample size must be positive")
        if self.min_calendar_days <= 0:
            raise ValueError("minimum calendar duration must be positive")
        if self.min_market_regimes < 2:
            raise ValueError("paper validation must cover multiple market regimes")
        for value in (self.min_long_examples, self.min_exit_examples, self.min_short_examples):
            if value < 0:
                raise ValueError("directional example minimums cannot be negative")
        if self.max_execution_divergence_bps < 0:
            raise ValueError("execution divergence limit cannot be negative")
        return self


@dataclass(frozen=True)
class PaperCampaignEvidence:
    effective_sample_size: float
    calendar_days: int
    market_regimes: tuple[str, ...]
    long_examples: int
    exit_examples: int
    short_examples: int
    active_market_type: str
    cost_stress_passed: bool
    latency_stress_passed: bool
    independent_oos_passed: bool
    execution_divergence_bps: float
    executed: bool
    real_market_data: bool

    def blockers(self, policy: PaperCampaignPolicy) -> tuple[str, ...]:
        policy.validate()
        out: list[str] = []
        if not self.executed:
            out.append("PAPER_CAMPAIGN_NOT_EXECUTED")
        if not self.real_market_data:
            out.append("REAL_MARKET_PAPER_EVIDENCE_MISSING")
        if self.effective_sample_size < policy.min_effective_sample_size:
            out.append("EFFECTIVE_SAMPLE_TOO_SMALL")
        if self.calendar_days < policy.min_calendar_days:
            out.append("CALENDAR_DURATION_TOO_SHORT")
        if len({x.strip().upper() for x in self.market_regimes if x.strip()}) < policy.min_market_regimes:
            out.append("INSUFFICIENT_MARKET_REGIMES")
        if self.long_examples < policy.min_long_examples:
            out.append("INSUFFICIENT_LONG_EXAMPLES")
        if self.exit_examples < policy.min_exit_examples:
            out.append("INSUFFICIENT_EXIT_EXAMPLES")
        market_type = self.active_market_type.strip().upper()
        if market_type in {"PERPETUAL", "FUTURES", "MARGIN"} and self.short_examples < policy.min_short_examples:
            out.append("INSUFFICIENT_SHORT_EXAMPLES")
        if policy.require_cost_stress and not self.cost_stress_passed:
            out.append("COST_STRESS_MISSING_OR_FAILED")
        if policy.require_latency_stress and not self.latency_stress_passed:
            out.append("LATENCY_STRESS_MISSING_OR_FAILED")
        if policy.require_independent_oos and not self.independent_oos_passed:
            out.append("INDEPENDENT_OOS_MISSING_OR_FAILED")
        if self.execution_divergence_bps < 0 or self.execution_divergence_bps > policy.max_execution_divergence_bps:
            out.append("EXECUTION_DIVERGENCE_EXCEEDED")
        return tuple(out)

    def assert_eligible(self, policy: PaperCampaignPolicy) -> "PaperCampaignEvidence":
        blockers = self.blockers(policy)
        if blockers:
            raise PermissionError("paper campaign is not LIVE-promotion eligible: " + ",".join(blockers))
        return self
