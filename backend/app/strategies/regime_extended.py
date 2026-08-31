from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RegimeAssessment:
    regime: str
    reasons: tuple[str,...]
    risk_multiplier: float


def detect_extended_regime(f:dict)->RegimeAssessment:
    """Explainable regime classification from point-in-time features only."""
    reasons=[]
    vol=float(f.get("historical_volatility",0)); bb=float(f.get("bb_width",0)); vr=float(f.get("volume_ratio",1))
    price=float(f.get("price",0)); resistance=float(f.get("resistance",float("inf"))); support=float(f.get("support",0))
    ema21=float(f.get("ema21",price)); ema50=float(f.get("ema50",price)); slope=float(f.get("trend_slope",0))
    if bool(f.get("liquidation_panic",False)) or (bb>=0.12 and vr>=2.0 and slope<0):
        reasons += ["PANIC_VOLATILITY","NEGATIVE_STRUCTURE"]; return RegimeAssessment("PANIC",tuple(reasons),0.0)
    if price>0 and resistance>0 and price>resistance and vr>=1.25:
        return RegimeAssessment("BREAKOUT",("RESISTANCE_BREAK","VOLUME_CONFIRMATION"),0.8)
    if price>0 and support>0 and price<support and vr>=1.25:
        return RegimeAssessment("BREAKDOWN",("SUPPORT_BREAK","VOLUME_CONFIRMATION"),0.0)
    if vol<=float(f.get("low_vol_threshold",0.005)) and bb<=float(f.get("low_bb_threshold",0.02)):
        return RegimeAssessment("LOW_VOLATILITY",("LOW_REALIZED_VOL","NARROW_BANDS"),0.6)
    if bb>=0.08:
        return RegimeAssessment("HIGH_VOLATILITY",("WIDE_BANDS",),0.4)
    if ema21>ema50 and slope>0 and bool(f.get("higher_high",1)):
        return RegimeAssessment("BULLISH_TREND",("MOVING_AVERAGE_ALIGNMENT","BULLISH_MARKET_STRUCTURE"),1.0)
    if ema21<ema50 and slope<0 and bool(f.get("lower_low",1)):
        return RegimeAssessment("BEARISH_TREND",("MOVING_AVERAGE_ALIGNMENT","BEARISH_MARKET_STRUCTURE"),0.0)
    return RegimeAssessment("SIDEWAYS",("MIXED_STRUCTURE",),0.7)
