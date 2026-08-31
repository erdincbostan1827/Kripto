from __future__ import annotations

from dataclasses import dataclass
import math


def _finite(name: str, value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


@dataclass(frozen=True)
class ExecutionCosts:
    trading_fees: float = 0.0
    spread_cost: float = 0.0
    realized_slippage: float = 0.0
    funding_cost: float = 0.0
    borrow_cost: float = 0.0
    other_direct_costs: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "trading_fees",
            "spread_cost",
            "realized_slippage",
            "funding_cost",
            "borrow_cost",
            "other_direct_costs",
        ):
            value = _finite(name, getattr(self, name))
            if value < 0:
                raise ValueError(f"{name} cannot be negative")

    @property
    def total(self) -> float:
        return float(
            self.trading_fees
            + self.spread_cost
            + self.realized_slippage
            + self.funding_cost
            + self.borrow_cost
            + self.other_direct_costs
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "trading_fees": float(self.trading_fees),
            "spread_cost": float(self.spread_cost),
            "realized_slippage": float(self.realized_slippage),
            "funding_cost": float(self.funding_cost),
            "borrow_cost": float(self.borrow_cost),
            "other_direct_costs": float(self.other_direct_costs),
            "total": self.total,
        }


@dataclass(frozen=True)
class ObjectiveEvidence:
    capital: float
    gross_pnl: float
    trade_count: int
    wins: int
    permanent_loss_fraction: float
    max_drawdown_fraction: float
    tail_loss_fraction: float
    data_integrity_score: float
    execution_integrity_score: float
    oos_reliability_score: float
    live_execution_quality_score: float
    costs: ExecutionCosts

    def __post_init__(self) -> None:
        if _finite("capital", self.capital) <= 0:
            raise ValueError("capital must be positive")
        _finite("gross_pnl", self.gross_pnl)
        if self.trade_count < 1:
            raise ValueError("trade_count must be positive")
        if self.wins < 0 or self.wins > self.trade_count:
            raise ValueError("wins must be between zero and trade_count")
        for name in (
            "permanent_loss_fraction",
            "max_drawdown_fraction",
            "tail_loss_fraction",
            "data_integrity_score",
            "execution_integrity_score",
            "oos_reliability_score",
            "live_execution_quality_score",
        ):
            value = _finite(name, getattr(self, name))
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be in [0, 1]")

    @property
    def net_pnl(self) -> float:
        return float(self.gross_pnl - self.costs.total)

    @property
    def net_return(self) -> float:
        return self.net_pnl / self.capital

    @property
    def net_expectancy_per_trade(self) -> float:
        return self.net_pnl / self.trade_count

    @property
    def win_rate(self) -> float:
        return self.wins / self.trade_count

    @property
    def gross_return(self) -> float:
        return self.gross_pnl / self.capital

    @property
    def risk_adjusted_net_return(self) -> float:
        denominator = max(
            self.permanent_loss_fraction,
            self.max_drawdown_fraction,
            self.tail_loss_fraction,
            1e-12,
        )
        return self.net_return / denominator


@dataclass(frozen=True)
class ObjectiveAssessment:
    eligible: bool
    blockers: tuple[str, ...]
    net_pnl: float
    net_expectancy_per_trade: float
    risk_adjusted_net_return: float
    cost_breakdown: dict[str, float]
    rank_key: tuple[float, ...]


@dataclass(frozen=True)
class CapitalPreservationObjective:
    max_permanent_loss_fraction: float = 0.05
    max_drawdown_fraction: float = 0.20
    max_tail_loss_fraction: float = 0.10
    min_data_integrity_score: float = 0.99
    min_execution_integrity_score: float = 0.99
    min_oos_reliability_score: float = 0.80
    min_live_execution_quality_score: float = 0.80

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            value = _finite(name, value)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be in [0, 1]")

    def assess(self, evidence: ObjectiveEvidence) -> ObjectiveAssessment:
        blockers: list[str] = []
        if evidence.permanent_loss_fraction > self.max_permanent_loss_fraction:
            blockers.append("PERMANENT_LOSS_RISK_TOO_HIGH")
        if evidence.data_integrity_score < self.min_data_integrity_score:
            blockers.append("DATA_INTEGRITY_BELOW_THRESHOLD")
        if evidence.execution_integrity_score < self.min_execution_integrity_score:
            blockers.append("EXECUTION_INTEGRITY_BELOW_THRESHOLD")
        if evidence.max_drawdown_fraction > self.max_drawdown_fraction:
            blockers.append("MAX_DRAWDOWN_TOO_HIGH")
        if evidence.tail_loss_fraction > self.max_tail_loss_fraction:
            blockers.append("TAIL_LOSS_TOO_HIGH")
        if evidence.net_expectancy_per_trade <= 0:
            blockers.append("NET_EXPECTANCY_NOT_POSITIVE")
        if evidence.oos_reliability_score < self.min_oos_reliability_score:
            blockers.append("OOS_RELIABILITY_BELOW_THRESHOLD")
        if evidence.live_execution_quality_score < self.min_live_execution_quality_score:
            blockers.append("LIVE_EXECUTION_QUALITY_BELOW_THRESHOLD")

        eligible = not blockers
        # Safety/quality criteria intentionally dominate secondary vanity metrics.
        rank_key = (
            float(eligible),
            -evidence.permanent_loss_fraction,
            min(evidence.data_integrity_score, evidence.execution_integrity_score),
            -max(evidence.max_drawdown_fraction, evidence.tail_loss_fraction),
            evidence.net_expectancy_per_trade,
            evidence.oos_reliability_score,
            evidence.live_execution_quality_score,
            evidence.risk_adjusted_net_return,
            float(evidence.trade_count),
            evidence.win_rate,
            evidence.gross_return,
        )
        return ObjectiveAssessment(
            eligible=eligible,
            blockers=tuple(blockers),
            net_pnl=evidence.net_pnl,
            net_expectancy_per_trade=evidence.net_expectancy_per_trade,
            risk_adjusted_net_return=evidence.risk_adjusted_net_return,
            cost_breakdown=evidence.costs.as_dict(),
            rank_key=rank_key,
        )

    def select_best(self, candidates: list[ObjectiveEvidence]) -> int | None:
        assessed = [(index, self.assess(candidate)) for index, candidate in enumerate(candidates)]
        eligible = [(index, row) for index, row in assessed if row.eligible]
        if not eligible:
            return None
        return max(eligible, key=lambda item: item[1].rank_key)[0]
