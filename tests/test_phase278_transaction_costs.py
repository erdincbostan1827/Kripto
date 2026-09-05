from decimal import Decimal

import pytest

from app.backtest.transaction_costs import FeeSchedule, TransactionCostModel

D = Decimal


def test_taker_market_fill_is_adverse_and_includes_fee() -> None:
    model = TransactionCostModel(
        fees=FeeSchedule(taker_buy_bps=D("10"), taker_sell_bps=D("12")),
        spread_bps=D("6"),
        slippage_bps=D("4"),
        impact_coefficient_bps=D("20"),
        max_market_impact_bps=D("50"),
    )
    buy = model.estimate_market_fill(
        side="BUY",
        reference_price=D("100"),
        quantity=D("2"),
        daily_notional=D("2000"),
    )
    sell = model.estimate_market_fill(
        side="SELL",
        reference_price=D("100"),
        quantity=D("2"),
        daily_notional=D("2000"),
    )

    assert buy.executed_price > D("100")
    assert sell.executed_price < D("100")
    assert buy.fee > 0
    assert sell.fee > buy.fee
    assert buy.market_impact_bps == D("2")
    assert buy.total_cost > buy.fee


def test_maker_and_taker_fees_are_not_silently_collapsed() -> None:
    fees = FeeSchedule(
        maker_buy_bps=D("1"),
        maker_sell_bps=D("2"),
        taker_buy_bps=D("9"),
        taker_sell_bps=D("11"),
    )
    assert fees.bps_for("BUY", "maker") == D("1")
    assert fees.bps_for("SELL", "maker") == D("2")
    assert fees.bps_for("BUY", "taker") == D("9")
    assert fees.bps_for("SELL", "taker") == D("11")


def test_round_trip_cost_bps_includes_spread_both_slippages_fees_and_impact() -> None:
    model = TransactionCostModel(
        fees=FeeSchedule(taker_buy_bps=D("10"), taker_sell_bps=D("12")),
        spread_bps=D("6"),
        slippage_bps=D("4"),
        impact_coefficient_bps=D("20"),
        max_market_impact_bps=D("50"),
    )
    # 10% participation -> 2 bps impact on each leg.
    assert model.round_trip_cost_bps(participation_rate=D("0.1")) == D("40.0")


def test_market_impact_is_capped() -> None:
    model = TransactionCostModel(
        impact_coefficient_bps=D("1000"),
        max_market_impact_bps=D("30"),
    )
    assert model.market_impact_bps(D("1000"), D("1000")) == D("30")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"reference_price": D("0"), "quantity": D("1")}, "reference_price"),
        ({"reference_price": D("1"), "quantity": D("0")}, "quantity"),
    ],
)
def test_invalid_fill_inputs_fail_closed(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TransactionCostModel().estimate_market_fill(side="BUY", **kwargs)


def test_invalid_liquidity_denominator_fails_closed() -> None:
    with pytest.raises(ValueError, match="daily_notional"):
        TransactionCostModel().market_impact_bps(D("100"), D("0"))
