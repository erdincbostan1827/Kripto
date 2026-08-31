from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class StrategyVote:
    name: str
    vote: int  # -1 sell, 0 abstain, +1 buy
    confidence: float

STRATEGY_FAMILIES=("TREND_FOLLOWING","BREAKOUT","PULLBACK","MEAN_REVERSION","MOMENTUM")

def ensemble_vote(votes:list[StrategyVote], *, min_agreement:float=0.60)->dict:
    if not votes: return {"decision":"NO_TRADE","agreement":0.0,"contributors":()}
    if any(v.name not in STRATEGY_FAMILIES or v.vote not in {-1,0,1} or not 0<=v.confidence<=1 for v in votes):
        raise ValueError("invalid strategy vote")
    weighted=sum(v.vote*v.confidence for v in votes); total=sum(v.confidence for v in votes)
    agreement=abs(weighted)/total if total else 0.0
    decision="BUY" if weighted>0 and agreement>=min_agreement else "SELL" if weighted<0 and agreement>=min_agreement else "NO_TRADE"
    return {"decision":decision,"agreement":agreement,"contributors":tuple(v.name for v in votes)}
