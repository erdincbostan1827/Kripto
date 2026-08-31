from __future__ import annotations

import json
import os
import sys
import time
import uuid
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.exchange.binance import BinanceSpotAdapter  # noqa: E402
from app.exchange.models import OrderIntent  # noqa: E402
from app.core.enums import OrderState  # noqa: E402

TESTNET_URL = "https://testnet.binance.vision"


def _step_quantize(value: Decimal, step: Decimal, *, up: bool = False) -> Decimal:
    if step <= 0:
        raise ValueError("step must be positive")
    units = value / step
    rounding = ROUND_UP if up else ROUND_DOWN
    return units.to_integral_value(rounding=rounding) * step


def _safe_quantity(adapter: BinanceSpotAdapter, symbol: str, max_notional: Decimal) -> tuple[Decimal, Decimal]:
    filters = adapter.get_symbol_filters(symbol)
    price = Decimal(str(adapter.get_ticker(symbol)["price"]))
    if price <= 0:
        raise RuntimeError("invalid ticker price")
    target_notional = max(filters.min_notional * Decimal("1.10"), price * filters.min_qty)
    if target_notional > max_notional:
        raise RuntimeError(f"minimum executable notional {target_notional} exceeds safety cap {max_notional}")
    quantity = _step_quantize(target_notional / price, filters.step_size, up=True)
    if quantity < filters.min_qty or quantity > filters.max_qty:
        raise RuntimeError("derived quantity outside LOT_SIZE bounds")
    return quantity, price


def _intent(symbol: str, side: str, order_type: str, quantity: Decimal, *, price: Decimal | None = None) -> OrderIntent:
    ident = "accept-" + uuid.uuid4().hex[:20]
    return OrderIntent(
        intent_id=ident,
        account_id="binance-testnet-acceptance",
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        client_order_id=ident,
    )


def run_scenario(adapter: BinanceSpotAdapter, *, symbol: str, max_notional: Decimal,
                 partial_price: Decimal | None = None, poll_seconds: float = 8.0) -> dict:
    if not adapter.testnet or adapter.base_url.rstrip("/") != TESTNET_URL:
        raise RuntimeError("refusing to execute: adapter is not pinned to Binance Spot TESTNET")

    quantity, ticker_price = _safe_quantity(adapter, symbol, max_notional)
    filters = adapter.get_symbol_filters(symbol)
    result: dict = {"symbol": symbol, "max_notional": str(max_notional), "ticker_price": str(ticker_price),
                    "quantity": str(quantity), "endpoint": TESTNET_URL, "checks": {}}

    market = adapter.submit_order(_intent(symbol, "BUY", "MARKET", quantity))
    market_ok = market.state in {OrderState.FILLED, OrderState.PARTIALLY_FILLED} and market.filled_quantity > 0
    result["checks"]["market_order"] = {"pass": market_ok, "state": market.state.value,
                                           "filled_quantity": str(market.filled_quantity), "order_id": market.exchange_order_id}

    # Place a deliberately non-marketable SELL well above ticker, then verify cancellation.
    limit_price = _step_quantize(ticker_price * Decimal("1.50"), filters.tick_size, up=True)
    limit_order = adapter.submit_order(_intent(symbol, "SELL", "LIMIT", quantity, price=limit_price))
    limit_ok = limit_order.exchange_order_id is not None and limit_order.state in {OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED}
    result["checks"]["limit_order"] = {"pass": limit_ok, "state": limit_order.state.value,
                                          "price": str(limit_price), "order_id": limit_order.exchange_order_id}
    cancel = adapter.cancel_order(symbol, limit_order.exchange_order_id or "")
    cancel_ok = cancel.state == OrderState.CANCELLED
    result["checks"]["cancel"] = {"pass": cancel_ok, "state": cancel.state.value, "order_id": cancel.exchange_order_id}

    # Partial fill is intentionally explicit because it is market-dependent. The operator supplies
    # a TESTNET-only probe price; PASS is granted only when the exchange reports 0 < filled < quantity.
    partial_ok = False
    if partial_price is None:
        result["checks"]["partial_fill"] = {"pass": False, "status": "NOT_EXECUTED", "reason": "BINANCE_TESTNET_PARTIAL_PRICE_REQUIRED"}
    else:
        probe_price = _step_quantize(partial_price, filters.tick_size)
        probe = adapter.submit_order(_intent(symbol, "SELL", "LIMIT", quantity, price=probe_price))
        deadline = time.monotonic() + max(0.1, poll_seconds)
        current = probe
        while time.monotonic() < deadline:
            current = adapter.get_order(symbol, order_id=probe.exchange_order_id)
            if current.filled_quantity > 0:
                break
            time.sleep(min(0.5, poll_seconds / 4 if poll_seconds > 0 else 0.1))
        partial_ok = current.filled_quantity > 0 and current.filled_quantity < current.quantity
        result["checks"]["partial_fill"] = {
            "pass": partial_ok, "state": current.state.value, "filled_quantity": str(current.filled_quantity),
            "quantity": str(current.quantity), "order_id": current.exchange_order_id,
        }
        if current.state not in {OrderState.FILLED, OrderState.CANCELLED}:
            adapter.cancel_order(symbol, current.exchange_order_id or "")

    result["all_pass"] = bool(market_ok and limit_ok and cancel_ok and partial_ok)
    return result


def main() -> int:
    key = os.getenv("BINANCE_TESTNET_API_KEY")
    secret = os.getenv("BINANCE_TESTNET_API_SECRET")
    if not key or not secret:
        print("BLOCKED: Binance TESTNET credentials are missing; values are never printed.")
        return 2
    if os.getenv("BINANCE_TESTNET_EXECUTE") != "YES":
        print("BLOCKED: set BINANCE_TESTNET_EXECUTE=YES to explicitly permit TESTNET-only order acceptance.")
        return 2

    symbol = os.getenv("BINANCE_TESTNET_SYMBOL", "BTCUSDT").strip().upper()
    max_notional = Decimal(os.getenv("BINANCE_TESTNET_MAX_NOTIONAL", "15"))
    partial_raw = os.getenv("BINANCE_TESTNET_PARTIAL_PRICE")
    partial_price = Decimal(partial_raw) if partial_raw else None
    adapter = BinanceSpotAdapter(api_key=key, api_secret=secret, testnet=True)
    try:
        result = run_scenario(adapter, symbol=symbol, max_notional=max_notional, partial_price=partial_price)
    except Exception as exc:
        print(json.dumps({"all_pass": False, "error_type": type(exc).__name__, "error": str(exc), "endpoint": TESTNET_URL}, sort_keys=True))
        return 2
    finally:
        adapter.client.close()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
