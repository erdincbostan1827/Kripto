from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

D=Decimal
EXECUTION_MODEL_VERSION='conservative-intrabar-v1'

@dataclass(frozen=True)
class FillDecision:
    filled:bool
    price:D|None
    reason:str
    model_version:str=EXECUTION_MODEL_VERSION


def next_bar_market_fill(side:str,next_open,slippage_bps=D('0'))->FillDecision:
    px=D(next_open); slip=D(slippage_bps)/D('10000')
    if px<=0: raise ValueError('next open must be positive')
    price=px*(D('1')+slip if side.upper()=='BUY' else D('1')-slip)
    return FillDecision(True,price,'NEXT_BAR_MARKET')


def conservative_exit_long(*,bar_open,bar_high,bar_low,stop,tp,slippage_bps=D('0'))->FillDecision:
    o,h,l,st,t=D(bar_open),D(bar_high),D(bar_low),D(stop),D(tp)
    slip=D(slippage_bps)/D('10000')
    if o<=st: return FillDecision(True,o*(D('1')-slip),'STOP_GAP_THROUGH')
    stop_hit=l<=st; tp_hit=h>=t
    if stop_hit: return FillDecision(True,st*(D('1')-slip),'STOP_CONSERVATIVE')
    if tp_hit: return FillDecision(True,t*(D('1')-slip),'TAKE_PROFIT')
    return FillDecision(False,None,'NO_EXIT')


def conservative_limit_fill(side:str,limit_price,bar_open,bar_high,bar_low,*,require_penetration=True,queue_fill_ratio=D('1'),requested_qty=D('1'),available_liquidity=None)->FillDecision:
    lp,o,h,l=D(limit_price),D(bar_open),D(bar_high),D(bar_low)
    touched = l<=lp if side.upper()=='BUY' else h>=lp
    penetrated = l<lp if side.upper()=='BUY' else h>lp
    if not touched: return FillDecision(False,None,'LIMIT_NOT_TOUCHED')
    if require_penetration and not penetrated: return FillDecision(False,None,'TOUCH_NOT_GUARANTEED')
    if D(queue_fill_ratio)<=0: return FillDecision(False,None,'QUEUE_NO_FILL')
    if available_liquidity is not None and D(available_liquidity)<=0: return FillDecision(False,None,'NO_LIQUIDITY')
    # Conservative limit fills never improve beyond the limit on a touch model.
    return FillDecision(True,lp,'LIMIT_CONSERVATIVE')

@dataclass(frozen=True)
class IntrabarEvidence:
    lower_timeframe_order: str | None = None
    tick_trade_order: str | None = None
    orderbook_order: str | None = None


def resolve_long_stop_take_profit(*,bar_open,bar_high,bar_low,stop,tp,evidence:IntrabarEvidence|None=None,slippage_bps=D('0'))->FillDecision:
    """Resolve ambiguous long exit with strongest available point-in-time micro evidence.

    Evidence priority is lower-timeframe sequence, then trade/tick sequence, then
    order-book sequence. If none is available, the conservative stop-first bar
    model is used; evidence never permits optimistic guessing.
    """
    o,h,l,st,t=D(bar_open),D(bar_high),D(bar_low),D(stop),D(tp)
    stop_hit=l<=st; tp_hit=h>=t
    if not (stop_hit and tp_hit):
        return conservative_exit_long(bar_open=o,bar_high=h,bar_low=l,stop=st,tp=t,slippage_bps=slippage_bps)
    ev=evidence or IntrabarEvidence()
    source_order=(('LOWER_TIMEFRAME',ev.lower_timeframe_order),('TICK_TRADE',ev.tick_trade_order),('ORDER_BOOK',ev.orderbook_order))
    for source,order in source_order:
        if order:
            x=order.upper()
            if x not in {'STOP_FIRST','TP_FIRST'}: raise ValueError(f'invalid {source} intrabar ordering')
            if x=='STOP_FIRST':
                return FillDecision(True,st*(D('1')-D(slippage_bps)/D('10000')),f'STOP_{source}_EVIDENCE')
            return FillDecision(True,t,f'TAKE_PROFIT_{source}_EVIDENCE')
    return conservative_exit_long(bar_open=o,bar_high=h,bar_low=l,stop=st,tp=t,slippage_bps=slippage_bps)
