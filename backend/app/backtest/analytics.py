from __future__ import annotations
from dataclasses import dataclass
import math
from statistics import mean, pstdev


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: float
    cagr: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    win_rate: float
    loss_rate: float
    profit_factor: float
    expectancy: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    average_holding_time: float
    number_of_trades: int


def performance_metrics(trades, *, initial_equity: float = 10000.0, elapsed_years: float = 1.0, periods_per_year: int = 252) -> PerformanceMetrics:
    if initial_equity <= 0 or elapsed_years <= 0 or periods_per_year <= 0:
        raise ValueError("invalid metric parameters")
    pnls = [float(t.pnl if hasattr(t, "pnl") else t["pnl"]) for t in trades]
    equity = initial_equity
    curve = [equity]
    for pnl in pnls:
        equity += pnl; curve.append(equity)
    total_return = equity/initial_equity - 1
    cagr = (max(equity, 1e-12)/initial_equity) ** (1/elapsed_years) - 1
    peaks=[]; peak=curve[0]; maxdd=0.0
    for x in curve:
        peak=max(peak,x); peaks.append(peak); maxdd=max(maxdd,(peak-x)/peak if peak>0 else 0.0)
    rets=[]
    for a,b in zip(curve,curve[1:]): rets.append((b-a)/a if a else 0.0)
    mu=mean(rets) if rets else 0.0; sd=pstdev(rets) if len(rets)>1 else 0.0
    downside=[min(0.0,x) for x in rets]; dsd=math.sqrt(mean([x*x for x in downside])) if downside else 0.0
    sharpe=mu/sd*math.sqrt(periods_per_year) if sd>0 else 0.0
    sortino=mu/dsd*math.sqrt(periods_per_year) if dsd>0 else 0.0
    calmar=cagr/maxdd if maxdd>0 else 0.0
    wins=[x for x in pnls if x>0]; losses=[x for x in pnls if x<0]
    pf=sum(wins)/abs(sum(losses)) if losses else (float("inf") if wins else 0.0)
    holds=[]
    for t in trades:
        a=getattr(t,"entry_time",None); b=getattr(t,"exit_time",None)
        try:
            delta=b-a
            holds.append(float(delta.total_seconds()) if hasattr(delta,"total_seconds") else float(delta))
        except (TypeError,ValueError,AttributeError):
            continue
    return PerformanceMetrics(
        total_return,cagr,sharpe,sortino,calmar,maxdd,
        len(wins)/len(pnls) if pnls else 0.0,
        len(losses)/len(pnls) if pnls else 0.0,
        pf,mean(pnls) if pnls else 0.0,mean(wins) if wins else 0.0,
        mean(losses) if losses else 0.0,max(wins) if wins else 0.0,
        min(losses) if losses else 0.0,mean(holds) if holds else 0.0,len(pnls)
    )


def sensitivity_analysis(parameter_values, evaluator):
    """Deterministic one-dimensional sensitivity evidence, sorted by parameter."""
    rows=[]
    for value in sorted(parameter_values):
        metric=float(evaluator(value))
        if not math.isfinite(metric): raise ValueError("non-finite sensitivity metric")
        rows.append({"parameter":value,"metric":metric})
    return rows
