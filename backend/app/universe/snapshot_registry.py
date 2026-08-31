from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class UniverseMemberRecord:
    exchange:str; market_type:str; symbol:str; base_asset:str; first_seen_at:datetime; observed_at:datetime; available_at:datetime
    listing_open_time:datetime|None=None; inclusion_reason:str|None=None; exclusion_reason:str|None=None
    def __post_init__(self):
        for f in ('exchange','market_type','symbol','base_asset'):
            if not getattr(self,f): raise ValueError(f'{f} required')
        for f in ('first_seen_at','observed_at','available_at','listing_open_time'):
            v=getattr(self,f)
            if v is not None and v.tzinfo is None: raise ValueError('timezone-aware timestamps required')
        if self.available_at < self.observed_at: raise ValueError('available_at before observed_at')
        if bool(self.inclusion_reason)==bool(self.exclusion_reason): raise ValueError('exactly one inclusion/exclusion reason required')

@dataclass(frozen=True)
class UniverseSnapshotRecord:
    snapshot_id:str; mode:str; as_of:datetime; members:tuple[UniverseMemberRecord,...]

class PointInTimeUniverseRegistry:
    MODES={'DYNAMIC_EXCHANGE_UNIVERSE','RESEARCH_SNAPSHOT'}
    def __init__(self): self._snapshots:dict[str,UniverseSnapshotRecord]={}
    def create(self,*,snapshot_id:str,mode:str,as_of:datetime,records:list[UniverseMemberRecord])->UniverseSnapshotRecord:
        if mode not in self.MODES: raise ValueError('unsupported universe mode')
        if as_of.tzinfo is None: raise ValueError('as_of timezone required')
        if snapshot_id in self._snapshots: raise ValueError('snapshot immutable')
        for r in records:
            if r.available_at > as_of: raise ValueError('future membership evidence unavailable as-of')
        s=UniverseSnapshotRecord(snapshot_id,mode,as_of,tuple(records)); self._snapshots[snapshot_id]=s; return s
    def eligible_symbols(self,snapshot_id:str)->tuple[str,...]:
        s=self._snapshots[snapshot_id]
        return tuple(sorted(r.symbol for r in s.members if r.inclusion_reason))
