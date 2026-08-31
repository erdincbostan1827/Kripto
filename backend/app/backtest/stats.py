from __future__ import annotations
import math
from statistics import NormalDist

def probabilistic_sharpe(sr,benchmark_sr,n,skew=0.0,kurtosis=3.0):
    if n<=1:return 0.0
    denom=math.sqrt(max(1e-12,(1-skew*sr+(kurtosis-1)*sr*sr/4)/(n-1)))
    return NormalDist().cdf((sr-benchmark_sr)/denom)
def deflated_sharpe(sr,n_trials,n,skew=0,kurtosis=3):
    expected_max=NormalDist().inv_cdf(max(0.5,min(0.999999,1-1/max(2,n_trials))))/math.sqrt(max(n,2)); return probabilistic_sharpe(sr,expected_max,n,skew,kurtosis)
def pbo_from_rankings(train_ranks,test_ranks):
    if not train_ranks:return 0.0
    bad=sum(t>0.5 for t in test_ranks); return bad/len(test_ranks)
