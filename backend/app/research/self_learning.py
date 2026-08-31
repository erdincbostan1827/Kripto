from __future__ import annotations
from dataclasses import dataclass
from statistics import mean

@dataclass(frozen=True)
class ParameterProposal:
    parameter:str; current:float; proposed:float; reason:str; requires_paper_validation:bool=True; auto_promote_live:bool=False


def analyze_history(returns:list[float], *, baseline_expectancy:float, current_threshold:float)->dict:
    if not returns: return {"samples":0,"expectancy":0.0,"degraded":False,"proposals":()}
    expectancy=mean(returns); degraded=len(returns)>=30 and expectancy<baseline_expectancy
    proposals=()
    if degraded:
        # Proposal is deliberately bounded and review-only; no autonomous mutation.
        proposed=min(0.95,max(0.05,current_threshold+0.02))
        proposals=(ParameterProposal("signal_threshold",current_threshold,proposed,"EXPECTANCY_DEGRADATION"),)
    return {"samples":len(returns),"expectancy":expectancy,"degraded":degraded,"proposals":proposals}
