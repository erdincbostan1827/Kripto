from __future__ import annotations

from decimal import Decimal

import pytest

from app.core.enums import OrderState
from app.exchange.models import OrderRecord, SymbolFilters
from scripts.external.binance_testnet_acceptance import TESTNET_URL, run_scenario


class FakeAdapter:
    def __init__(self, *, testnet=True, partial=True):
        self.testnet = testnet
        self.base_url = TESTNET_URL if testnet else "https://api.binance.com"
        self.partial = partial
        self.orders = []
        self._partial_id = None

    def get_symbol_filters(self, symbol):
        return SymbolFilters(Decimal("0.01"), Decimal("0.00001"), Decimal("0.00001"), Decimal("100"), Decimal("5"))

    def get_ticker(self, symbol):
        return {"price": "50000"}

    def get_order_book(self, symbol):
        return {
            "bids": [
                ["50000", "0.00010"],
                ["49999", "1.00000"],
            ]
        }

    def submit_order(self, intent):
        oid = str(len(self.orders) + 1)
        self.orders.append(intent)
        if intent.order_type == "MARKET":
            return OrderRecord(intent.intent_id, intent.account_id, intent.symbol, intent.side, intent.order_type, intent.quantity,
                               OrderState.FILLED, exchange_order_id=oid, filled_quantity=intent.quantity)
        if intent.price is not None and intent.price < Decimal("60000"):
            self._partial_id = oid
        return OrderRecord(intent.intent_id, intent.account_id, intent.symbol, intent.side, intent.order_type, intent.quantity,
                           OrderState.ACKNOWLEDGED, price=intent.price, exchange_order_id=oid)

    def cancel_order(self, symbol, order_id):
        intent = self.orders[int(order_id) - 1]
        return OrderRecord(intent.intent_id, intent.account_id, symbol, intent.side, intent.order_type, intent.quantity,
                           OrderState.CANCELLED, price=intent.price, exchange_order_id=order_id)

    def get_order(self, symbol, order_id=None, client_order_id=None):
        intent = self.orders[int(order_id) - 1]
        filled = intent.quantity / 2 if self.partial and order_id == self._partial_id else Decimal("0")
        state = OrderState.PARTIALLY_FILLED if filled else OrderState.ACKNOWLEDGED
        return OrderRecord(intent.intent_id, intent.account_id, symbol, intent.side, intent.order_type, intent.quantity,
                           state, price=intent.price, exchange_order_id=order_id, filled_quantity=filled)


def test_testnet_scenario_market_limit_cancel_and_partial_fill_pass():
    result = run_scenario(FakeAdapter(), symbol="BTCUSDT", max_notional=Decimal("15"),
                          partial_price=Decimal("50000"), poll_seconds=0.01)
    assert result["all_pass"] is True
    assert all(v["pass"] for v in result["checks"].values())


def test_partial_fill_is_mandatory_not_silently_skipped():
    result = run_scenario(FakeAdapter(), symbol="BTCUSDT", max_notional=Decimal("15"), partial_price=None)
    assert result["all_pass"] is False
    assert result["checks"]["partial_fill"]["status"] == "NOT_EXECUTED"


def test_live_endpoint_is_refused_even_with_adapter_contract():
    with pytest.raises(RuntimeError, match="TESTNET"):
        run_scenario(FakeAdapter(testnet=False), symbol="BTCUSDT", max_notional=Decimal("15"))


def test_minimum_notional_above_safety_cap_fails_closed():
    with pytest.raises(RuntimeError, match="safety cap"):
        run_scenario(FakeAdapter(), symbol="BTCUSDT", max_notional=Decimal("1"))
