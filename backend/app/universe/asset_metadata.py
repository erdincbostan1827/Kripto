from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

UTC=timezone.utc
TRUSTED_CONTRACT_SOURCES={"EXCHANGE_OFFICIAL","PROJECT_OFFICIAL","CHAIN_REGISTRY"}

def _aware(x:datetime|None)->datetime|None:
    if x is None: return None
    if x.tzinfo is None: raise ValueError("timezone-aware timestamp required")
    return x.astimezone(UTC)

@dataclass(frozen=True)
class AssetIdentityVersion:
    asset_id:str
    canonical_symbol:str
    display_name:str
    active_from:datetime
    active_to:datetime|None=None
    chain_network:str|None=None
    contract_identifier:str|None=None
    contract_source:str|None=None
    def __post_init__(self):
        object.__setattr__(self,"active_from",_aware(self.active_from)); object.__setattr__(self,"active_to",_aware(self.active_to))
        if not self.asset_id or not self.canonical_symbol or not self.display_name: raise ValueError("asset identity fields required")
        if self.active_to is not None and self.active_to <= self.active_from: raise ValueError("invalid asset validity range")
        if self.contract_identifier and self.contract_source not in TRUSTED_CONTRACT_SOURCES: raise ValueError("contract identifier requires trusted source")
        if self.contract_identifier and not self.chain_network: raise ValueError("contract identifier requires chain/network")

@dataclass(frozen=True)
class MarketIdentityVersion:
    exchange:str; market_type:str; symbol:str; base_asset_id:str; quote_asset_id:str
    contract_type:str; status:str; onboard_open_time:datetime; version_valid_from:datetime
    expire_delist_time:datetime|None=None; version_valid_to:datetime|None=None
    def __post_init__(self):
        for f in ("exchange","market_type","symbol","base_asset_id","quote_asset_id","contract_type","status"):
            if not getattr(self,f): raise ValueError(f"{f} required")
        for f in ("onboard_open_time","version_valid_from","expire_delist_time","version_valid_to"):
            object.__setattr__(self,f,_aware(getattr(self,f)))
        if self.version_valid_to and self.version_valid_to <= self.version_valid_from: raise ValueError("invalid market validity range")
        if self.expire_delist_time and self.expire_delist_time < self.onboard_open_time: raise ValueError("delist before onboard")

class AssetMetadataRegistry:
    def __init__(self): self.assets:list[AssetIdentityVersion]=[]; self.markets:list[MarketIdentityVersion]=[]
    @staticmethod
    def _contains(start,end,at): return start <= at and (end is None or at < end)
    def add_asset(self,v:AssetIdentityVersion):
        for e in self.assets:
            if e.asset_id==v.asset_id and max(e.active_from,v.active_from) < min(e.active_to or datetime.max.replace(tzinfo=UTC),v.active_to or datetime.max.replace(tzinfo=UTC)):
                raise ValueError("overlapping asset identity versions")
        self.assets.append(v)
    def add_market(self,v:MarketIdentityVersion):
        for e in self.markets:
            if e.exchange==v.exchange and e.market_type==v.market_type and e.symbol==v.symbol and max(e.version_valid_from,v.version_valid_from) < min(e.version_valid_to or datetime.max.replace(tzinfo=UTC),v.version_valid_to or datetime.max.replace(tzinfo=UTC)):
                raise ValueError("overlapping market identity versions")
        self.markets.append(v)
    def asset_as_of(self,asset_id:str,at:datetime)->AssetIdentityVersion:
        at=_aware(at); xs=[v for v in self.assets if v.asset_id==asset_id and self._contains(v.active_from,v.active_to,at)]
        if len(xs)!=1: raise LookupError("asset identity unavailable or ambiguous as-of timestamp")
        return xs[0]
    def market_as_of(self,exchange:str,market_type:str,symbol:str,at:datetime)->MarketIdentityVersion:
        at=_aware(at); xs=[v for v in self.markets if (v.exchange,v.market_type,v.symbol)==(exchange,market_type,symbol) and self._contains(v.version_valid_from,v.version_valid_to,at)]
        if len(xs)!=1: raise LookupError("market identity unavailable or ambiguous as-of timestamp")
        return xs[0]
