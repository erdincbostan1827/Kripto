from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.exchange.models import SymbolFilters
from scripts.external import binance_testnet_acceptance as legacy


def _positive_decimal(raw: object) -> Decimal | None:
    try:
        value = Decimal(str(raw if raw is not None else "0"))
    except (InvalidOperation, ValueError):
        return None
    return value if value > 0 else None


def _fieldwise_market_symbol_filters(adapter, symbol: str) -> SymbolFilters:
    """Apply each active MARKET_LOT_SIZE field independently.

    Binance can expose zero-valued MARKET_LOT_SIZE fields as disabled while
    another field (notably maxQty) remains enforceable. Falling back to the
    whole LOT_SIZE filter in that mixed state can submit a MARKET quantity
    above the exchange's active market-only bound.
    """
    base = adapter.get_symbol_filters(symbol)
    metadata = adapter.get_symbol_metadata(symbol)
    raw_market = next(
        (
            item
            for item in metadata.get("filters", [])
            if isinstance(item, dict) and item.get("filterType") == "MARKET_LOT_SIZE"
        ),
        None,
    )
    if not isinstance(raw_market, dict):
        return base

    market_step = _positive_decimal(raw_market.get("stepSize"))
    market_min = _positive_decimal(raw_market.get("minQty"))
    market_max = _positive_decimal(raw_market.get("maxQty"))
    if market_step is None and market_min is None and market_max is None:
        return base

    step = market_step or base.step_size
    minimum = market_min or base.min_qty
    maximum = market_max or base.max_qty
    if step <= 0 or minimum <= 0 or maximum <= 0 or maximum < minimum:
        raise RuntimeError("invalid effective MARKET_LOT_SIZE bounds")

    return SymbolFilters(
        tick_size=base.tick_size,
        step_size=step,
        min_qty=minimum,
        max_qty=maximum,
        min_notional=base.min_notional,
        max_notional=base.max_notional,
        max_orders=base.max_orders,
    )


def main() -> int:
    legacy._market_symbol_filters = _fieldwise_market_symbol_filters
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
