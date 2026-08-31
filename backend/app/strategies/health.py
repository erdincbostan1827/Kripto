from __future__ import annotations
from dataclasses import dataclass
import statistics
@dataclass(frozen=True)
class HealthAssessment:
    degraded:bool; reasons:tuple[str,...]; action:str
class StrategyHealthMonitor:
    def __init__(self,z_threshold=2.5,min_samples=30): self.z_threshold=float(z_threshold); self.min_samples=int(min_samples)
    def assess(self,baseline_returns,current_returns,baseline_slippage,current_slippage):
        if len(baseline_returns)<self.min_samples or len(current_returns)<self.min_samples: return HealthAssessment(False,('INSUFFICIENT_SAMPLE',),'KEEP_CURRENT_RISK')
        mu=statistics.mean(baseline_returns); sd=statistics.pstdev(baseline_returns) or 1e-12; cur=statistics.mean(current_returns); z=(cur-mu)/sd; reasons=[]
        if z<=-self.z_threshold: reasons.append('EXPECTANCY_DECAY')
        if current_slippage>max(baseline_slippage*1.5,baseline_slippage+1e-9): reasons.append('SLIPPAGE_DRIFT')
        degraded=bool(reasons); return HealthAssessment(degraded,tuple(reasons),'REDUCE_RISK_AND_RESEARCH_REVIEW' if degraded else 'KEEP_CURRENT_RISK')
