from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from app.backtest.stats import probabilistic_sharpe, deflated_sharpe
from app.backtest.validation import effective_sample_size

@dataclass(frozen=True)
class ResearchValidationReport:
    in_sample_return: float
    out_of_sample_return: float
    walk_forward_mean: float
    fee_sensitivity: dict[str, float]
    slippage_sensitivity: dict[str, float]
    latency_sensitivity: dict[str, float]
    parameter_sensitivity: dict[str, float]
    regime_breakdown: dict[str, float]
    benchmark_excess_return: float
    trade_count: int
    effective_sample_size: float
    probabilistic_sharpe_ratio: float
    deflated_sharpe_ratio: float
    bootstrap_ci95: tuple[float, float]
    multiple_testing_adjusted_alpha: float
    accepted: bool
    rejection_reasons: tuple[str, ...]


def _total_return(xs) -> float:
    arr=np.asarray(xs,float)
    if arr.size==0: return 0.0
    return float(np.prod(1.0+arr)-1.0)


def _sharpe(xs) -> float:
    arr=np.asarray(xs,float)
    if arr.size < 2: return 0.0
    sd=float(arr.std(ddof=1))
    if sd <= 1e-15: return 0.0
    return float(arr.mean()/sd*math.sqrt(arr.size))


def bootstrap_ci(xs, *, simulations=2000, seed=42) -> tuple[float,float]:
    arr=np.asarray(xs,float)
    if arr.size == 0: return (0.0,0.0)
    rng=np.random.default_rng(seed)
    stats=np.empty(simulations,float)
    for i in range(simulations):
        sample=rng.choice(arr,size=arr.size,replace=True)
        stats[i]=_total_return(sample)
    return (float(np.quantile(stats,0.025)),float(np.quantile(stats,0.975)))


def holm_bonferroni_alpha(alpha:float, trials:int) -> float:
    if not 0 < alpha < 1: raise ValueError('alpha must be between zero and one')
    if trials < 1: raise ValueError('trials must be positive')
    return alpha/trials


def validate_research(
    *,
    in_sample_returns,
    out_of_sample_returns,
    walk_forward_returns,
    benchmark_returns,
    fee_scenarios:dict[str,list[float]],
    slippage_scenarios:dict[str,list[float]],
    latency_scenarios:dict[str,list[float]],
    parameter_scenarios:dict[str,list[float]],
    regime_returns:dict[str,list[float]],
    n_trials:int=1,
    min_trades:int=30,
    min_effective_samples:float=20.0,
    min_psr:float=0.90,
    min_dsr:float=0.80,
    seed:int=42,
) -> ResearchValidationReport:
    ins=np.asarray(in_sample_returns,float); oos=np.asarray(out_of_sample_returns,float)
    wf=np.asarray(walk_forward_returns,float); bench=np.asarray(benchmark_returns,float)
    if oos.size == 0: raise ValueError('out-of-sample returns required')
    if ins.size == 0: raise ValueError('in-sample returns required')
    if wf.size == 0: raise ValueError('walk-forward returns required')
    fee={k:_total_return(v) for k,v in fee_scenarios.items()}
    slip={k:_total_return(v) for k,v in slippage_scenarios.items()}
    lat={k:_total_return(v) for k,v in latency_scenarios.items()}
    param={k:_total_return(v) for k,v in parameter_scenarios.items()}
    regimes={k:_total_return(v) for k,v in regime_returns.items()}
    sr=_sharpe(oos)
    psr=probabilistic_sharpe(sr,0.0,len(oos))
    dsr=deflated_sharpe(sr,n_trials,len(oos))
    ess=effective_sample_size(oos)
    ci=bootstrap_ci(oos,seed=seed)
    bench_excess=_total_return(oos)-_total_return(bench)
    reasons=[]
    if len(oos) < min_trades: reasons.append('INSUFFICIENT_TRADES')
    if ess < min_effective_samples: reasons.append('INSUFFICIENT_EFFECTIVE_SAMPLE')
    if psr < min_psr: reasons.append('LOW_PSR')
    if dsr < min_dsr: reasons.append('LOW_DSR')
    if ci[0] <= 0: reasons.append('BOOTSTRAP_CI_NOT_POSITIVE')
    if bench_excess <= 0: reasons.append('NO_BENCHMARK_EDGE')
    if any(v <= 0 for v in fee.values()): reasons.append('FEE_STRESS_FAIL')
    if any(v <= 0 for v in slip.values()): reasons.append('SLIPPAGE_STRESS_FAIL')
    if any(v <= 0 for v in lat.values()): reasons.append('LATENCY_STRESS_FAIL')
    if any(v <= 0 for v in param.values()): reasons.append('PARAMETER_STABILITY_FAIL')
    for required in ('bull','bear','range'):
        if required not in regimes: reasons.append(f'MISSING_REGIME_{required.upper()}')
    return ResearchValidationReport(
        _total_return(ins),_total_return(oos),float(wf.mean()),fee,slip,lat,param,regimes,
        bench_excess,len(oos),ess,psr,dsr,ci,holm_bonferroni_alpha(0.05,n_trials),not reasons,tuple(reasons)
    )
