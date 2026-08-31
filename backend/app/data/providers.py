from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json

@dataclass(frozen=True)
class DataProviderPolicy:
    provider_id:str; data_type:str; official_source:str; license_tos:str
    redistribution_allowed:bool; attribution_requirements:str; retention_restrictions:str
    rate_limits:str; commercial_constraints:str; timezone_semantics:str; revision_vintage_semantics:str
    data_quality_owner:str; adapter_version:str

class DataProviderRegistry:
    def __init__(self): self._items={}
    def register(self,p:DataProviderPolicy)->None:
        if not p.provider_id or not p.official_source or not p.license_tos or not p.adapter_version: raise ValueError('provider governance metadata incomplete')
        old=self._items.get(p.provider_id)
        if old and old!=p: raise ValueError('provider policy change requires versioned provider_id or explicit migration')
        self._items[p.provider_id]=p
    def get(self,provider_id:str)->DataProviderPolicy: return self._items[provider_id]
    def snapshot(self)->dict:
        body=[asdict(self._items[k]) for k in sorted(self._items)]
        encoded=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
        return {'providers':body,'sha256':hashlib.sha256(encoded).hexdigest()}
    def assert_usage_allowed(self,provider_id:str,*,redistribute=False,commercial=False)->None:
        p=self.get(provider_id)
        if redistribute and not p.redistribution_allowed: raise PermissionError('provider policy forbids redistribution')
        if commercial and 'non-commercial' in p.commercial_constraints.lower(): raise PermissionError('provider policy forbids commercial use')
