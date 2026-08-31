from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

D = Decimal


@dataclass(frozen=True)
class EligibilityPolicy:
    supported_market_types: frozenset[str] = frozenset({"SPOT"})
    allowed_base_assets: frozenset[str] | None = None
    allowed_quote_assets: frozenset[str] = frozenset({"USDT", "USDC"})
    min_listing_age_days: int = 30
    min_history_bars: int = 250
    min_quote_volume_24h: Decimal = D("5000000")
    min_rolling_median_volume: Decimal = D("100000")
    max_spread_bps: Decimal = D("20")
    min_depth_notional: Decimal = D("100000")
    max_expected_slippage_bps: Decimal = D("25")
    min_trade_count_24h: int = 1000
    max_stale_tick_ratio: Decimal = D("0.01")
    max_missing_candle_ratio: Decimal = D("0.01")
    max_abnormal_gap_ratio: Decimal = D("0.01")


@dataclass(frozen=True)
class EligibilitySnapshot:
    symbol: str
    market_type: str
    base_asset: str
    quote_asset: str
    trading_active: bool
    listing_age_days: int
    history_bars: int
    quote_volume_24h: Decimal
    rolling_median_volume: Decimal
    spread_bps: Decimal
    depth_notional: Decimal
    expected_slippage_bps: Decimal
    trade_count_24h: int
    stale_tick_ratio: Decimal
    missing_candle_ratio: Decimal
    abnormal_gap_ratio: Decimal
    exchange_filters_ok: bool
    quote_asset_risk_ok: bool
    venue_healthy: bool


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    reasons: tuple[str, ...]


class EligibilityEngine:
    """Multi-asset fail-closed eligibility filter using bps/notional/ratio based limits."""

    def __init__(self, policy: EligibilityPolicy) -> None:
        self.policy = policy

    def evaluate(self, x: EligibilitySnapshot) -> EligibilityDecision:
        p = self.policy
        reasons: list[str] = []
        if not x.trading_active:
            reasons.append("SYMBOL_NOT_TRADING")
        if x.market_type.upper() not in p.supported_market_types:
            reasons.append("MARKET_TYPE_UNSUPPORTED")
        if p.allowed_base_assets is not None and x.base_asset.upper() not in p.allowed_base_assets:
            reasons.append("BASE_ASSET_NOT_ALLOWED")
        if x.quote_asset.upper() not in p.allowed_quote_assets:
            reasons.append("QUOTE_ASSET_NOT_ALLOWED")
        if x.listing_age_days < p.min_listing_age_days:
            reasons.append("LISTING_TOO_NEW")
        if x.history_bars < p.min_history_bars:
            reasons.append("INSUFFICIENT_HISTORY")
        if x.quote_volume_24h < p.min_quote_volume_24h:
            reasons.append("LOW_24H_QUOTE_VOLUME")
        if x.rolling_median_volume < p.min_rolling_median_volume:
            reasons.append("LOW_ROLLING_MEDIAN_VOLUME")
        if x.spread_bps > p.max_spread_bps:
            reasons.append("SPREAD_TOO_WIDE")
        if x.depth_notional < p.min_depth_notional:
            reasons.append("INSUFFICIENT_BOOK_DEPTH")
        if x.expected_slippage_bps > p.max_expected_slippage_bps:
            reasons.append("SLIPPAGE_TOO_HIGH")
        if x.trade_count_24h < p.min_trade_count_24h:
            reasons.append("TRADE_COUNT_TOO_LOW")
        if x.stale_tick_ratio > p.max_stale_tick_ratio:
            reasons.append("STALE_TICK_RATIO_HIGH")
        if x.missing_candle_ratio > p.max_missing_candle_ratio:
            reasons.append("MISSING_CANDLE_RATIO_HIGH")
        if x.abnormal_gap_ratio > p.max_abnormal_gap_ratio:
            reasons.append("ABNORMAL_GAP_RATIO_HIGH")
        if not x.exchange_filters_ok:
            reasons.append("EXCHANGE_FILTER_MISMATCH")
        if not x.quote_asset_risk_ok:
            reasons.append("QUOTE_ASSET_RISK_BLOCK")
        if not x.venue_healthy:
            reasons.append("VENUE_UNHEALTHY")
        return EligibilityDecision(not reasons, tuple(reasons))
