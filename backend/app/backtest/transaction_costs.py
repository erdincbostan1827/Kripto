from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

D = Decimal
LiquidityRole = Literal["maker", "taker"]
Side = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class FeeSchedule:
    """Exchange/account fee schedule expressed in basis points.

    Separate maker/taker and buy/sell fields avoid silently assuming a single
    symmetric fee. Values may be negative to represent an exchange rebate.
    """

    maker_buy_bps: D = D("0")
    maker_sell_bps: D = D("0")
    taker_buy_bps: D = D("10")
    taker_sell_bps: D = D("10")

    def bps_for(self, side: Side, liquidity_role: LiquidityRole) -> D:
        normalized_side = side.upper()
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError(f"unsupported side: {side}")
        if liquidity_role not in {"maker", "taker"}:
            raise ValueError(f"unsupported liquidity role: {liquidity_role}")
        return getattr(self, f"{liquidity_role}_{normalized_side.lower()}_bps")


@dataclass(frozen=True)
class CostBreakdown:
    reference_price: D
    executed_price: D
    quantity: D
    fee: D
    half_spread_cost: D
    slippage_cost: D
    market_impact_cost: D
    total_cost: D
    fee_bps: D
    spread_bps: D
    slippage_bps: D
    market_impact_bps: D


@dataclass(frozen=True)
class TransactionCostModel:
    """Fail-closed adverse transaction-cost model for backtest/PAPER analysis.

    `spread_bps` is the full quoted spread, so a marketable fill pays half on
    each side. Slippage and market impact are always adverse. Market impact is
    a deterministic linear participation-rate model capped by
    `max_market_impact_bps`; callers can leave `daily_notional=None` to disable
    impact rather than invent liquidity.
    """

    fees: FeeSchedule = FeeSchedule()
    spread_bps: D = D("5")
    slippage_bps: D = D("5")
    impact_coefficient_bps: D = D("25")
    max_market_impact_bps: D = D("100")

    def __post_init__(self) -> None:
        for name in (
            "spread_bps",
            "slippage_bps",
            "impact_coefficient_bps",
            "max_market_impact_bps",
        ):
            if D(getattr(self, name)) < 0:
                raise ValueError(f"{name} must be non-negative")

    def market_impact_bps(self, notional: D, daily_notional: D | None) -> D:
        notional = D(notional)
        if notional < 0:
            raise ValueError("notional must be non-negative")
        if daily_notional is None:
            return D("0")
        daily_notional = D(daily_notional)
        if daily_notional <= 0:
            raise ValueError("daily_notional must be positive when provided")
        participation = notional / daily_notional
        return min(self.max_market_impact_bps, self.impact_coefficient_bps * participation)

    def estimate_market_fill(
        self,
        *,
        side: Side,
        reference_price: D,
        quantity: D,
        liquidity_role: LiquidityRole = "taker",
        daily_notional: D | None = None,
    ) -> CostBreakdown:
        side = side.upper()  # type: ignore[assignment]
        if side not in {"BUY", "SELL"}:
            raise ValueError(f"unsupported side: {side}")
        price = D(reference_price)
        qty = D(quantity)
        if price <= 0:
            raise ValueError("reference_price must be positive")
        if qty <= 0:
            raise ValueError("quantity must be positive")

        reference_notional = price * qty
        impact_bps = self.market_impact_bps(reference_notional, daily_notional)
        half_spread_bps = self.spread_bps / D("2")
        adverse_bps = half_spread_bps + self.slippage_bps + impact_bps
        direction = D("1") if side == "BUY" else D("-1")
        executed_price = price * (D("1") + direction * adverse_bps / D("10000"))
        fee_bps = self.fees.bps_for(side, liquidity_role)  # type: ignore[arg-type]
        executed_notional = executed_price * qty
        fee = executed_notional * fee_bps / D("10000")

        half_spread_cost = reference_notional * half_spread_bps / D("10000")
        slippage_cost = reference_notional * self.slippage_bps / D("10000")
        market_impact_cost = reference_notional * impact_bps / D("10000")
        total_cost = half_spread_cost + slippage_cost + market_impact_cost + fee

        return CostBreakdown(
            reference_price=price,
            executed_price=executed_price,
            quantity=qty,
            fee=fee,
            half_spread_cost=half_spread_cost,
            slippage_cost=slippage_cost,
            market_impact_cost=market_impact_cost,
            total_cost=total_cost,
            fee_bps=fee_bps,
            spread_bps=self.spread_bps,
            slippage_bps=self.slippage_bps,
            market_impact_bps=impact_bps,
        )

    def round_trip_cost_bps(
        self,
        *,
        buy_role: LiquidityRole = "taker",
        sell_role: LiquidityRole = "taker",
        participation_rate: D = D("0"),
    ) -> D:
        participation_rate = D(participation_rate)
        if participation_rate < 0:
            raise ValueError("participation_rate must be non-negative")
        impact = min(
            self.max_market_impact_bps,
            self.impact_coefficient_bps * participation_rate,
        )
        return (
            self.spread_bps
            + self.slippage_bps * D("2")
            + impact * D("2")
            + self.fees.bps_for("BUY", buy_role)
            + self.fees.bps_for("SELL", sell_role)
        )
