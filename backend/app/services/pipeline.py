from __future__ import annotations
from datetime import datetime,timezone
from decimal import Decimal
from datetime import datetime
from app.data.quality import validate_candles
from app.data.candles import INTERVAL_SECONDS
from app.indicators.engine import indicators
from app.strategies.regime import detect_regime
from app.signals.engine import decide

def analyze(candles,timeframe='1h'):
    normalized=[]
    for row in candles:
        x=dict(row)
        for key in ('open_time','close_time'):
            if isinstance(x.get(key),str): x[key]=datetime.fromisoformat(x[key].replace('Z','+00:00'))
        normalized.append(x)
    candles=normalized
    validate_candles(candles,INTERVAL_SECONDS[timeframe],min_bars=min(50,len(candles)))
    f=indicators(candles); f['price']=float(candles[-1]['close']); regime=detect_regime(f); return decide(f,regime,candles[-1]['close_time'].isoformat())
