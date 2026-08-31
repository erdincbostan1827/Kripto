from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from statistics import mean,pstdev
from typing import Sequence

@dataclass(frozen=True)
class BenchmarkReport:
    strategy_return:float; buy_hold_return:float; cash_return:float; dca_return:float; trend_return:float; excess_return:float
    sharpe:float; sortino:float; effective_sample_size:float; confidence_interval:tuple[float,float]; minimum_track_record_length:int

def _compound(xs):
    w=1.0
    for x in xs: w*=1+x
    return w-1

def benchmark_report(strategy:Sequence[float],asset:Sequence[float],*,cash_rate=0.0)->BenchmarkReport:
    if len(strategy)!=len(asset) or len(strategy)<10: raise ValueError('aligned track record required')
    s=list(map(float,strategy)); a=list(map(float,asset)); mu=mean(s); sd=pstdev(s); down=pstdev([min(0,x) for x in s])
    sharpe=0 if sd==0 else mu/sd*sqrt(365); sortino=0 if down==0 else mu/down*sqrt(365)
    # lightweight uncertainty/track-record proxies; explicit, deterministic and conservative.
    se=(sd/sqrt(len(s))) if sd else 0.0; ci=(mu-1.96*se,mu+1.96*se)
    ess=float(len(s)); mtrl=max(30,int((1.96/max(abs(sharpe),.1))**2*30))
    dca=_compound([x*.5 for x in a]); trend=_compound([x if i and a[i-1]>0 else 0 for i,x in enumerate(a)])
    sr=_compound(s); bh=_compound(a)
    return BenchmarkReport(sr,bh,cash_rate,dca,trend,sr-bh,sharpe,sortino,ess,ci,mtrl)

def deflated_sharpe_proxy(sharpe:float,trials:int)->float:
    return sharpe/max(1.0,sqrt(max(1,trials)))

def probabilistic_sharpe_proxy(sharpe:float,benchmark:float,sample:int)->float:
    z=(sharpe-benchmark)*sqrt(max(1,sample)); return max(0.0,min(1.0,.5+z/10))

def probability_backtest_overfit_proxy(train_scores:Sequence[float],test_scores:Sequence[float])->float:
    if len(train_scores)!=len(test_scores) or not train_scores: raise ValueError('paired trials required')
    top=max(range(len(train_scores)),key=lambda i:train_scores[i]); rank=sum(x<=test_scores[top] for x in test_scores)/len(test_scores)
    return max(0.0,min(1.0,1-rank))
