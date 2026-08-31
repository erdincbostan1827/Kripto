from __future__ import annotations
from dataclasses import dataclass
from random import Random
from statistics import mean
from math import sqrt
from typing import Sequence

@dataclass(frozen=True)
class BootstrapSummary:
    ruin_probability: float
    expected_max_drawdown: float
    max_drawdown_p95: float
    expected_drawdown_duration: float
    expected_losing_streak: float
    terminal_wealth_p05: float
    terminal_wealth_p50: float
    terminal_wealth_p95: float
    recovery_time_p95: float
    effective_sample_size: float

def effective_sample_size(xs: Sequence[float]) -> float:
    if len(xs)<3: return float(len(xs))
    m=mean(xs); den=sum((x-m)**2 for x in xs)
    if den<=0: return float(len(xs))
    rho=sum((xs[i]-m)*(xs[i-1]-m) for i in range(1,len(xs)))/den
    rho=max(-.99,min(.99,rho)); return max(1.0,min(float(len(xs)),len(xs)*(1-rho)/(1+rho)))

def _drawdown(path):
    wealth=peak=1.0; maxdd=0.0; dur=maxdur=0; losing=streak=maxstreak=0; recovery=[]
    for r in path:
        wealth*=1+r; peak=max(peak,wealth); dd=(peak-wealth)/peak
        if dd>0: dur+=1; maxdur=max(maxdur,dur)
        else:
            if dur: recovery.append(dur)
            dur=0
        maxdd=max(maxdd,dd)
        if r<0: streak+=1; maxstreak=max(maxstreak,streak)
        else: streak=0
    return wealth,maxdd,maxdur,maxstreak,max(recovery or [dur])

def bootstrap_paths(returns: Sequence[float], *, simulations=500, method='block', block_size=5, regimes: Sequence[str]|None=None, seed=7, cost_shock=0.0, slippage_shock=0.0, latency_shock=0.0, ruin_threshold=.5):
    xs=list(map(float,returns)); n=len(xs)
    if n<5: raise ValueError('insufficient sample')
    if method not in {'reshuffle','block','stationary','regime'}: raise ValueError('unsupported bootstrap method')
    if method=='regime' and (regimes is None or len(regimes)!=n): raise ValueError('regimes required')
    rng=Random(seed); paths=[]
    for _ in range(simulations):
        if method=='reshuffle':
            p=xs.copy(); rng.shuffle(p)
        elif method=='block':
            p=[]
            while len(p)<n:
                start=rng.randrange(n); p.extend(xs[(start+j)%n] for j in range(block_size))
            p=p[:n]
        elif method=='stationary':
            p=[]; i=rng.randrange(n)
            while len(p)<n:
                p.append(xs[i]); i=(i+1)%n if rng.random()>1/max(1,block_size) else rng.randrange(n)
        else:
            buckets={}
            for r,x in zip(regimes,xs): buckets.setdefault(r,[]).append(x)
            p=[rng.choice(buckets[r]) for r in regimes]
        shock=abs(cost_shock)+abs(slippage_shock)+abs(latency_shock)
        paths.append([x-shock for x in p])
    stats=[_drawdown(p) for p in paths]
    vals=sorted(s[0] for s in stats); dds=sorted(s[1] for s in stats); rec=sorted(s[4] for s in stats)
    q=lambda arr,p: arr[min(len(arr)-1,max(0,int((len(arr)-1)*p)))]
    return BootstrapSummary(sum(v<ruin_threshold for v in vals)/len(vals),mean(dds),q(dds,.95),mean(s[2] for s in stats),mean(s[3] for s in stats),q(vals,.05),q(vals,.5),q(vals,.95),q(rec,.95),effective_sample_size(xs))
