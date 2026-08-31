from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import dataclass
from math import sqrt

@dataclass(frozen=True)
class AttributionTrade:
    asset:str; strategy:str; pnl:float; notional:float; position_count:int; was_delisted:bool=False; selection_rank:int|None=None

@dataclass(frozen=True)
class PerformanceAttribution:
    per_asset_contribution:dict[str,float]; per_strategy_contribution:dict[str,float]; turnover:float; concentration:float
    average_concurrent_positions:float; maximum_concurrent_positions:int; correlation_adjusted_drawdown:float
    universe_turnover:float; excluded_symbol_reason_distribution:dict[str,int]; delisted_asset_contribution:float; selection_ranking_attribution:dict[int,float]

def build_attribution(*,trades:list[AttributionTrade],portfolio_equity:float,drawdown:float,average_pairwise_correlation:float,universe_added:int,universe_removed:int,universe_size:int,excluded_reasons:list[str],missing_data_policy:str)->PerformanceAttribution:
    if portfolio_equity<=0 or universe_size<=0: raise ValueError("positive denominators required")
    if missing_data_policy not in {"EXCLUDE_AND_REPORT","FAIL_CLOSED"}: raise ValueError("explicit missing-data policy required")
    if not -1 <= average_pairwise_correlation <= 1: raise ValueError("invalid correlation")
    pa=defaultdict(float); ps=defaultdict(float); ranks=defaultdict(float)
    for t in trades:
        pa[t.asset]+=t.pnl; ps[t.strategy]+=t.pnl
        if t.selection_rank is not None: ranks[t.selection_rank]+=t.pnl
    turnover=sum(abs(t.notional) for t in trades)/portfolio_equity
    gross=sum(abs(v) for v in pa.values())
    concentration=(max((abs(v) for v in pa.values()),default=0.0)/gross) if gross else 0.0
    counts=[t.position_count for t in trades]
    corr_adj=abs(drawdown)*sqrt(max(0.0,1.0+average_pairwise_correlation))
    return PerformanceAttribution(dict(pa),dict(ps),turnover,concentration,sum(counts)/len(counts) if counts else 0.0,max(counts,default=0),corr_adj,(universe_added+universe_removed)/universe_size,dict(Counter(excluded_reasons)),sum(t.pnl for t in trades if t.was_delisted),dict(ranks))
