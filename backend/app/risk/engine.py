from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.money import decimal, normalize_quantity


@dataclass(frozen=True)
class RiskLimits:
    risk_per_trade: Decimal = Decimal("0.0025")
    max_daily_loss: Decimal = Decimal("0.02")
    max_weekly_loss: Decimal = Decimal("0.05")
    max_drawdown: Decimal = Decimal("0.10")
    max_portfolio_exposure: Decimal = Decimal("0.50")
    max_single_asset_exposure: Decimal = Decimal("0.15")
    max_quote_asset_exposure: Decimal = Decimal("0.85")
    max_volatility_adjusted_exposure: Decimal = Decimal("0.60")
    max_open_positions: int = 6
    max_consecutive_losses: int = 5


@dataclass(frozen=True)
class RiskSnapshot:
    equity: Decimal
    daily_pnl: Decimal = Decimal("0")
    weekly_pnl: Decimal = Decimal("0")
    drawdown: Decimal = Decimal("0")
    gross_exposure: Decimal = Decimal("0")
    asset_exposure: Decimal = Decimal("0")
    quote_asset_exposure: Decimal = Decimal("0")
    volatility_adjusted_exposure: Decimal = Decimal("0")
    open_positions: int = 0
    consecutive_losses: int = 0


def effective_loss_per_unit(
    entry,
    stop,
    entry_fee_bps=10,
    exit_fee_bps=10,
    spread_bps=5,
    entry_slippage_bps=5,
    stop_slippage_bps=15,
    funding_borrow_bps=0,
):
    entry, stop = decimal(entry), decimal(stop)
    base = abs(entry - stop)
    bps = sum(
        map(
            Decimal,
            map(
                str,
                (
                    entry_fee_bps,
                    exit_fee_bps,
                    spread_bps,
                    entry_slippage_bps,
                    stop_slippage_bps,
                    funding_borrow_bps,
                ),
            ),
        )
    )
    return base + entry * bps / Decimal(10000)


def size_position(equity, entry, stop, step, risk_fraction):
    equity, entry, stop, step, risk_fraction = map(decimal, (equity, entry, stop, step, risk_fraction))
    loss = effective_loss_per_unit(entry, stop)
    if loss <= 0:
        raise ValueError("invalid loss distance")
    return normalize_quantity(equity * risk_fraction / loss, step)


def validate_portfolio(snapshot: RiskSnapshot, limits: RiskLimits):
    reasons: list[str] = []
    if snapshot.equity <= 0:
        return ["INVALID_EQUITY"]
    if -snapshot.daily_pnl >= snapshot.equity * limits.max_daily_loss:
        reasons.append("DAILY_LOSS")
    if -snapshot.weekly_pnl >= snapshot.equity * limits.max_weekly_loss:
        reasons.append("WEEKLY_LOSS")
    if snapshot.drawdown >= limits.max_drawdown:
        reasons.append("MAX_DRAWDOWN")
    if snapshot.gross_exposure >= snapshot.equity * limits.max_portfolio_exposure:
        reasons.append("PORTFOLIO_EXPOSURE")
    if snapshot.asset_exposure >= snapshot.equity * limits.max_single_asset_exposure:
        reasons.append("SINGLE_ASSET_EXPOSURE")
    if snapshot.quote_asset_exposure >= snapshot.equity * limits.max_quote_asset_exposure:
        reasons.append("QUOTE_ASSET_EXPOSURE")
    if snapshot.volatility_adjusted_exposure >= snapshot.equity * limits.max_volatility_adjusted_exposure:
        reasons.append("VOLATILITY_ADJUSTED_EXPOSURE")
    if snapshot.open_positions >= limits.max_open_positions:
        reasons.append("MAX_POSITIONS")
    if snapshot.consecutive_losses >= limits.max_consecutive_losses:
        reasons.append("CONSECUTIVE_LOSSES")
    return reasons
