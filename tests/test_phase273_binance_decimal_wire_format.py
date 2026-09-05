from decimal import Decimal

import httpx
import pytest

from app.exchange.binance import BinanceSpotAdapter
from app.exchange.models import OrderIntent
from scripts.external.binance_testnet_acceptance_hardened import _market_order_test


def _exchange_info() -> dict:
    return {
        "symbols": [
            {
                "symbol": "TINYUSDT",
                "status": "TRADING",
                "orderTypes": ["MARKET", "LIMIT", "STOP_LOSS_LIMIT"],
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.00000001"},
                    {
                        "filterType": "LOT_SIZE",
                        "stepSize": "0.00000001",
                        "minQty": "0.00000001",
                        "maxQty": "1000000",
                    },
                    {"filterType": "MIN_NOTIONAL", "minNotional": "0"},
                ],
            }
        ]
    }


def test_decimal_param_never_uses_scientific_notation() -> None:
    assert BinanceSpotAdapter._decimal_param(Decimal("1E-8")) == "0.00000001"
    assert BinanceSpotAdapter._decimal_param(Decimal("6E+4")) == "60000"
    assert "E" not in BinanceSpotAdapter._decimal_param(Decimal("1.25E-7"))
    with pytest.raises(ValueError, match="finite"):
        BinanceSpotAdapter._decimal_param(Decimal("NaN"))


def test_submit_order_uses_fixed_point_wire_values() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/exchangeInfo"):
            return httpx.Response(200, json=_exchange_info())
        if request.url.path.endswith("/order") and request.method == "POST":
            seen.update(dict(request.url.params))
            return httpx.Response(
                200,
                json={
                    "symbol": "TINYUSDT",
                    "orderId": 1,
                    "clientOrderId": seen["newClientOrderId"],
                    "status": "NEW",
                    "type": seen["type"],
                    "side": seen["side"],
                    "origQty": seen["quantity"],
                    "executedQty": "0",
                    "price": seen.get("price", "0"),
                    "stopPrice": seen.get("stopPrice", "0"),
                },
            )
        return httpx.Response(404, json={"msg": "unexpected"})

    adapter = BinanceSpotAdapter(
        "key",
        "secret",
        testnet=True,
        transport=httpx.MockTransport(handler),
    )
    adapter.submit_order(
        OrderIntent(
            intent_id="tiny-1",
            account_id="acct",
            symbol="TINYUSDT",
            side="BUY",
            order_type="STOP_LOSS_LIMIT",
            quantity=Decimal("1E-8"),
            price=Decimal("2E-8"),
            stop_price=Decimal("3E-8"),
        )
    )

    assert seen["quantity"] == "0.00000001"
    assert seen["price"] == "0.00000002"
    assert seen["stopPrice"] == "0.00000003"
    assert all("E" not in seen[key].upper() for key in ("quantity", "price", "stopPrice"))


def test_testnet_order_test_uses_same_fixed_point_serializer() -> None:
    captured: dict[str, str] = {}

    class Adapter:
        _decimal_param = staticmethod(BinanceSpotAdapter._decimal_param)

        def _request(self, method, path, params, signed=False):
            assert method == "POST"
            assert path == "/api/v3/order/test"
            assert signed is True
            captured.update(params)
            return {}

    assert _market_order_test(Adapter(), "TINYUSDT", Decimal("1E-8")) is True
    assert captured["quantity"] == "0.00000001"
    assert "E" not in captured["quantity"].upper()
