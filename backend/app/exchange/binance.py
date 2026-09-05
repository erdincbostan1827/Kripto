from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timezone
import hashlib, hmac, time, urllib.parse
import httpx
from app.core.enums import OrderState
from .base import ExchangeAdapter, AmbiguousExecution, UnsupportedCapability, ExchangeRateLimited
from .models import *


class BinanceSpotAdapter(ExchangeAdapter):
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, testnet: bool = False, transport=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.base_url = self.TESTNET_URL if testnet else self.BASE_URL
        self.client = httpx.Client(base_url=self.base_url, timeout=10, transport=transport)
        self._info = None
        self.last_rate_limit_observation = {}

    @staticmethod
    def _decimal_param(value: Decimal) -> str:
        """Serialize Binance decimal parameters as plain fixed-point text, never exponent notation."""
        if not value.is_finite():
            raise ValueError("Binance decimal parameter must be finite")
        return format(value, "f")

    def _request(self, method, path, params=None, signed=False, mutation=False, api_key_only=False):
        params = dict(params or {})
        headers = {}
        if signed:
            if not self.api_key or not self.api_secret:
                raise PermissionError("credentials required")
            params["timestamp"] = int(time.time() * 1000)
            query = urllib.parse.urlencode(params)
            params["signature"] = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers["X-MBX-APIKEY"] = self.api_key
        elif api_key_only:
            if not self.api_key:
                raise PermissionError("API key required")
            headers["X-MBX-APIKEY"] = self.api_key
        try:
            response = self.client.request(method, path, params=params, headers=headers)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            if mutation:
                raise AmbiguousExecution("transport outcome unknown; reconcile by clientOrderId") from exc
            raise
        self.last_rate_limit_observation = self._parse_rate_limit_headers(response.headers)
        if response.status_code in {418, 429}:
            raise ExchangeRateLimited(
                f"Binance rate limit HTTP {response.status_code}",
                self.last_rate_limit_observation.get("RETRY-AFTER"),
            )
        if mutation and response.status_code >= 500:
            raise AmbiguousExecution("exchange 5xx; execution status unknown")
        response.raise_for_status()
        return response.json()


    @staticmethod
    def _parse_rate_limit_headers(headers):
        """Parse documented Binance rate-limit observations without assuming presence."""
        out = {}
        for key, value in headers.items():
            upper = key.upper()
            if upper.startswith("X-MBX-USED-WEIGHT-") or upper.startswith("X-MBX-ORDER-COUNT-"):
                try:
                    out[upper] = int(value)
                except (TypeError, ValueError):
                    out[upper] = value
            elif upper == "RETRY-AFTER":
                try:
                    out[upper] = int(value)
                except (TypeError, ValueError):
                    out[upper] = value
        return out

    def get_last_rate_limit_observation(self):
        return dict(self.last_rate_limit_observation)

    def get_adapter_manifest(self, symbol):
        snapshot = self.get_capability_snapshot(symbol)
        return {
            "adapter_version": "0.3.0-local-acceptance",
            "exchange": "BINANCE",
            "market_type": "SPOT",
            "api_family": "Binance Spot REST API v3",
            "documented_schema": "exchangeInfo + order/account REST contracts",
            "authentication_type": "API key + HMAC-SHA256 signed requests",
            "supported_endpoints": (
                "/api/v3/exchangeInfo", "/api/v3/ticker/price", "/api/v3/depth",
                "/api/v3/account", "/api/v3/openOrders", "/api/v3/order",
                "/api/v3/klines", "/api/v3/time",
            ),
            "limits_snapshot": tuple(self.get_rate_limits()),
            "filters_snapshot_version": snapshot["version"],
            "compatibility_evidence": "tests/integration/test_binance_contract.py",
        }

    def get_capability_snapshot(self, symbol):
        """Content-addressed runtime capability/filter snapshot for audit/revalidation."""
        import json
        raw = self._symbol(symbol)
        payload = {
            "exchange": "BINANCE",
            "market_type": "SPOT",
            "symbol": symbol,
            "status": raw.get("status"),
            "order_types": raw.get("orderTypes", []),
            "filters": raw.get("filters", []),
            "oco_allowed": raw.get("ocoAllowed", False),
            "stp_modes": raw.get("allowedSelfTradePreventionModes", []),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return {**payload, "version": hashlib.sha256(canonical.encode()).hexdigest()[:16], "source": "GET /api/v3/exchangeInfo"}

    def _exchange_info(self):
        if self._info is None:
            self._info = self._request("GET", "/api/v3/exchangeInfo")
        return self._info

    def get_exchange_info(self):
        return self._exchange_info()

    def get_ticker(self, symbol):
        return self._request("GET", "/api/v3/ticker/price", {"symbol": symbol})

    def get_order_book(self, symbol):
        return self._request("GET", "/api/v3/depth", {"symbol": symbol, "limit": 100})

    def get_balance(self):
        data = self._request("GET", "/api/v3/account", signed=True)
        return {x["asset"]: Decimal(x["free"]) + Decimal(x["locked"]) for x in data.get("balances", [])}

    def get_positions(self):
        return []

    def get_open_orders(self, symbol=None):
        params = {"symbol": symbol} if symbol else {}
        data = self._request("GET", "/api/v3/openOrders", params, signed=True)
        return [self._map_order(x) for x in data]

    def get_klines(self, symbol, interval, limit=500):
        return self._request("GET", "/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})

    def submit_order(self, intent):
        cap = self.get_capabilities(intent.symbol)
        order_type = intent.order_type.upper()
        mapping = {"MARKET": "market", "LIMIT": "limit", "STOP_LOSS_LIMIT": "stop", "TAKE_PROFIT_LIMIT": "take_profit"}
        capability = mapping.get(order_type)
        if capability is None or not getattr(cap, capability, False):
            raise UnsupportedCapability(order_type)
        params = {
            "symbol": intent.symbol,
            "side": intent.side,
            "type": order_type,
            "quantity": self._decimal_param(intent.quantity),
            "newClientOrderId": intent.client_order_id or intent.intent_id,
        }
        if intent.price is not None:
            params["price"] = self._decimal_param(intent.price)
            params["timeInForce"] = "GTC"
        if intent.stop_price is not None:
            params["stopPrice"] = self._decimal_param(intent.stop_price)
        return self._map_order(self._request("POST", "/api/v3/order", params, signed=True, mutation=True), fallback=intent)

    def cancel_order(self, symbol, order_id):
        return self._map_order(self._request("DELETE", "/api/v3/order", {"symbol": symbol, "orderId": order_id}, signed=True, mutation=True))

    def get_order(self, symbol, order_id=None, client_order_id=None):
        if not order_id and not client_order_id:
            raise ValueError("order_id or client_order_id required")
        params = {"symbol": symbol}
        params.update({"orderId": order_id} if order_id else {"origClientOrderId": client_order_id})
        return self._map_order(self._request("GET", "/api/v3/order", params, signed=True))

    def list_markets(self):
        return [x["symbol"] for x in self._exchange_info().get("symbols", []) if x.get("status") == "TRADING"]

    def _symbol(self, symbol):
        try:
            return next(x for x in self._exchange_info().get("symbols", []) if x.get("symbol") == symbol)
        except StopIteration as exc:
            raise KeyError(f"unknown Binance symbol: {symbol}") from exc

    def get_symbol_filters(self, symbol):
        filters = {f["filterType"]: f for f in self._symbol(symbol).get("filters", [])}
        try:
            price_filter = filters["PRICE_FILTER"]
            lot_filter = filters["LOT_SIZE"]
        except KeyError as exc:
            raise UnsupportedCapability(f"required symbol filter missing: {exc.args[0]}") from exc
        notional_filter = filters.get("NOTIONAL") or filters.get("MIN_NOTIONAL", {})
        return SymbolFilters(
            Decimal(price_filter["tickSize"]),
            Decimal(lot_filter["stepSize"]),
            Decimal(lot_filter["minQty"]),
            Decimal(lot_filter["maxQty"]),
            Decimal(notional_filter.get("minNotional", "0")),
            Decimal(notional_filter["maxNotional"]) if notional_filter.get("maxNotional") else None,
            int(self._symbol(symbol).get("maxNumOrders")) if self._symbol(symbol).get("maxNumOrders") is not None else None,
        )

    def get_capabilities(self, symbol):
        symbol_info = self._symbol(symbol)
        types = set(symbol_info.get("orderTypes", []))
        filters = {x.get("filterType") for x in symbol_info.get("filters", [])}
        stp = tuple(symbol_info.get("allowedSelfTradePreventionModes", []))
        return Capabilities(
            market="MARKET" in types,
            limit="LIMIT" in types,
            stop=bool(types & {"STOP_LOSS", "STOP_LOSS_LIMIT"}),
            take_profit=bool(types & {"TAKE_PROFIT", "TAKE_PROFIT_LIMIT"}),
            trailing_stop="TRAILING_DELTA" in filters,
            oco=bool(symbol_info.get("ocoAllowed", False)),
            post_only=False,
            reduce_only=False,
            client_order_id=True,
            testnet=True,
            private_stream=True,
            stp_modes=stp,
        )

    def get_symbol_metadata(self, symbol):
        raw = self._symbol(symbol)
        return {
            "exchange": "BINANCE",
            "market_type": "SPOT",
            "symbol": raw.get("symbol"),
            "base_asset": raw.get("baseAsset"),
            "quote_asset": raw.get("quoteAsset"),
            "status": raw.get("status"),
            "permissions": raw.get("permissions", []),
            "filters": raw.get("filters", []),
            "order_types": raw.get("orderTypes", []),
            "oco_allowed": bool(raw.get("ocoAllowed", False)),
            "stp_modes": raw.get("allowedSelfTradePreventionModes", []),
            "source": "GET /api/v3/exchangeInfo",
        }

    def get_asset_metadata(self, asset):
        asset = asset.upper()
        related = [s for s in self._exchange_info().get("symbols", []) if s.get("baseAsset") == asset or s.get("quoteAsset") == asset]
        return {
            "asset": asset,
            "trading": any(s.get("status") == "TRADING" for s in related),
            "symbols": [s.get("symbol") for s in related],
            "source": "GET /api/v3/exchangeInfo",
            "limitations": ["chain/network metadata is not inferred from ticker identity"],
        }

    def get_scheduled_listings(self):
        if self.testnet:
            raise UnsupportedCapability("scheduled_listings_testnet")
        data = self._request("GET", "/sapi/v1/spot/open-symbol-list", api_key_only=True)
        items = data if isinstance(data, list) else [data]
        return [
            {
                "open_time": int(item["openTime"]),
                "symbols": tuple(item.get("symbols", [])),
                "source": "GET /sapi/v1/spot/open-symbol-list",
            }
            for item in items
            if item and item.get("openTime") is not None
        ]

    def get_server_time(self):
        return datetime.fromtimestamp(self._request("GET", "/api/v3/time")["serverTime"] / 1000, timezone.utc)

    def get_rate_limits(self):
        return self._exchange_info().get("rateLimits", [])

    def get_exchange_status(self):
        return {"status": "ONLINE", "server_time": self.get_server_time().isoformat(), "market_type": "SPOT", "testnet": self.testnet}

    def _map_order(self, x, fallback=None):
        required = ("symbol", "status", "type", "side", "origQty")
        if fallback is None:
            missing = [key for key in required if x.get(key) is None]
            if missing:
                raise ValueError("required order field missing: " + ",".join(missing))
        state = {
            "NEW": OrderState.ACKNOWLEDGED,
            "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED,
            "FILLED": OrderState.FILLED,
            "CANCELED": OrderState.CANCELLED,
            "REJECTED": OrderState.REJECTED,
            "EXPIRED": OrderState.FAILED,
        }.get(x.get("status"), OrderState.UNKNOWN)
        return OrderRecord(
            x.get("clientOrderId") or (fallback.intent_id if fallback else ""),
            fallback.account_id if fallback else "binance",
            x.get("symbol") or fallback.symbol,
            x.get("side") or fallback.side,
            x.get("type") or fallback.order_type,
            Decimal(x.get("origQty") or fallback.quantity),
            state,
            Decimal(x["price"]) if x.get("price") else fallback.price if fallback else None,
            Decimal(x["stopPrice"]) if x.get("stopPrice") else fallback.stop_price if fallback else None,
            str(x.get("orderId")) if x.get("orderId") is not None else None,
            x.get("clientOrderId"),
            Decimal(x.get("executedQty", "0")),
        )