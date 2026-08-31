from __future__ import annotations
from dataclasses import dataclass
from .engine import indicators

@dataclass(frozen=True)
class StabilityResult:
    stable:bool
    max_relative_drift:float
    drifts:dict[str,float]


def recursive_stability(rows:list[dict],warmup_bars:int=200,extra_history:int=50,tolerance:float=0.01)->StabilityResult:
    if warmup_bars<=0 or extra_history<=0: raise ValueError('warmup and extra_history must be positive')
    if len(rows)<warmup_bars+extra_history: raise ValueError('insufficient history for recursive stability test')
    short=indicators(rows[-warmup_bars:])
    long=indicators(rows[-(warmup_bars+extra_history):])
    drifts={}
    for k in short:
        denom=max(abs(float(long[k])),1e-9)
        drifts[k]=abs(float(short[k])-float(long[k]))/denom
    max_drift=max(drifts.values(),default=0.0)
    return StabilityResult(max_drift<=tolerance,max_drift,drifts)
