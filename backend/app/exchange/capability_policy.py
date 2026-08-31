from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

@dataclass(frozen=True)
class SymbolCapabilityProfile:
    symbol: str
    order_types: tuple[str, ...]
    oco_or_order_list: bool
    order_book_depth_supported: bool
    cancel_replace_supported: bool
    precision_mode: str
    min_price: Decimal
    max_price: Decimal | None
    min_qty: Decimal
    max_qty: Decimal
    min_notional: Decimal
    max_notional: Decimal | None
    max_open_orders: int | None
    exchange_rate_limits: tuple[dict[str, Any], ...]

    def assert_pretrade_supported(self) -> None:
        if not self.symbol.strip():
            raise RuntimeError('symbol required')
        if self.precision_mode not in {'TICK_STEP_FILTERS'}:
            raise RuntimeError('unsupported precision mode')
        if not self.order_types:
            raise RuntimeError('no supported order types')
        if self.min_price <= 0 or self.min_qty <= 0:
            raise RuntimeError('invalid exchange filters')
        if self.max_price is not None and self.max_price < self.min_price:
            raise RuntimeError('max price below min price')
        if self.max_qty < self.min_qty:
            raise RuntimeError('max quantity below min quantity')
        if self.min_notional < 0:
            raise RuntimeError('negative min notional')
        if self.max_notional is not None and self.max_notional < self.min_notional:
            raise RuntimeError('max notional below min notional')
        if self.max_open_orders is not None and self.max_open_orders <= 0:
            raise RuntimeError('invalid max open orders')
        for item in self.exchange_rate_limits:
            if item.get('limit') is not None and int(item['limit']) <= 0:
                raise RuntimeError('invalid exchange rate limit')


def from_binance_exchange_info(symbol_info: dict[str, Any], rate_limits: list[dict[str, Any]]) -> SymbolCapabilityProfile:
    filters = {f.get('filterType'): f for f in symbol_info.get('filters', [])}
    price = filters.get('PRICE_FILTER')
    lot = filters.get('LOT_SIZE')
    if not price or not lot:
        raise RuntimeError('PRICE_FILTER and LOT_SIZE required')
    notion = filters.get('NOTIONAL') or filters.get('MIN_NOTIONAL') or {}
    tick = Decimal(str(price.get('tickSize', '0')))
    step = Decimal(str(lot.get('stepSize', '0')))
    if tick <= 0 or step <= 0:
        raise RuntimeError('non-positive tick/step')
    min_price = Decimal(str(price.get('minPrice', tick)))
    max_price_raw = price.get('maxPrice')
    max_price = Decimal(str(max_price_raw)) if max_price_raw not in (None, '', '0', 0) else None
    max_notional_raw = notion.get('maxNotional')
    profile = SymbolCapabilityProfile(
        symbol=str(symbol_info.get('symbol') or ''),
        order_types=tuple(str(x) for x in symbol_info.get('orderTypes', [])),
        oco_or_order_list=bool(symbol_info.get('ocoAllowed') or symbol_info.get('otoAllowed') or symbol_info.get('otoCoAllowed')),
        order_book_depth_supported=True,
        cancel_replace_supported=bool(symbol_info.get('cancelReplaceAllowed', False)),
        precision_mode='TICK_STEP_FILTERS',
        min_price=min_price,
        max_price=max_price,
        min_qty=Decimal(str(lot.get('minQty', '0'))),
        max_qty=Decimal(str(lot.get('maxQty', '0'))),
        min_notional=Decimal(str(notion.get('minNotional', '0'))),
        max_notional=Decimal(str(max_notional_raw)) if max_notional_raw not in (None, '') else None,
        max_open_orders=int(symbol_info['maxNumOrders']) if symbol_info.get('maxNumOrders') is not None else None,
        exchange_rate_limits=tuple(dict(x) for x in rate_limits),
    )
    profile.assert_pretrade_supported()
    return profile
