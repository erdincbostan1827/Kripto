from decimal import Decimal

from scripts.external.binance_testnet_acceptance_hardened import _market_buy_depth_sufficient


class BookAdapter:
    def __init__(self, asks):
        self.asks = asks

    def get_order_book(self, symbol):
        assert symbol == "TESTUSDT"
        return {"bids": [], "asks": self.asks}


def test_market_buy_depth_requires_full_quantity_coverage() -> None:
    adapter = BookAdapter([["1.00", "2"], ["1.01", "3"]])
    assert _market_buy_depth_sufficient(adapter, "TESTUSDT", Decimal("5")) is True
    assert _market_buy_depth_sufficient(adapter, "TESTUSDT", Decimal("5.0001")) is False


def test_market_buy_depth_ignores_invalid_and_nonpositive_levels() -> None:
    adapter = BookAdapter(
        [
            ["1.00", "0"],
            ["1.01", "-4"],
            ["1.02", "not-a-number"],
            ["1.03"],
            ["1.04", "1.25"],
        ]
    )
    assert _market_buy_depth_sufficient(adapter, "TESTUSDT", Decimal("1.25")) is True
    assert _market_buy_depth_sufficient(adapter, "TESTUSDT", Decimal("1.26")) is False


def test_market_buy_depth_rejects_nonpositive_planned_quantity() -> None:
    adapter = BookAdapter([["1.00", "100"]])
    assert _market_buy_depth_sufficient(adapter, "TESTUSDT", Decimal("0")) is False
    assert _market_buy_depth_sufficient(adapter, "TESTUSDT", Decimal("-1")) is False
