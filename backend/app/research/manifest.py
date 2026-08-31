from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

UTC=timezone.utc
@dataclass(frozen=True)
class ResearchPoint:
    name:str; observed_at:datetime; available_at:datetime
    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.available_at.tzinfo is None: raise ValueError("timestamps must be timezone-aware")
        if self.available_at < self.observed_at: raise ValueError("available_at before observed_at")

@dataclass(frozen=True)
class ResearchExperimentManifest:
    asset_universe_version:str; symbol_set:tuple[str,...]; strategy_version:str; parameter_search_space:dict[str,tuple]; feature_set:tuple[str,...]; timeframe_set:tuple[str,...]
    train_window:tuple[datetime,datetime]; oos_window:tuple[datetime,datetime]; primary_metric:str; as_of:datetime
    def __post_init__(self):
        if not all((self.asset_universe_version,self.symbol_set,self.strategy_version,self.feature_set,self.timeframe_set,self.primary_metric)): raise ValueError("complete research manifest required")
        if self.as_of.tzinfo is None: raise ValueError("as_of must be timezone-aware")
        if not self.train_window[0] < self.train_window[1] <= self.oos_window[0] < self.oos_window[1]: raise ValueError("train/OOS windows must be ordered and non-overlapping")
        if self.oos_window[1] > self.as_of: raise ValueError("research window extends beyond as_of")
    def assert_point_in_time_safe(self,points:Iterable[ResearchPoint])->None:
        for p in points:
            if p.available_at > self.as_of: raise ValueError(f"future information unavailable as-of: {p.name}")
    def assert_no_future_labels(self,*,universe_membership:ResearchPoint|None=None,market_cap_category:ResearchPoint|None=None,revised_metadata:ResearchPoint|None=None,liquidity_rank:ResearchPoint|None=None,intraday_eod:ResearchPoint|None=None)->None:
        self.assert_point_in_time_safe(x for x in (universe_membership,market_cap_category,revised_metadata,liquidity_rank,intraday_eod) if x is not None)
