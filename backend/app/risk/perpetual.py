from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PerpetualRiskSnapshot:
    symbol: str
    leverage: Decimal
    liquidation_distance_pct: Decimal
    maintenance_margin_ratio: Decimal
    margin_ratio: Decimal
    funding_rate: Decimal
    funding_timestamp_ms: int
    expected_funding_cost: Decimal
    mark_price: Decimal
    index_price: Decimal
    open_interest: Decimal
    liquidation_spike_ratio: Decimal
    reduce_only: bool
    position_reducing: bool


@dataclass(frozen=True)
class PerpetualRiskLimits:
    max_leverage: Decimal
    leverage_per_symbol: dict[str, Decimal]
    min_liquidation_distance_pct: Decimal
    max_maintenance_margin_ratio: Decimal
    max_margin_ratio: Decimal
    max_abs_funding_rate: Decimal
    max_expected_funding_cost: Decimal
    max_mark_index_divergence_pct: Decimal
    max_open_interest: Decimal
    max_liquidation_spike_ratio: Decimal
    max_funding_age_ms: int


@dataclass(frozen=True)
class PerpetualRiskDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_perpetual_risk(snapshot: PerpetualRiskSnapshot, limits: PerpetualRiskLimits, *, now_ms: int) -> PerpetualRiskDecision:
    reasons: list[str] = []
    symbol = snapshot.symbol.upper()
    symbol_max = limits.leverage_per_symbol.get(symbol, limits.max_leverage)
    effective_max = min(limits.max_leverage, symbol_max)
    if snapshot.leverage <= 0 or snapshot.leverage > effective_max:
        reasons.append("LEVERAGE_LIMIT")
    if snapshot.liquidation_distance_pct < limits.min_liquidation_distance_pct:
        reasons.append("LIQUIDATION_BUFFER_TOO_LOW")
    if snapshot.maintenance_margin_ratio < 0 or snapshot.maintenance_margin_ratio > limits.max_maintenance_margin_ratio:
        reasons.append("MAINTENANCE_MARGIN_TOO_HIGH")
    if snapshot.margin_ratio < 0 or snapshot.margin_ratio > limits.max_margin_ratio:
        reasons.append("MARGIN_RATIO_TOO_HIGH")
    if abs(snapshot.funding_rate) > limits.max_abs_funding_rate:
        reasons.append("FUNDING_RATE_LIMIT")
    if snapshot.funding_timestamp_ms <= 0 or now_ms - snapshot.funding_timestamp_ms > limits.max_funding_age_ms:
        reasons.append("FUNDING_DATA_STALE")
    if snapshot.expected_funding_cost < 0 or snapshot.expected_funding_cost > limits.max_expected_funding_cost:
        reasons.append("EXPECTED_FUNDING_COST_LIMIT")
    if snapshot.mark_price <= 0 or snapshot.index_price <= 0:
        reasons.append("INVALID_MARK_INDEX_PRICE")
    else:
        divergence = abs(snapshot.mark_price - snapshot.index_price) / snapshot.index_price
        if divergence > limits.max_mark_index_divergence_pct:
            reasons.append("MARK_INDEX_DIVERGENCE")
    if snapshot.open_interest < 0 or snapshot.open_interest > limits.max_open_interest:
        reasons.append("OPEN_INTEREST_LIMIT")
    if snapshot.liquidation_spike_ratio < 0 or snapshot.liquidation_spike_ratio > limits.max_liquidation_spike_ratio:
        reasons.append("LIQUIDATION_SPIKE")
    if snapshot.reduce_only and not snapshot.position_reducing:
        reasons.append("REDUCE_ONLY_WOULD_INCREASE_POSITION")
    return PerpetualRiskDecision(not reasons, tuple(reasons))
