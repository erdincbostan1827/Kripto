from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class StrategyVote:
    strategy_id: str
    side: str
    expected_edge_bps: float
    confidence: float
    health: float
    regime_fit: float
    risk_score: float
    turnover: float = 0.0
    capacity_need: float = 0.0


@dataclass(frozen=True)
class DiversificationProfile:
    return_correlation: float
    signal_correlation: float
    drawdown_overlap: float
    regime_dependency: float
    turnover: float
    capacity_liquidity_need: float

    @property
    def diversification_score(self) -> float:
        penalty = sum(max(0.0, min(1.0, x)) for x in (
            abs(self.return_correlation), abs(self.signal_correlation), self.drawdown_overlap,
            self.regime_dependency, self.turnover, self.capacity_liquidity_need,
        )) / 6.0
        return max(0.0, min(1.0, 1.0 - penalty))


@dataclass(frozen=True)
class ConflictDecision:
    action: str
    score: float
    reason: str
    version: str = "1.0"


def resolve_conflict(votes: Sequence[StrategyVote], *, min_score: float = 0.10, max_conflict: float = 0.45) -> ConflictDecision:
    if not votes:
        return ConflictDecision("NO_TRADE", 0.0, "NO_VOTES")
    scored=[]
    for v in votes:
        side = 1.0 if v.side.upper() == "BUY" else -1.0 if v.side.upper() == "SELL" else 0.0
        quality=max(0.0,min(1.0,v.confidence))*max(0.0,min(1.0,v.health))*max(0.0,min(1.0,v.regime_fit))
        risk=max(0.0,min(1.0,v.risk_score))
        scored.append(side * (v.expected_edge_bps/100.0) * quality * (1-risk))
    gross=sum(abs(x) for x in scored)
    net=sum(scored)
    conflict=0.0 if gross == 0 else 1.0-abs(net)/gross
    if conflict > max_conflict or abs(net) < min_score:
        return ConflictDecision("NO_TRADE", net, "HIGH_CONFLICT_OR_LOW_EDGE")
    return ConflictDecision("BUY" if net>0 else "SELL", net, "OOS_VERSIONED_CONFLICT_RESOLUTION")


@dataclass(frozen=True)
class AbstentionInputs:
    net_edge_bps: float
    confidence_calibrated: bool = True
    mtf_conflict: bool = False
    regime_clear: bool = True
    spread_ok: bool = True
    liquidity_ok: bool = True
    slippage_ok: bool = True
    data_fresh_complete: bool = True
    venue_consistent: bool = True
    macro_event_safe: bool = True
    protected_positions: bool = True
    strategy_healthy: bool = True
    execution_healthy: bool = True
    risk_budget_available: bool = True
    cooling_period: bool = False


def abstention_reasons(x: AbstentionInputs, *, min_edge_bps: float) -> tuple[str, ...]:
    checks={
        "EDGE_TOO_LOW": x.net_edge_bps < min_edge_bps, "CONFIDENCE_UNCALIBRATED": not x.confidence_calibrated,
        "MTF_CONFLICT":x.mtf_conflict,"REGIME_UNCLEAR":not x.regime_clear,"SPREAD_HIGH":not x.spread_ok,
        "LIQUIDITY_INSUFFICIENT":not x.liquidity_ok,"SLIPPAGE_TOO_HIGH":not x.slippage_ok,
        "DATA_STALE_OR_INCOMPLETE":not x.data_fresh_complete,"CROSS_VENUE_DIVERGENCE":not x.venue_consistent,
        "MACRO_EVENT_RISK":not x.macro_event_safe,"UNPROTECTED_POSITION":not x.protected_positions,
        "STRATEGY_DEGRADED":not x.strategy_healthy,"EXECUTION_DEGRADED":not x.execution_healthy,
        "RISK_BUDGET_LOW":not x.risk_budget_available,"DRAWDOWN_COOLING":x.cooling_period,
    }
    return tuple(k for k,v in checks.items() if v)


@dataclass(frozen=True)
class CostEstimate:
    expected_fees_bps: float
    expected_spread_bps: float
    expected_slippage_bps: float
    expected_funding_or_borrow_bps: float
    uncertainty_buffer_bps: float

    @property
    def break_even_bps(self) -> float:
        return sum(max(0.0,v) for v in (
            self.expected_fees_bps,self.expected_spread_bps,self.expected_slippage_bps,
            self.expected_funding_or_borrow_bps,self.uncertainty_buffer_bps,
        ))


def cost_aware_gate(expected_gross_edge_bps: float, cost: CostEstimate, *, oos_validated: bool) -> tuple[bool,float,str]:
    net=expected_gross_edge_bps-cost.break_even_bps
    ok=bool(oos_validated and net>0)
    return ok,net,"PASS" if ok else "NO_TRADE"
