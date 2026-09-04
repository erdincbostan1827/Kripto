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

from app.core.enums import OrderState  # noqa: E402
from app.exchange.binance import BinanceSpotAdapter  # noqa: E402
from app.exchange.models import OrderIntent, SymbolFilters  # noqa: E402

TESTNET_URL = "https://testnet.binance.vision"
AUTO_VALUE = "AUTO"
ACQUISITION_CAP_UTILIZATION = Decimal("0.90")
PARTIAL_CAP_UTILIZATION = Decimal("0.85")
AUTO_PARTIAL_MAX_RATIO = Decimal("0.70")
AUTO_QUOTE_PRIORITY = ("USDT", "USDC", "FDUSD", "BNB", "BTC", "ETH")


def _step_quantize(value: Decimal, step: Decimal, *, up: bool = False) -> Decimal:
    if step <= 0:
        raise ValueError("step must be positive")
    units = value / step
    rounding = ROUND_UP if up else ROUND_DOWN
    return units.to_integral_value(rounding=rounding) * step


def _effective_notional_cap(filters: SymbolFilters, max_notional: Decimal) -> Decimal:
    if max_notional <= 0:
        raise RuntimeError("max_notional must be positive")
    exchange_cap = filters.max_notional
    if exchange_cap is not None and exchange_cap > 0:
        return min(max_notional, exchange_cap)
    return max_notional


def _bounded_quantity_for_price(
    filters: SymbolFilters,
    price: Decimal,
    max_notional: Decimal,
    *,
    utilization: Decimal,
) -> Decimal:
    if price <= 0:
        raise RuntimeError("price must be positive")
    if utilization <= 0 or utilization >= 1:
        raise RuntimeError("notional utilization must be >0 and <1")

    cap = _effective_notional_cap(filters, max_notional)
    budget = cap * utilization
    minimum_target = max(filters.min_notional * Decimal("1.10"), price * filters.min_qty)
    if minimum_target > budget:
        raise RuntimeError(
            f"minimum executable notional {minimum_target} exceeds safety cap bounded budget {budget}"
        )

    quantity = _step_quantize(budget / price, filters.step_size)
    max_quantity = _step_quantize(filters.max_qty, filters.step_size)
    quantity = min(quantity, max_quantity)
    if quantity < filters.min_qty:
        raise RuntimeError("bounded quantity is below LOT_SIZE minimum")

    notional = quantity * price
    if notional < filters.min_notional:
        minimum_quantity = _step_quantize(
            filters.min_notional / price,
            filters.step_size,
            up=True,
        )
        if minimum_quantity < filters.min_qty:
            minimum_quantity = filters.min_qty
        if minimum_quantity > filters.max_qty or minimum_quantity * price > cap:
            raise RuntimeError("minimum executable quantity exceeds safety cap")
        quantity = minimum_quantity
        notional = quantity * price

    if notional > cap:
        raise RuntimeError(f"derived notional {notional} exceeds safety cap {cap}")
    return quantity


def _safe_quantity(
    adapter: BinanceSpotAdapter,
    symbol: str,
    max_notional: Decimal,
) -> tuple[Decimal, Decimal]:
    filters = adapter.get_symbol_filters(symbol)
    price = Decimal(str(adapter.get_ticker(symbol)["price"]))
    if price <= 0:
        raise RuntimeError("invalid ticker price")
    quantity = _bounded_quantity_for_price(
        filters,
        price,
        max_notional,
        utilization=ACQUISITION_CAP_UTILIZATION,
    )
    return quantity, price


def _executable_bid_quantity_from_book(book: dict, probe_price: Decimal) -> Decimal:
    executable = Decimal("0")
    for raw_price, raw_quantity in book.get("bids", []):
        bid_price = Decimal(str(raw_price))
        if bid_price < probe_price:
            break
        executable += Decimal(str(raw_quantity))
    return executable


def _executable_bid_quantity(
    adapter: BinanceSpotAdapter,
    symbol: str,
    probe_price: Decimal,
) -> Decimal:
    return _executable_bid_quantity_from_book(adapter.get_order_book(symbol), probe_price)


def _auto_probe_for_symbol(
    adapter: BinanceSpotAdapter,
    symbol: str,
    max_notional: Decimal,
    *,
    acquired_quantity: Decimal | None = None,
) -> dict | None:
    filters = adapter.get_symbol_filters(symbol)
    book = adapter.get_order_book(symbol)
    bids = book.get("bids", [])
    if not bids:
        return None

    best_bid = Decimal(str(bids[0][0]))
    if best_bid <= 0:
        return None
    probe_price = _step_quantize(best_bid, filters.tick_size)
    probe_quantity = _bounded_quantity_for_price(
        filters,
        probe_price,
        max_notional,
        utilization=PARTIAL_CAP_UTILIZATION,
    )
    if acquired_quantity is not None and probe_quantity > acquired_quantity:
        return None

    executable = _executable_bid_quantity_from_book(book, probe_price)
    if executable <= 0 or executable >= probe_quantity:
        return None
    ratio = executable / probe_quantity
    if ratio > AUTO_PARTIAL_MAX_RATIO:
        return None
    return {
        "price": probe_price,
        "quantity": probe_quantity,
        "executable_bid_quantity": executable,
        "ratio": ratio,
    }


def _auto_symbol_sort_key(symbol_info: dict) -> tuple[int, str]:
    quote = str(symbol_info.get("quoteAsset", "")).upper()
    try:
        quote_rank = AUTO_QUOTE_PRIORITY.index(quote)
    except ValueError:
        quote_rank = len(AUTO_QUOTE_PRIORITY)
    return quote_rank, str(symbol_info.get("symbol", ""))


def _select_auto_target(
    adapter: BinanceSpotAdapter,
    max_notional: Decimal,
) -> tuple[str, dict]:
    symbols = [
        item
        for item in adapter.get_exchange_info().get("symbols", [])
        if item.get("status") == "TRADING"
        and "MARKET" in set(item.get("orderTypes", []))
        and "LIMIT" in set(item.get("orderTypes", []))
    ]
    symbols.sort(key=_auto_symbol_sort_key)

    for item in symbols:
        symbol = str(item.get("symbol", "")).upper()
        if not symbol:
            continue
        try:
            probe = _auto_probe_for_symbol(adapter, symbol, max_notional)
            if probe is None:
                continue
            acquisition_quantity, ticker_price = _safe_quantity(adapter, symbol, max_notional)
            if probe["quantity"] > acquisition_quantity:
                continue
            filters = adapter.get_symbol_filters(symbol)
            limit_price = _step_quantize(
                ticker_price * Decimal("1.50"),
                filters.tick_size,
                up=True,
            )
            _bounded_quantity_for_price(
                filters,
                limit_price,
                max_notional,
                utilization=PARTIAL_CAP_UTILIZATION,
            )
            return symbol, probe
        except (KeyError, RuntimeError, ValueError):
            continue
    raise RuntimeError(
        "no fresh Binance Spot TESTNET symbol satisfies the cap-bounded partial-fill preflight"
    )


def _intent(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    *,
    price: Decimal | None = None,
) -> OrderIntent:
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


def run_scenario(
    adapter: BinanceSpotAdapter,
    *,
    symbol: str,
    max_notional: Decimal,
    partial_price: Decimal | None = None,
    poll_seconds: float = 8.0,
    auto_select_symbol: bool = False,
    auto_partial_price: bool = False,
) -> dict:
    if not adapter.testnet or adapter.base_url.rstrip("/") != TESTNET_URL:
        raise RuntimeError("refusing to execute: adapter is not pinned to Binance Spot TESTNET")
    if auto_select_symbol and not auto_partial_price:
        raise RuntimeError("AUTO symbol selection requires AUTO partial-price selection")

    requested_symbol = symbol
    initial_auto_probe: dict | None = None
    if auto_select_symbol:
        symbol, initial_auto_probe = _select_auto_target(adapter, max_notional)

    quantity, ticker_price = _safe_quantity(adapter, symbol, max_notional)
    filters = adapter.get_symbol_filters(symbol)
    result: dict = {
        "requested_symbol": requested_symbol,
        "symbol": symbol,
        "symbol_selection_mode": "AUTO" if auto_select_symbol else "EXPLICIT",
        "partial_price_mode": "AUTO" if auto_partial_price else "EXPLICIT",
        "max_notional": str(max_notional),
        "ticker_price": str(ticker_price),
        "quantity": str(quantity),
        "endpoint": TESTNET_URL,
        "checks": {},
    }

    market_ok = False
    limit_ok = False
    cancel_ok = False
    partial_ok = False

    if auto_partial_price:
        initial_auto_probe = initial_auto_probe or _auto_probe_for_symbol(
            adapter,
            symbol,
            max_notional,
            acquired_quantity=quantity,
        )
        if initial_auto_probe is None or initial_auto_probe["quantity"] > quantity:
            raise RuntimeError(
                "AUTO partial-fill preflight rejected current TESTNET order book before acquisition"
            )
        partial_price = initial_auto_probe["price"]

    if partial_price is None:
        result["checks"]["partial_fill"] = {"pass": False, "status": "NOT_EXECUTED", "reason": "BINANCE_TESTNET_PARTIAL_PRICE_REQUIRED"}
    else:
        if auto_partial_price:
            if initial_auto_probe is None:
                raise RuntimeError("AUTO partial-fill preflight result unexpectedly missing")
            probe_price = partial_price
            probe_quantity = initial_auto_probe["quantity"]
            executable_bid_quantity = initial_auto_probe["executable_bid_quantity"]
        else:
            probe_price = _step_quantize(partial_price, filters.tick_size)
            probe_quantity = _bounded_quantity_for_price(
                filters,
                probe_price,
                max_notional,
                utilization=PARTIAL_CAP_UTILIZATION,
            )
            if probe_quantity > quantity:
                raise RuntimeError(
                    "partial-fill probe quantity exceeds the planned TESTNET acquisition quantity"
                )
            executable_bid_quantity = _executable_bid_quantity(adapter, symbol, probe_price)
            if executable_bid_quantity <= 0 or executable_bid_quantity >= probe_quantity:
                raise RuntimeError(
                    "partial-fill preflight rejected current order book: "
                    f"executable_bid_quantity={executable_bid_quantity}, "
                    f"probe_quantity={probe_quantity}"
                )

        market = adapter.submit_order(_intent(symbol, "BUY", "MARKET", quantity))
        market_ok = (
            market.state in {OrderState.FILLED, OrderState.PARTIALLY_FILLED}
            and market.filled_quantity >= quantity
        )
        result["checks"]["market_order"] = {
            "pass": market_ok,
            "state": market.state.value,
            "filled_quantity": str(market.filled_quantity),
            "quantity": str(quantity),
            "order_id": market.exchange_order_id,
        }
        if not market_ok:
            result["checks"]["limit_order"] = {
                "pass": market_ok,
                "status": "NOT_EXECUTED",
            }
            result["checks"]["cancel"] = {
                "pass": market_ok,
                "status": "NOT_EXECUTED",
            }
            result["checks"]["partial_fill"] = {
                "pass": market_ok,
                "status": "NOT_EXECUTED",
                "reason": "MARKET_ACQUISITION_INCOMPLETE",
            }
            result["all_pass"] = market_ok
            return result

        # Use a smaller quantity at the deliberately high cancellation price so every
        # submitted order remains inside the same max-notional safety boundary.
        limit_price = _step_quantize(
            ticker_price * Decimal("1.50"),
            filters.tick_size,
            up=True,
        )
        limit_quantity = _bounded_quantity_for_price(
            filters,
            limit_price,
            max_notional,
            utilization=PARTIAL_CAP_UTILIZATION,
        )
        limit_order = adapter.submit_order(
            _intent(symbol, "SELL", "LIMIT", limit_quantity, price=limit_price)
        )
        limit_ok = limit_order.exchange_order_id is not None and limit_order.state in {
            OrderState.ACKNOWLEDGED,
            OrderState.PARTIALLY_FILLED,
        }
        result["checks"]["limit_order"] = {
            "pass": limit_ok,
            "state": limit_order.state.value,
            "quantity": str(limit_quantity),
            "price": str(limit_price),
            "order_id": limit_order.exchange_order_id,
        }
        cancel = adapter.cancel_order(symbol, limit_order.exchange_order_id or "")
        cancel_ok = cancel.state == OrderState.CANCELLED
        result["checks"]["cancel"] = {
            "pass": cancel_ok,
            "state": cancel.state.value,
            "order_id": cancel.exchange_order_id,
        }

        # Refresh the AUTO probe immediately before the partial SELL to minimize the
        # market-race window. Explicit prices are revalidated but never silently changed.
        if auto_partial_price:
            fresh_probe = _auto_probe_for_symbol(
                adapter,
                symbol,
                max_notional,
                acquired_quantity=market.filled_quantity,
            )
            if fresh_probe is None:
                result["checks"]["partial_fill"] = {
                    "pass": partial_ok,
                    "status": "NOT_EXECUTED",
                    "reason": "AUTO_PARTIAL_PREFLIGHT_STALE",
                    "initial_probe_price": str(probe_price),
                    "initial_executable_bid_quantity": str(executable_bid_quantity),
                }
                result["all_pass"] = partial_ok
                return result
            probe_price = fresh_probe["price"]
            probe_quantity = fresh_probe["quantity"]
            executable_bid_quantity = fresh_probe["executable_bid_quantity"]
        else:
            executable_bid_quantity = _executable_bid_quantity(adapter, symbol, probe_price)
            if (
                executable_bid_quantity <= 0
                or executable_bid_quantity >= probe_quantity
                or probe_quantity > market.filled_quantity
            ):
                result["checks"]["partial_fill"] = {
                    "pass": partial_ok,
                    "status": "NOT_EXECUTED",
                    "reason": "EXPLICIT_PARTIAL_PREFLIGHT_STALE",
                    "probe_price": str(probe_price),
                    "preflight_executable_bid_quantity": str(executable_bid_quantity),
                    "quantity": str(probe_quantity),
                }
                result["all_pass"] = partial_ok
                return result

        # PASS is still based only on the real exchange reporting 0 < filled < quantity.
        probe = adapter.submit_order(
            _intent(symbol, "SELL", "LIMIT", probe_quantity, price=probe_price)
        )
        deadline = time.monotonic() + max(0.1, poll_seconds)
        current = probe
        while time.monotonic() < deadline:
            current = adapter.get_order(symbol, order_id=probe.exchange_order_id)
            if current.filled_quantity > 0:
                break
            time.sleep(min(0.5, poll_seconds / 4 if poll_seconds > 0 else 0.1))

        partial_ok = current.filled_quantity > 0 and current.filled_quantity < current.quantity
        result["checks"]["partial_fill"] = {
            "pass": partial_ok,
            "state": current.state.value,
            "filled_quantity": str(current.filled_quantity),
            "quantity": str(current.quantity),
            "probe_price": str(probe_price),
            "preflight_executable_bid_quantity": str(executable_bid_quantity),
            "order_id": current.exchange_order_id,
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
        print(
            "BLOCKED: set BINANCE_TESTNET_EXECUTE=YES to explicitly permit TESTNET-only order acceptance."
        )
        return 2

    symbol_raw = os.getenv("BINANCE_TESTNET_SYMBOL", "BTCUSDT").strip().upper()
    max_notional = Decimal(os.getenv("BINANCE_TESTNET_MAX_NOTIONAL", "15"))
    partial_raw = os.getenv("BINANCE_TESTNET_PARTIAL_PRICE")
    auto_select_symbol = symbol_raw == AUTO_VALUE
    auto_partial_price = bool(
        partial_raw is not None and partial_raw.strip().upper() == AUTO_VALUE
    )
    partial_price = (
        None
        if auto_partial_price or not partial_raw
        else Decimal(partial_raw)
    )
    adapter = BinanceSpotAdapter(api_key=key, api_secret=secret, testnet=True)
    try:
        result = run_scenario(
            adapter,
            symbol=symbol_raw,
            max_notional=max_notional,
            partial_price=partial_price,
            auto_select_symbol=auto_select_symbol,
            auto_partial_price=auto_partial_price,
        )
    except Exception as exc:
        print(json.dumps({"all_pass": False, "error_type": type(exc).__name__, "error": str(exc), "endpoint": TESTNET_URL}, sort_keys=True))
        return 2
    finally:
        adapter.client.close()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())