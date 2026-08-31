from datetime import datetime, timezone, timedelta

import pytest

from app.core.enums import Signal
from app.signals.multi_timeframe import analyze_multi_timeframe
from app.data.candles import INTERVAL_SECONDS


def candles(tf: str, up: bool, n: int = 250):
    step=INTERVAL_SECONDS[tf]
    start=datetime(2025,1,1,tzinfo=timezone.utc)
    out=[]
    for i in range(n):
        base=100+i*.2 if up else 200-i*.2
        open_time=start+timedelta(seconds=i*step)
        out.append({
            'open_time':open_time,
            'close_time':open_time+timedelta(seconds=step),
            'open':base,
            'high':base+.5,
            'low':base-.5,
            'close':base+.1,
            'volume':1000+i,
            'closed':True,
        })
    return out


def test_multi_timeframe_bullish_alignment():
    data={tf:candles(tf,True) for tf in ('1d','4h','1h','15m','5m')}
    result=analyze_multi_timeframe(data)
    assert result.higher_timeframe_bias=='BULLISH'
    assert result.conflict is False
    assert result.signal in {Signal.BUY,Signal.STRONG_BUY}
    assert set(result.timeframe_scores)==set(data)


def test_multi_timeframe_conflict_blocks_low_timeframe_buy():
    data={tf:candles(tf,False) for tf in ('1d','4h','1h')}
    data.update({tf:candles(tf,True) for tf in ('15m','5m')})
    result=analyze_multi_timeframe(data)
    assert result.higher_timeframe_bias=='BEARISH'
    assert result.conflict is True
    assert result.signal==Signal.NO_TRADE
    assert 'MULTI_TIMEFRAME_CONFLICT' in result.reasons


def test_multi_timeframe_requires_complete_configured_set():
    data={tf:candles(tf,True) for tf in ('1d','4h','1h','15m')}
    with pytest.raises(ValueError,match='missing required timeframes'):
        analyze_multi_timeframe(data)
