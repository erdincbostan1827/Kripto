from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean
from typing import Mapping, Sequence


@dataclass(frozen=True)
class DynamicRiskBudget:
    base_fraction: float
    realized_volatility_ratio: float
    drawdown_fraction: float
    liquidity_score: float
    strategy_health: float
    recovery_fraction: float = 1.0
    version: str = "1.0"

    def fraction(self) -> float:
        base=max(0.0,min(1.0,self.base_fraction))
        vol=1.0/max(1.0,self.realized_volatility_ratio)
        dd=max(0.0,1.0-min(1.0,self.drawdown_fraction)*2.0)
        liq=max(0.0,min(1.0,self.liquidity_score)); health=max(0.0,min(1.0,self.strategy_health))
        recovery=max(0.0,min(1.0,self.recovery_fraction))
        return max(0.0,min(base,base*vol*dd*liq*health*recovery))


def bounded_fractional_kelly(win_probability: float, payoff_ratio: float, *, enabled: bool = False, fraction: float = 0.25, hard_cap: float = 0.05) -> float:
    if not enabled:
        return 0.0
    if not (0 < win_probability < 1) or payoff_ratio <= 0:
        return 0.0
    full=(payoff_ratio*win_probability-(1-win_probability))/payoff_ratio
    return max(0.0,min(hard_cap,full*max(0.0,min(1.0,fraction))))


def aggregate_risk(stop_risks: Sequence[float], correlation_penalty: float = 0.0) -> float:
    return max(0.0,sum(max(0.0,x) for x in stop_risks)*(1+max(0.0,min(1.0,correlation_penalty))))


@dataclass(frozen=True)
class TailMetrics:
    var: float
    expected_shortfall: float
    downside_deviation: float
    worst_rolling_return: float
    max_drawdown: float
    drawdown_duration: int
    tail_ratio: float | None


def tail_metrics(returns: Sequence[float], alpha: float = 0.05) -> TailMetrics:
    if len(returns) < 2:
        raise ValueError("insufficient returns")
    xs=sorted(float(x) for x in returns); n=max(1,int(len(xs)*alpha)); tail=xs[:n]
    var=-tail[-1]; es=-mean(tail)
    downs=[min(0.0,x) for x in xs]; downside=sqrt(mean([x*x for x in downs]))
    equity=1.0; peak=1.0; maxdd=0.0; dur=maxdur=0
    for r in returns:
        equity*=1+r; peak=max(peak,equity)
        dd=(peak-equity)/peak
        if dd>0: dur+=1; maxdur=max(maxdur,dur)
        else: dur=0
        maxdd=max(maxdd,dd)
    pos=[x for x in xs if x>0]; neg=[abs(x) for x in xs if x<0]
    tr=(mean(pos)/mean(neg)) if pos and neg and mean(neg)>0 else None
    return TailMetrics(var,es,downside,min(xs),maxdd,maxdur,tr)


STRESS_SCENARIOS=frozenset({
    "FLASH_CRASH","SUDDEN_GAP","SPREAD_WIDENING","LIQUIDITY_COLLAPSE","API_LATENCY_SPIKE",
    "PRIVATE_STREAM_DISCONNECT","EXCHANGE_PARTIAL_OUTAGE","STABLECOIN_DEPEG","FUNDING_SPIKE",
    "MARK_INDEX_DIVERGENCE","LIQUIDATION_CASCADE","DATABASE_REDIS_FAILURE_OPEN_POSITION",
})


def stress_loss(exposure: float, shocks: Mapping[str,float], liquidity_multiplier: float = 1.0) -> dict[str,float]:
    return {k: abs(exposure)*abs(float(v))*max(1.0,liquidity_multiplier) for k,v in shocks.items() if k in STRESS_SCENARIOS}


@dataclass(frozen=True)
class QuoteAssetState:
    symbol: str
    parity: float
    venue_dislocation_bps: float
    custody_concentration: float
    idle_balance_concentration: float
    withdrawals_enabled: bool | None = None
    deposits_enabled: bool | None = None


def quote_asset_policy(state: QuoteAssetState, *, depeg_threshold: float = 0.01, concentration_cap: float = 0.60) -> tuple[str,tuple[str,...]]:
    reasons=[]
    if abs(state.parity-1.0)>depeg_threshold: reasons.append("DEPEG")
    if state.venue_dislocation_bps>100: reasons.append("VENUE_DISLOCATION")
    if state.custody_concentration>concentration_cap: reasons.append("CUSTODY_CONCENTRATION")
    if state.idle_balance_concentration>concentration_cap: reasons.append("IDLE_BALANCE_CONCENTRATION")
    if state.withdrawals_enabled is False or state.deposits_enabled is False: reasons.append("TRANSFER_STATUS_DEGRADED")
    if reasons:
        return "REDUCE_ONLY",tuple(reasons)
    return "ALLOW_NEW_ENTRY",()
