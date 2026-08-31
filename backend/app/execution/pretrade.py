from __future__ import annotations
from decimal import Decimal
from app.core.money import normalize_price,normalize_quantity,bps_distance
from app.exchange.models import OrderIntent,SymbolFilters,Capabilities

def normalize_and_validate(intent:OrderIntent,filters:SymbolFilters,cap:Capabilities,reference_price:Decimal,max_deviation_bps:Decimal=Decimal('100')):
    typ=intent.order_type.upper(); supported={'MARKET':cap.market,'LIMIT':cap.limit,'STOP_LOSS_LIMIT':cap.stop,'TAKE_PROFIT_LIMIT':cap.take_profit}.get(typ,False)
    if not supported: raise ValueError('unsupported order type')
    qty=normalize_quantity(intent.quantity,filters.step_size)
    if qty<filters.min_qty or qty>filters.max_qty: raise ValueError('quantity filter')
    price=normalize_price(intent.price,filters.tick_size,intent.side) if intent.price is not None else None
    check_price=price or reference_price
    if check_price*qty<filters.min_notional: raise ValueError('min notional')
    if filters.max_notional and check_price*qty>filters.max_notional: raise ValueError('max notional')
    if price is not None and bps_distance(price,reference_price)>max_deviation_bps: raise ValueError('fat finger price collar')
    return OrderIntent(intent.intent_id,intent.account_id,intent.symbol,intent.side,typ,qty,price,intent.stop_price,intent.market_type,intent.strategy_id,intent.reduce_only,intent.client_order_id or intent.intent_id)


def validate_reduce_only(intent: OrderIntent, current_position_qty: Decimal | None) -> None:
    """Fail closed unless the order can only reduce absolute exposure.

    Positive position quantity represents long exposure; negative represents
    short exposure. A reduce-only order may never cross through zero.
    """
    if not intent.reduce_only:
        return
    if current_position_qty is None:
        raise PermissionError('reduce-only requires current position context')
    position = Decimal(current_position_qty)
    if position == 0:
        raise PermissionError('reduce-only cannot open exposure from flat')
    side = intent.side.upper()
    if position > 0 and side != 'SELL':
        raise PermissionError('reduce-only side would increase long exposure')
    if position < 0 and side != 'BUY':
        raise PermissionError('reduce-only side would increase short exposure')
    if Decimal(intent.quantity) > abs(position):
        raise PermissionError('reduce-only quantity would cross through zero')


def validate_spot_sell_balance(intent: OrderIntent, available_base_qty: Decimal | None) -> None:
    """SPOT cannot create synthetic short exposure by selling unavailable base asset."""
    if str(intent.market_type.value if hasattr(intent.market_type, "value") else intent.market_type).upper() != "SPOT":
        return
    if intent.side.upper() != "SELL":
        return
    if available_base_qty is None:
        raise PermissionError("SPOT SELL requires available base-asset balance context")
    available = Decimal(available_base_qty)
    if available < 0:
        raise ValueError("available base balance cannot be negative")
    if Decimal(intent.quantity) > available:
        raise PermissionError("SPOT SELL exceeds available base-asset balance")
