from __future__ import annotations

import sys
import uuid
from decimal import Decimal
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.external import binance_testnet_acceptance as base  # noqa: E402


def _is_candidate_filter_rejection(exc: httpx.HTTPStatusError) -> bool:
    """Return true only for Binance candidate-specific filter rejections."""
    try:
        payload = exc.response.json()
    except (ValueError, TypeError):
        return False
    if not isinstance(payload, dict):
        return False
    code = payload.get("code")
    message = str(payload.get("msg", ""))
    return code == -1013 and message.startswith("Filter failure:")


def _market_order_test(adapter, symbol: str, quantity: Decimal) -> bool:
    """Ask Binance TESTNET to validate the exact MARKET quantity without creating an order."""
    request = getattr(adapter, "_request", None)
    decimal_param = getattr(adapter, "_decimal_param", None)
    if request is None or decimal_param is None:
        raise RuntimeError("Binance adapter does not expose the signed fixed-point order-test contract")
    client_order_id = "accept-test-" + uuid.uuid4().hex[:16]
    try:
        request(
            "POST",
            "/api/v3/order/test",
            {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quantity": decimal_param(quantity),
                "newClientOrderId": client_order_id,
            },
            signed=True,
        )
    except httpx.HTTPStatusError as exc:
        if _is_candidate_filter_rejection(exc):
            return False
        raise
    return True


def _select_auto_target(
    adapter,
    max_notional: Decimal,
    available_balances: dict[str, Decimal] | None = None,
) -> tuple[str, dict, Decimal, str]:
    balances = available_balances or base._available_quote_balances(adapter)
    symbols = [
        item
        for item in adapter.get_exchange_info().get("symbols", [])
        if item.get("status") == "TRADING"
        and "MARKET" in set(item.get("orderTypes", []))
        and "LIMIT" in set(item.get("orderTypes", []))
    ]
    symbols.sort(key=base._auto_symbol_sort_key)

    for item in symbols:
        symbol = str(item.get("symbol", "")).upper()
        quote_asset = str(item.get("quoteAsset", "")).upper()
        if not symbol or not quote_asset:
            continue
        try:
            effective_cap = base._spendable_notional_cap(
                max_notional,
                balances.get(quote_asset, Decimal("0")),
            )
            probe = base._auto_probe_for_symbol(adapter, symbol, effective_cap)
            if probe is None:
                continue
            acquisition_quantity, ticker_price = base._safe_quantity(
                adapter,
                symbol,
                effective_cap,
            )
            if probe["quantity"] > acquisition_quantity:
                continue
            if not _market_order_test(adapter, symbol, acquisition_quantity):
                continue
            filters = adapter.get_symbol_filters(symbol)
            limit_price = base._step_quantize(
                ticker_price * Decimal("1.50"),
                filters.tick_size,
                up=True,
            )
            base._bounded_quantity_for_price(
                filters,
                limit_price,
                effective_cap,
                utilization=base.PARTIAL_CAP_UTILIZATION,
            )
            return symbol, probe, effective_cap, quote_asset
        except (KeyError, RuntimeError, ValueError):
            continue
    raise RuntimeError(
        "no fresh Binance Spot TESTNET symbol satisfies balance, exchange order-test, market-filter, cap-bounded partial-fill preflight"
    )


def main() -> int:
    # Preserve the canonical scenario implementation and evidence shape; only harden
    # AUTO candidate selection with Binance's non-executing signed order-test endpoint.
    base._select_auto_target = _select_auto_target
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
