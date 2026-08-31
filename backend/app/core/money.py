from __future__ import annotations
from decimal import Decimal, ROUND_DOWN, ROUND_UP, InvalidOperation

D=Decimal

def decimal(value: object) -> Decimal:
    try: x=Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc: raise ValueError('invalid decimal') from exc
    if not x.is_finite(): raise ValueError('non-finite financial value')
    return x.copy_abs() if x==0 else x

def quantize_step(value: Decimal, step: Decimal, *, direction: str='down') -> Decimal:
    value, step=decimal(value),decimal(step)
    if step<=0: raise ValueError('step must be positive')
    rounding=ROUND_DOWN if direction=='down' else ROUND_UP
    units=(value/step).to_integral_value(rounding=rounding)
    return units*step

def normalize_price(price: Decimal,tick: Decimal,side: str) -> Decimal:
    return quantize_step(price,tick,direction='down' if side.upper()=='BUY' else 'up')

def normalize_quantity(qty: Decimal,step: Decimal) -> Decimal:
    return quantize_step(qty,step,direction='down')

def bps_distance(a: Decimal,b: Decimal) -> Decimal:
    a,b=decimal(a),decimal(b)
    if b==0: raise ZeroDivisionError('reference price is zero')
    return abs(a-b)/b*D(10000)
