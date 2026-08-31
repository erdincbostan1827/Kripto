from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class StrategyMetrics:
    name:str; total_return:float; max_drawdown:float; sharpe:float; sortino:float; profit_factor:float; stability:float; trades:int


def select_strategy(rows:list[StrategyMetrics], *, min_trades:int=30)->dict:
    """Transparent bounded ranking; never represents the winner as guaranteed profit."""
    eligible=[r for r in rows if r.trades>=min_trades and all(math.isfinite(float(x)) for x in (r.total_return,r.max_drawdown,r.sharpe,r.sortino,r.profit_factor,r.stability))]
    if not eligible: return {"selected":None,"scores":{},"guaranteed_profit":False,"reason":"INSUFFICIENT_EVIDENCE"}
    scores={}
    for r in eligible:
        # Conservative utility: reward return/risk quality and stability, penalize drawdown.
        score=(r.total_return*25)+(r.sharpe*12)+(r.sortino*8)+(min(r.profit_factor,3)*6)+(r.stability*10)-(r.max_drawdown*35)
        scores[r.name]=round(score,8)
    winner=max(eligible,key=lambda r:(scores[r.name],r.trades,r.name))
    return {"selected":winner.name,"scores":scores,"guaranteed_profit":False,"reason":"EVIDENCE_RANKING_ONLY"}
