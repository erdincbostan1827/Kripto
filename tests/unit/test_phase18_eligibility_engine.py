from decimal import Decimal

from app.universe.eligibility_engine import EligibilityEngine, EligibilityPolicy, EligibilitySnapshot


def _snapshot(**overrides):
    values = dict(
        symbol="BTCUSDT", market_type="SPOT", base_asset="BTC", quote_asset="USDT", trading_active=True,
        listing_age_days=1000, history_bars=1000, quote_volume_24h=Decimal("100000000"),
        rolling_median_volume=Decimal("1000000"), spread_bps=Decimal("3"), depth_notional=Decimal("1000000"),
        expected_slippage_bps=Decimal("4"), trade_count_24h=100000, stale_tick_ratio=Decimal("0"),
        missing_candle_ratio=Decimal("0"), abnormal_gap_ratio=Decimal("0"), exchange_filters_ok=True,
        quote_asset_risk_ok=True, venue_healthy=True,
    )
    values.update(overrides)
    return EligibilitySnapshot(**values)


def test_eligibility_engine_accepts_complete_liquid_healthy_symbol():
    result = EligibilityEngine(EligibilityPolicy()).evaluate(_snapshot())
    assert result.eligible and result.reasons == ()


def test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue():
    policy = EligibilityPolicy(allowed_base_assets=frozenset({"BTC"}))
    result = EligibilityEngine(policy).evaluate(_snapshot(
        market_type="PERPETUAL", base_asset="ETH", quote_asset="TRY", trading_active=False,
        listing_age_days=1, history_bars=10, quote_volume_24h=Decimal("1"), rolling_median_volume=Decimal("1"),
        spread_bps=Decimal("100"), depth_notional=Decimal("1"), expected_slippage_bps=Decimal("100"),
        trade_count_24h=1, stale_tick_ratio=Decimal("0.5"), missing_candle_ratio=Decimal("0.5"),
        abnormal_gap_ratio=Decimal("0.5"), exchange_filters_ok=False, quote_asset_risk_ok=False, venue_healthy=False,
    ))
    expected = {
        "SYMBOL_NOT_TRADING", "MARKET_TYPE_UNSUPPORTED", "BASE_ASSET_NOT_ALLOWED", "QUOTE_ASSET_NOT_ALLOWED",
        "LISTING_TOO_NEW", "INSUFFICIENT_HISTORY", "LOW_24H_QUOTE_VOLUME", "LOW_ROLLING_MEDIAN_VOLUME",
        "SPREAD_TOO_WIDE", "INSUFFICIENT_BOOK_DEPTH", "SLIPPAGE_TOO_HIGH", "TRADE_COUNT_TOO_LOW",
        "STALE_TICK_RATIO_HIGH", "MISSING_CANDLE_RATIO_HIGH", "ABNORMAL_GAP_RATIO_HIGH",
        "EXCHANGE_FILTER_MISMATCH", "QUOTE_ASSET_RISK_BLOCK", "VENUE_UNHEALTHY",
    }
    assert not result.eligible
    assert expected == set(result.reasons)


def test_eligibility_policy_uses_relative_bps_ratio_and_notional_thresholds():
    policy = EligibilityPolicy(max_spread_bps=Decimal("15"), max_expected_slippage_bps=Decimal("20"), max_stale_tick_ratio=Decimal("0.02"))
    result = EligibilityEngine(policy).evaluate(_snapshot(spread_bps=Decimal("15"), expected_slippage_bps=Decimal("20"), stale_tick_ratio=Decimal("0.02")))
    assert result.eligible
