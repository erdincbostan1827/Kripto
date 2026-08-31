from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping

ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class OptimizerPolicy:
    """Fail-closed portfolio optimizer policy.

    The default deliberately avoids an unconstrained mean-variance solution.
    It clips single-name weights, forbids shorting unless explicitly enabled,
    and retains a cash/risk reserve.
    """

    max_single_asset_weight: Decimal = Decimal("0.20")
    max_gross_weight: Decimal = Decimal("0.85")
    allow_short: bool = False
    min_expected_edge_bps: Decimal = Decimal("0")

    def validate(self) -> "OptimizerPolicy":
        if not (ZERO < self.max_single_asset_weight <= ONE):
            raise ValueError("max_single_asset_weight must be in (0,1]")
        if not (ZERO < self.max_gross_weight <= ONE):
            raise ValueError("max_gross_weight must be in (0,1]")
        if self.max_single_asset_weight > self.max_gross_weight:
            raise ValueError("single-asset cap cannot exceed gross cap")
        if not self.min_expected_edge_bps.is_finite():
            raise ValueError("min_expected_edge_bps must be finite")
        return self


@dataclass(frozen=True)
class OptimizedPortfolio:
    weights: dict[str, Decimal]
    cash_weight: Decimal
    gross_weight: Decimal
    blocked: tuple[str, ...]


def constrained_edge_optimizer(
    expected_edge_bps: Mapping[str, Decimal],
    *,
    policy: OptimizerPolicy = OptimizerPolicy(),
) -> OptimizedPortfolio:
    policy.validate()
    clean: dict[str, Decimal] = {}
    blocked: list[str] = []
    for symbol, edge in expected_edge_bps.items():
        edge = Decimal(edge)
        if not edge.is_finite():
            blocked.append(f"{symbol}:NON_FINITE_EDGE")
            continue
        if edge <= policy.min_expected_edge_bps and not policy.allow_short:
            blocked.append(f"{symbol}:NON_POSITIVE_EDGE")
            continue
        clean[symbol] = abs(edge) if policy.allow_short else max(ZERO, edge)

    if not clean or sum(clean.values(), ZERO) <= ZERO:
        return OptimizedPortfolio({}, ONE, ZERO, tuple(sorted(blocked)))

    total_score = sum(clean.values(), ZERO)
    tentative = {
        symbol: min(policy.max_single_asset_weight, policy.max_gross_weight * score / total_score)
        for symbol, score in clean.items()
    }
    gross = sum(tentative.values(), ZERO)
    if gross > policy.max_gross_weight:
        scale = policy.max_gross_weight / gross
        tentative = {symbol: weight * scale for symbol, weight in tentative.items()}
        gross = sum(tentative.values(), ZERO)
    cash = ONE - gross
    return OptimizedPortfolio(tentative, cash, gross, tuple(sorted(blocked)))
