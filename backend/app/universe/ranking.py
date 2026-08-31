from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RankedCandidate:
    symbol: str
    score: float
    confidence: float
    net_edge_bps: float
    listed_age_hours: float
    data_fresh: bool = True
    risk_blocked: bool = False


def rank_with_quarantine(items: list[RankedCandidate], *, min_listing_age_hours: float=24.0, limit: int=20) -> list[RankedCandidate]:
    if min_listing_age_hours < 0 or limit <= 0:
        raise ValueError('invalid scanner ranking policy')
    eligible = [x for x in items if x.data_fresh and not x.risk_blocked and x.net_edge_bps > 0 and x.listed_age_hours >= min_listing_age_hours]
    return sorted(eligible, key=lambda x:(-x.score,-x.confidence,-x.net_edge_bps,x.symbol))[:limit]

@dataclass(frozen=True)
class CrossSectionalRankInput:
    symbol:str
    calibrated_net_expectancy:float
    signal_confidence:float
    regime_alignment:float
    liquidity_quality:float
    expected_slippage_bps:float
    risk_reward:float
    volatility_suitability:float
    strategy_health:float
    diversification_benefit:float
    data_quality:float
    risk_budget:float
    eligible:bool=True
    signal:str='WATCH'
    blocking_reasons:tuple[str,...]=()

@dataclass(frozen=True)
class CrossSectionalRankResult:
    symbol:str
    rank:int
    rank_score:float
    eligible:bool
    signal:str
    net_expected_edge:float
    risk_budget:float
    blocking_reasons:tuple[str,...]
    correlation_penalty:float
    liquidity_penalty:float
    data_quality_score:float


def rank_cross_sectional(items:list[CrossSectionalRankInput])->list[CrossSectionalRankResult]:
    """Relative ranking with normalized inputs and explicit penalties/evidence."""
    if not items: return []
    def clamp(x): return max(0.0,min(1.0,float(x)))
    staged=[]
    for x in items:
        corr_penalty=max(0.0,1.0-clamp(x.diversification_benefit))
        liq_penalty=max(0.0,1.0-clamp(x.liquidity_quality))
        dataq=clamp(x.data_quality)
        slip_penalty=max(0.0,float(x.expected_slippage_bps))/100.0
        score=(
            1.8*float(x.calibrated_net_expectancy)+1.2*clamp(x.signal_confidence)+clamp(x.regime_alignment)
            +clamp(x.liquidity_quality)+0.8*max(0.0,float(x.risk_reward))/5.0+clamp(x.volatility_suitability)
            +clamp(x.strategy_health)+clamp(x.diversification_benefit)+dataq
            -corr_penalty-liq_penalty-slip_penalty
        )
        if not x.eligible or x.blocking_reasons: score-=1000
        staged.append((score,x,corr_penalty,liq_penalty,dataq))
    staged.sort(key=lambda z:(-z[0],z[1].symbol))
    return [CrossSectionalRankResult(x.symbol,i+1,score,x.eligible and not x.blocking_reasons,x.signal,x.calibrated_net_expectancy,x.risk_budget,x.blocking_reasons,corr,liq,dq) for i,(score,x,corr,liq,dq) in enumerate(staged)]
