from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

MATERIAL_EVENTS={
 'SCHEDULED_LISTING','TRADING_ENABLED','TRADING_DISABLED','SUSPENSION','DELISTING','QUOTE_PAIR_REMOVAL',
 'TOKEN_RENAME','REDENOMINATION','CONTRACT_MIGRATION','CHAIN_MIGRATION','HARD_FORK','TICKER_CHANGE','MERGE_SPLIT_REBASE'
}

@dataclass(frozen=True)
class AssetLifecycleEvent:
    asset_id:str
    symbol:str
    event_type:str
    effective_at:datetime
    source:str
    details:dict=field(default_factory=dict)

@dataclass(frozen=True)
class LifecycleDecision:
    mode:str
    warn_user:bool
    verify_venue_rules:bool
    reducing_only:bool
    allow_new_risk:bool
    automatic_transfer_withdrawal:bool
    reasons:tuple[str,...]
    mapping_version:int

class AssetLifecycleManager:
    """Versioned, auditable asset lifecycle policy; never performs withdrawals/transfers."""
    def __init__(self):
        self._events:list[AssetLifecycleEvent]=[]; self._versions:dict[str,int]={}
    def record(self,event:AssetLifecycleEvent)->LifecycleDecision:
        if event.event_type not in MATERIAL_EVENTS: raise ValueError('unsupported lifecycle event')
        if event.effective_at.tzinfo is None: raise ValueError('effective_at must be timezone-aware')
        if not event.source: raise ValueError('source required')
        self._events.append(event)
        v=self._versions.get(event.asset_id,0)+1; self._versions[event.asset_id]=v
        severe=event.event_type in {'TRADING_DISABLED','SUSPENSION','DELISTING','QUOTE_PAIR_REMOVAL','CONTRACT_MIGRATION','CHAIN_MIGRATION','MERGE_SPLIT_REBASE'}
        metadata_change=event.event_type in {'TOKEN_RENAME','REDENOMINATION','CONTRACT_MIGRATION','CHAIN_MIGRATION','TICKER_CHANGE','MERGE_SPLIT_REBASE'}
        reasons=[event.event_type]
        if metadata_change: reasons.append('VERSIONED_MAPPING_CHANGE')
        return LifecycleDecision(
            mode='EXIT_OR_REDUCING_ONLY' if severe else 'REVALIDATE_BEFORE_NEW_RISK',
            warn_user=True,
            verify_venue_rules=True,
            reducing_only=severe,
            allow_new_risk=not severe and event.event_type not in {'SCHEDULED_LISTING'},
            automatic_transfer_withdrawal=False,
            reasons=tuple(reasons),
            mapping_version=v,
        )
    def history(self,asset_id:str)->tuple[AssetLifecycleEvent,...]:
        return tuple(e for e in self._events if e.asset_id==asset_id)
