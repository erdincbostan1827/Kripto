from __future__ import annotations
from decimal import Decimal
from app.core.enums import OrderState
from app.exchange.models import OrderRecord
PROTECTIVE_TYPES={'STOP_LOSS','STOP_LOSS_LIMIT'}
def protection_coverage(position_qty:Decimal,position_side:str,orders:list[OrderRecord])->Decimal:
    opposite='SELL' if position_side=='LONG' else 'BUY'
    return sum((o.quantity-o.filled_quantity for o in orders if o.side==opposite and o.order_type in PROTECTIVE_TYPES and o.state in {OrderState.ACKNOWLEDGED,OrderState.PARTIALLY_FILLED} and o.stop_price is not None),Decimal('0'))
def ensure_protected(position_qty,position_side,orders):
    if protection_coverage(Decimal(position_qty),position_side,orders)<abs(Decimal(position_qty)): raise RuntimeError('UNPROTECTED_POSITION')
    return True
