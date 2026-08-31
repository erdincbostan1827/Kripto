from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MarketTypeRiskSnapshot:
    market_type: str
    gross_exposure: Decimal
    equity: Decimal
    largest_symbol_exposure: Decimal
    quote_asset_exposure: Decimal
    liquidation_distance_pct: Decimal | None = None
    maintenance_margin_ratio: Decimal | None = None
    leverage: Decimal | None = None


@dataclass(frozen=True)
class MarketTypeRiskDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_market_type_risk(
    snapshot: MarketTypeRiskSnapshot,
    *,
    max_gross_exposure_ratio: Decimal,
    max_single_symbol_ratio: Decimal,
    max_quote_asset_ratio: Decimal,
    min_liquidation_distance_pct: Decimal = Decimal("0.10"),
    max_maintenance_margin_ratio: Decimal = Decimal("0.70"),
    max_leverage: Decimal = Decimal("3"),
) -> MarketTypeRiskDecision:
    reasons: list[str] = []
    if snapshot.equity <= 0:
        return MarketTypeRiskDecision(False, ("NON_POSITIVE_EQUITY",))
    gross_ratio = snapshot.gross_exposure / snapshot.equity
    single_ratio = snapshot.largest_symbol_exposure / snapshot.equity
    quote_ratio = snapshot.quote_asset_exposure / snapshot.equity
    if gross_ratio > max_gross_exposure_ratio:
        reasons.append("GROSS_EXPOSURE_LIMIT")
    if single_ratio > max_single_symbol_ratio:
        reasons.append("SINGLE_SYMBOL_CONCENTRATION")
    if quote_ratio > max_quote_asset_ratio:
        reasons.append("QUOTE_ASSET_CONCENTRATION")

    market_type = snapshot.market_type.upper()
    derivative_fields = (snapshot.liquidation_distance_pct, snapshot.maintenance_margin_ratio, snapshot.leverage)
    if market_type == "SPOT":
        if any(value is not None for value in derivative_fields):
            reasons.append("SPOT_DERIVATIVE_SEMANTICS_FORBIDDEN")
    elif market_type in {"FUTURES", "PERPETUAL", "MARGIN"}:
        if any(value is None for value in derivative_fields):
            reasons.append("DERIVATIVE_RISK_FIELDS_REQUIRED")
        else:
            assert snapshot.liquidation_distance_pct is not None
            assert snapshot.maintenance_margin_ratio is not None
            assert snapshot.leverage is not None
            if snapshot.liquidation_distance_pct < min_liquidation_distance_pct:
                reasons.append("LIQUIDATION_BUFFER_TOO_LOW")
            if snapshot.maintenance_margin_ratio > max_maintenance_margin_ratio:
                reasons.append("MAINTENANCE_MARGIN_TOO_HIGH")
            if snapshot.leverage > max_leverage:
                reasons.append("LEVERAGE_LIMIT")
    else:
        reasons.append("UNSUPPORTED_MARKET_TYPE")
    return MarketTypeRiskDecision(not reasons, tuple(reasons))
