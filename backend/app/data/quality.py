from __future__ import annotations
from datetime import datetime,timezone,timedelta
from decimal import Decimal

def ensure_fresh(data_time:datetime,max_age_seconds:int,now:datetime|None=None):
    now=now or datetime.now(timezone.utc)
    if data_time.tzinfo is None: raise ValueError('timezone-aware timestamp required')
    age=(now-data_time).total_seconds()
    if age<0: raise ValueError('future data timestamp')
    if age>max_age_seconds: raise ValueError('stale data')
    return age

def validate_candles(candles:list[dict],interval_seconds:int,min_bars:int=1,now:datetime|None=None):
    if len(candles)<min_bars: raise ValueError('insufficient warmup history')
    times=[c['open_time'] for c in candles]
    if len(set(times))!=len(times): raise ValueError('duplicate candle')
    if times!=sorted(times): raise ValueError('out-of-order candle')
    for a,b in zip(times,times[1:]):
        if int((b-a).total_seconds())!=interval_seconds: raise ValueError('candle gap')
    now=now or datetime.now(timezone.utc)
    if any(not c.get('closed', c.get('close_time',now)<=now) for c in candles): raise ValueError('non-final candle')
    return True

def spread_bps(best_bid:Decimal,best_ask:Decimal)->Decimal:
    if best_bid<=0 or best_ask<=0 or best_ask<best_bid: raise ValueError('invalid/crossed book')
    mid=(best_bid+best_ask)/2; return (best_ask-best_bid)/mid*Decimal(10000)
