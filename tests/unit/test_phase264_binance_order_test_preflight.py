from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest

from scripts.external import binance_testnet_acceptance as base
from scripts.external import binance_testnet_acceptance_hardened as hardened


class FakeAdapter:
    def __init__(self) -> None:
        self.test_calls: list[str] = []
        self.submit_calls = 0
        self.book_calls: list[str] = []

    def get_exchange_info(self):
        return {
            "symbols": [
                {
                    "symbol": "AAAUSDT",
                    "quoteAsset": "USDT",
                    "status": "TRADING",
                    "orderTypes": ["MARKET", "LIMIT"],
                },
                {
                    "symbol": "BBBUSDT",
                    "quoteAsset": "USDT",
                    "status": "TRADING",
                    "orderTypes": ["MARKET", "LIMIT"],
                },
            ]
        }

    def get_symbol_filters(self, symbol: str):
        return SimpleNamespace(tick_size=Decimal("0.01"))

    def get_order_book(self, symbol: str):
        self.book_calls.append(symbol)
        return {"bids": [["1", "100"]], "asks": [["1", "100"]]}

    def _request(self, method, path, params=None, signed=False):
        assert method == "POST"
        assert path == "/api/v3/order/test"
        assert signed is True
        assert params["side"] == "BUY"
        assert params["type"] == "MARKET"
        assert params["quantity"] == "2"
        symbol = params["symbol"]
        self.test_calls.append(symbol)
        if symbol == "AAAUSDT":
            request = httpx.Request("POST", "https://testnet.binance.vision/api/v3/order/test")
            response = httpx.Response(
                400,
                request=request,
                json={"code": -1013, "msg": "Filter failure: MARKET_LOT_SIZE"},
            )
            raise httpx.HTTPStatusError("bad market lot", request=request, response=response)
        return {}

    def submit_order(self, intent):
        self.submit_calls += 1
        raise AssertionError("AUTO preflight must never submit a real order")


def test_auto_selector_skips_market_lot_rejection_without_real_submit(monkeypatch):
    adapter = FakeAdapter()
    probe = {
        "price": Decimal("1"),
        "quantity": Decimal("1"),
        "executable_bid_quantity": Decimal("0.5"),
        "ratio": Decimal("0.5"),
    }

    monkeypatch.setattr(base, "_spendable_notional_cap", lambda max_notional, balance: Decimal("15"))
    monkeypatch.setattr(base, "_auto_probe_for_symbol", lambda adapter, symbol, cap: dict(probe))
    monkeypatch.setattr(base, "_safe_quantity", lambda adapter, symbol, cap: (Decimal("2"), Decimal("1")))
    monkeypatch.setattr(base, "_step_quantize", lambda value, step, up=False: value)
    monkeypatch.setattr(base, "_bounded_quantity_for_price", lambda *args, **kwargs: Decimal("1"))

    selected = hardened._select_auto_target(
        adapter,
        Decimal("15"),
        {"USDT": Decimal("100")},
    )

    assert selected[0] == "BBBUSDT"
    assert selected[3] == "USDT"
    assert adapter.book_calls == ["AAAUSDT", "BBBUSDT"]
    assert adapter.test_calls == ["AAAUSDT", "BBBUSDT"]
    assert adapter.submit_calls == 0


def test_market_order_test_returns_false_on_binance_filter_rejection():
    adapter = FakeAdapter()
    assert hardened._market_order_test(adapter, "AAAUSDT", Decimal("2")) is False
    assert adapter.test_calls == ["AAAUSDT"]
    assert adapter.submit_calls == 0


def test_market_order_test_reraises_non_filter_http_error():
    adapter = FakeAdapter()

    def reject_auth(method, path, params=None, signed=False):
        request = httpx.Request("POST", "https://testnet.binance.vision/api/v3/order/test")
        response = httpx.Response(
            401,
            request=request,
            json={"code": -2015, "msg": "Invalid API-key, IP, or permissions for action."},
        )
        raise httpx.HTTPStatusError("auth rejected", request=request, response=response)

    adapter._request = reject_auth  # type: ignore[method-assign]

    with pytest.raises(httpx.HTTPStatusError):
        hardened._market_order_test(adapter, "AAAUSDT", Decimal("2"))
    assert adapter.submit_calls == 0
