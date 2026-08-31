from __future__ import annotations
from dataclasses import dataclass
from statistics import mean,pstdev
from typing import Sequence,Mapping

@dataclass(frozen=True)
class DegradationReport:
    degraded:bool; reasons:tuple[str,...]; sample_size:int; false_alarm_guard:bool

def detect_degradation(metrics:Mapping[str,Sequence[float]],*,min_samples=30,z_threshold=2.5)->DegradationReport:
    reasons=[]; sizes=[len(v) for v in metrics.values()]
    if not sizes or min(sizes)<min_samples: return DegradationReport(False,(),min(sizes or [0]),True)
    for name,xs0 in metrics.items():
        xs=list(map(float,xs0)); split=max(10,len(xs)//2); base=xs[:split]; recent=xs[split:]
        sd=pstdev(base)
        if sd>0 and abs(mean(recent)-mean(base))/sd>=z_threshold: reasons.append(name.upper()+"_DRIFT")
    return DegradationReport(bool(reasons),tuple(sorted(reasons)),min(sizes),True)

def cusum(values:Sequence[float],*,target=0.0,threshold=5.0,drift=0.0)->bool:
    pos=neg=0.0
    for x in values:
        pos=max(0,pos+x-target-drift); neg=min(0,neg+x-target+drift)
        if pos>threshold or abs(neg)>threshold: return True
    return False

def page_hinkley(values:Sequence[float],*,threshold=5.0,delta=.005)->bool:
    m=0.0; cumulative=0.0; minimum=0.0
    for i,x in enumerate(values,1):
        m += (x-m)/i; cumulative += x-m-delta; minimum=min(minimum,cumulative)
        if cumulative-minimum>threshold: return True
    return False
