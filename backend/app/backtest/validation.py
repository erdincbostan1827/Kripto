from __future__ import annotations
import numpy as np

def walk_forward_splits(n,train,test):
    out=[]; start=0
    while start+train+test<=n: out.append((range(start,start+train),range(start+train,start+train+test))); start+=test
    return out
def purged_embargo_split(n,test_start,test_end,purge=1,embargo=1):
    test=set(range(test_start,test_end)); train=[i for i in range(n) if i not in test and not(test_start-purge<=i<test_start) and not(test_end<=i<test_end+embargo)]; return train,sorted(test)
def monte_carlo(trade_returns,simulations=10000,seed=42):
    rng=np.random.default_rng(seed); r=np.asarray(trade_returns,float)
    if r.size==0: return {'expected_return':0,'worst_drawdown':0,'probability_of_ruin':0,'ci95':[0,0]}
    totals=[]; dds=[]; ruins=0
    for _ in range(simulations):
        s=rng.choice(r,size=len(r),replace=True); eq=np.cumprod(1+s); peak=np.maximum.accumulate(eq); dd=np.max((peak-eq)/peak); totals.append(eq[-1]-1); dds.append(dd); ruins+=int(np.min(eq)<=0.5)
    return {'expected_return':float(np.mean(totals)),'worst_drawdown':float(np.max(dds)),'probability_of_ruin':ruins/simulations,'ci95':[float(np.quantile(totals,.025)),float(np.quantile(totals,.975))]}
def effective_sample_size(x):
    x=np.asarray(x,float); n=len(x)
    if n<3:return float(n)
    rho=np.corrcoef(x[:-1],x[1:])[0,1]
    if not np.isfinite(rho) or rho<=-0.999999: return float(n)
    return min(float(n),max(1.0,n*(1-rho)/(1+rho)))
