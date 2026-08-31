from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from app.core.enums import Signal
@dataclass(frozen=True)
class SignalDecision:
    signal:Signal; score:int; confidence:float; reasons:tuple[str,...]; risks:tuple[str,...]; invalidation:str; entry:Decimal|None; stop_loss:Decimal|None; take_profits:tuple[Decimal,...]; risk_reward:Decimal|None; regime:str; data_timestamp:str

def falling_knife_blocked(f:dict,regime:str)->bool:
    return regime in {'BEARISH_TREND','HIGH_VOLATILITY'} and (f['ema50']>f.get('price',f['ema50']) or f['trend_slope']<0 or f.get('volume_ratio',1)>1.8)
def decide(f:dict,regime:str,data_timestamp:str,min_rr=Decimal('2'))->SignalDecision:
    price=Decimal(str(f['price'])); atr=Decimal(str(max(f['atr'],1e-9)))
    trend=20 if f['ema21']>f['ema50'] else -20; mom=15 if f['rsi']>=50 and f['macd']>=f['macd_signal'] else -10; volume=10 if f['volume_ratio']>=1 else 0; structure=10 if f['trend_slope']>0 else -10; regime_score=15 if regime=='BULLISH_TREND' else -20 if regime=='BEARISH_TREND' else 0
    score=max(0,min(100,50+trend+mom+volume+structure+regime_score))
    blocked=falling_knife_blocked(f,regime); stop=price-atr*Decimal('2'); risk=price-stop; tp=(price+risk,price+risk*2,price+risk*3); rr=(tp[1]-price)/risk if risk>0 else Decimal('0')
    if regime=='BEARISH_TREND' and blocked:
        sig=Signal.STRONG_SELL if score<=20 else Signal.SELL
    elif blocked or rr<min_rr:
        sig=Signal.NO_TRADE
    elif score>=80:
        sig=Signal.STRONG_BUY
    elif score>=65:
        sig=Signal.BUY
    elif score>=55:
        sig=Signal.WATCH
    elif score<=20:
        sig=Signal.STRONG_SELL
    elif score<=35:
        sig=Signal.SELL
    elif score<=45:
        sig=Signal.REDUCE
    else:
        sig=Signal.HOLD
    reasons=(f'regime={regime}',f'score={score}',f'rsi={f["rsi"]:.1f}',f'volume_ratio={f["volume_ratio"]:.2f}')
    risks=tuple(x for x,b in [('falling_knife',blocked),('high_volatility',regime=='HIGH_VOLATILITY')] if b)
    return SignalDecision(sig,score,min(0.99,max(0.01,score/100)),reasons,risks,'close below stop',price if sig in {Signal.BUY,Signal.STRONG_BUY} else None,stop if sig in {Signal.BUY,Signal.STRONG_BUY} else None,tp if sig in {Signal.BUY,Signal.STRONG_BUY} else (),rr if sig in {Signal.BUY,Signal.STRONG_BUY} else None,regime,data_timestamp)
