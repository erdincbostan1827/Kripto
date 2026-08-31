from __future__ import annotations
from datetime import datetime,timezone
INTERVAL_SECONDS={'1m':60,'3m':180,'5m':300,'15m':900,'30m':1800,'1h':3600,'4h':14400,'1d':86400}
# Fail-safe default: strategies consume only closed/final candles unless an explicitly reviewed intrabar strategy overrides this at its own boundary.
CLOSED_CANDLE_ONLY=True
def is_final(close_time:datetime,now:datetime|None=None)->bool: return close_time<= (now or datetime.now(timezone.utc))
def closed_only(candles,now=None): return [c for c in candles if c.get('closed',is_final(c['close_time'],now))]

def aggregate_ohlcv(candles:list[dict], timeframe:str)->list[dict]:
    """Aggregate already time-ordered base candles into deterministic UTC buckets."""
    seconds=INTERVAL_SECONDS.get(timeframe)
    if seconds is None: raise ValueError('unsupported timeframe')
    buckets={}
    for c in candles:
        ts=c['open_time']
        if ts.tzinfo is None: raise ValueError('candle open_time must be timezone-aware')
        epoch=int(ts.timestamp()); start_epoch=(epoch//seconds)*seconds
        start=datetime.fromtimestamp(start_epoch,tz=timezone.utc)
        b=buckets.get(start)
        if b is None:
            buckets[start]={'open_time':start,'close_time':datetime.fromtimestamp(start_epoch+seconds,tz=timezone.utc),'open':c['open'],'high':c['high'],'low':c['low'],'close':c['close'],'volume':c.get('volume',0),'closed':bool(c.get('closed',False))}
        else:
            b['high']=max(b['high'],c['high']); b['low']=min(b['low'],c['low']); b['close']=c['close']; b['volume']+=c.get('volume',0); b['closed']=b['closed'] and bool(c.get('closed',False))
    return [buckets[k] for k in sorted(buckets)]
