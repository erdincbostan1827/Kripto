from __future__ import annotations
def detect_regime(f:dict)->str:
    if f['atr']>0 and f.get('bb_width',0)>0.08: return 'HIGH_VOLATILITY'
    if f['ema21']>f['ema50']>f['ema200'] and f['trend_slope']>0: return 'BULLISH_TREND'
    if f['ema21']<f['ema50']<f['ema200'] and f['trend_slope']<0: return 'BEARISH_TREND'
    return 'SIDEWAYS'
