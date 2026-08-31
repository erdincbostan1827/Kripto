from __future__ import annotations
from abc import ABC, abstractmethod
from .models import OrderIntent, OrderRecord, Capabilities, SymbolFilters


class UnsupportedCapability(RuntimeError):
    """Raised when the venue does not advertise a requested capability."""


class AmbiguousExecution(RuntimeError):
    """Raised when an order mutation outcome cannot be determined safely."""


class ExchangeRateLimited(RuntimeError):
    """Raised when the venue reports a rate-limit boundary."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ExchangeAdapter(ABC):
    @abstractmethod
    def get_ticker(self, symbol: str): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_order_book(self, symbol: str): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_balance(self): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_positions(self): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_open_orders(self, symbol: str | None = None): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_klines(self, symbol: str, interval: str, limit: int = 500): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def submit_order(self, intent: OrderIntent) -> OrderRecord: raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str) -> OrderRecord: raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_order(self, symbol: str, order_id: str | None = None, client_order_id: str | None = None) -> OrderRecord | None: raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def list_markets(self): raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_symbol_filters(self, symbol: str) -> SymbolFilters: raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_capabilities(self, symbol: str) -> Capabilities: raise RuntimeError("abstract ExchangeAdapter method")
    @abstractmethod
    def get_server_time(self): raise RuntimeError("abstract ExchangeAdapter method")

    def create_market_order(self, **kwargs):
        return self.submit_order(OrderIntent(order_type="MARKET", **kwargs))

    def create_limit_order(self, **kwargs):
        return self.submit_order(OrderIntent(order_type="LIMIT", **kwargs))

    def create_stop_order(self, **kwargs):
        if not self.get_capabilities(kwargs["symbol"]).stop:
            raise UnsupportedCapability("stop")
        return self.submit_order(OrderIntent(order_type="STOP_LOSS_LIMIT", **kwargs))

    def create_take_profit_order(self, **kwargs):
        if not self.get_capabilities(kwargs["symbol"]).take_profit:
            raise UnsupportedCapability("take_profit")
        return self.submit_order(OrderIntent(order_type="TAKE_PROFIT_LIMIT", **kwargs))

    def cancel_all_orders(self, symbol: str):
        return [self.cancel_order(symbol, o.exchange_order_id or "") for o in self.get_open_orders(symbol)]

    def get_exchange_info(self):
        return {"markets": self.list_markets(), "rate_limits": self.get_rate_limits()}

    def get_symbol_metadata(self, symbol: str):
        return {
            "symbol": symbol,
            "trading_status": self.get_trading_status(symbol),
            "filters": self.get_symbol_filters(symbol),
            "capabilities": self.get_capabilities(symbol),
        }

    def get_asset_metadata(self, asset: str):
        symbols = [s for s in self.list_markets() if asset.upper() in s]
        return {"asset": asset.upper(), "symbols": symbols, "source": "derived_market_list"}

    def get_scheduled_listings(self):
        raise UnsupportedCapability("scheduled_listings")

    def get_trading_status(self, symbol: str):
        return {"symbol": symbol, "tradable": symbol in self.list_markets()}

    def get_rate_limits(self):
        return {}

    def get_exchange_status(self):
        return {"status": "ONLINE"}
