from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class CalibrationReport:
    brier_score:float; buckets:tuple[dict,...]; sample_count:int

def calibrate(probabilities,outcomes,buckets=10):
    if len(probabilities)!=len(outcomes) or not probabilities: raise ValueError('probability/outcome sample mismatch')
    ps=[min(1,max(0,float(p))) for p in probabilities]; ys=[1 if bool(y) else 0 for y in outcomes]; brier=sum((p-y)**2 for p,y in zip(ps,ys))/len(ps); out=[]
    for i in range(buckets):
        lo=i/buckets; hi=(i+1)/buckets; idx=[j for j,p in enumerate(ps) if lo<=p<(hi if i<buckets-1 else hi+1e-12)]
        if idx: out.append({'lower':lo,'upper':hi,'count':len(idx),'mean_confidence':sum(ps[j] for j in idx)/len(idx),'observed_rate':sum(ys[j] for j in idx)/len(idx)})
    return CalibrationReport(brier,tuple(out),len(ps))
