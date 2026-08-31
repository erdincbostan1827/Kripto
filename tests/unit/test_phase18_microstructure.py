from decimal import Decimal
import pytest

from app.microstructure.features import BookLevel, TradePrint, extract_microstructure_features


def test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum():
    result = extract_microstructure_features(
        bids=[BookLevel(Decimal("99"), Decimal("10")), BookLevel(Decimal("98"), Decimal("5"))],
        asks=[BookLevel(Decimal("101"), Decimal("5")), BookLevel(Decimal("102"), Decimal("5"))],
        trades=[TradePrint(Decimal("101"), Decimal("4"), "BUY"), TradePrint(Decimal("99"), Decimal("1"), "SELL")],
        previous_cvd=Decimal("2"), sweep_notional_threshold=Decimal("100000"), vacuum_depth_threshold=Decimal("1"),
    )
    assert result.spread_bps == Decimal("200")
    assert result.order_book_imbalance == Decimal("0.2")
    assert result.depth_imbalance == result.order_book_imbalance
    assert result.microprice > Decimal("100")
    assert result.buy_volume == Decimal("4")
    assert result.sell_volume == Decimal("1")
    assert result.volume_delta == Decimal("3")
    assert result.cumulative_volume_delta == Decimal("5")
    assert result.order_flow_momentum == Decimal("0.6")


def test_microstructure_detects_abnormal_sweep_and_liquidity_vacuum():
    result = extract_microstructure_features(
        bids=[BookLevel(Decimal("99.9"), Decimal("1"))],
        asks=[BookLevel(Decimal("100.1"), Decimal("1"))],
        trades=[TradePrint(Decimal("100.1"), Decimal("1000"), "BUY")],
        sweep_notional_threshold=Decimal("50000"), vacuum_depth_threshold=Decimal("10"),
    )
    assert result.abnormal_sweep
    assert result.liquidity_vacuum
    assert result.order_flow_momentum == Decimal("1")


def test_microstructure_fails_closed_on_invalid_book_or_aggressor_side():
    with pytest.raises(ValueError, match="both bid and ask"):
        extract_microstructure_features(bids=[], asks=[BookLevel(Decimal("1"), Decimal("1"))], trades=[])
    with pytest.raises(ValueError, match="aggressor"):
        extract_microstructure_features(
            bids=[BookLevel(Decimal("1"), Decimal("1"))], asks=[BookLevel(Decimal("2"), Decimal("1"))],
            trades=[TradePrint(Decimal("1.5"), Decimal("1"), "UNKNOWN")],
        )
