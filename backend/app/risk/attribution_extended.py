from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable,Mapping

@dataclass(frozen=True)
class TradeAttribution:
    strategy:str; strategy_version:str; regime:str; volatility_bucket:str; timeframe:str; direction:str; confidence_bucket:str
    signal_score_bucket:str; hour:int; day_of_week:int; weekend:bool; execution_type:str; maker_taker:str; liquidity_bucket:str; data_quality_bucket:str
    entry_timing:float; exit_timing:float; fees:float; funding_borrow:float; adverse_selection:float; missed_fill:float; stop_gap_loss:float; data_latency_loss:float
    @property
    def execution_drag(self): return sum(map(abs,(self.fees,self.funding_borrow,self.adverse_selection,self.missed_fill,self.stop_gap_loss,self.data_latency_loss)))
    @property
    def strategy_contribution(self): return self.entry_timing+self.exit_timing

def diagnose(t:TradeAttribution)->str:
    if t.data_latency_loss<-.001: return 'DATA_LATENCY'
    if t.execution_drag>abs(t.strategy_contribution): return 'EXECUTION_OR_COST'
    return 'STRATEGY'

def group_performance(rows:Iterable[TradeAttribution],field:str)->Mapping[object,float]:
    g=defaultdict(list)
    for r in rows: g[getattr(r,field)].append(r.strategy_contribution-r.execution_drag)
    return {k:sum(v)/len(v) for k,v in g.items()}
