from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class ApiVersionPolicy:
    current_version:str='v1'
    compatibility_window_days:int=180
    deprecation_warning_days:int=90
    def validate(self):
        if self.compatibility_window_days < self.deprecation_warning_days: raise ValueError('compatibility window must cover warning window')
        if self.deprecation_warning_days < 1: raise ValueError('deprecation warning must be positive')
        return self

@dataclass(frozen=True)
class DeprecationNotice:
    version:str
    announced_on:date
    sunset_on:date
    replacement_version:str
    breaking_reason:str

class ApiVersionRegistry:
    def __init__(self,policy:ApiVersionPolicy): self.policy=policy.validate(); self._notices={}
    def deprecate(self,notice:DeprecationNotice):
        days=(notice.sunset_on-notice.announced_on).days
        if days < self.policy.deprecation_warning_days: raise ValueError('deprecation notice window too short')
        if not notice.breaking_reason.strip(): raise ValueError('breaking-change reason required')
        self._notices[notice.version]=notice; return notice
    def headers(self,version:str,today:date):
        n=self._notices.get(version)
        if not n:return {}
        return {'Deprecation':'true','Sunset':n.sunset_on.isoformat(),'Link':f'</api/{n.replacement_version}>; rel="successor-version"'}
    @staticmethod
    def is_breaking_change(*, removes_field=False, changes_semantics=False, narrows_allowed_values=False, changes_auth=False):
        return any((removes_field,changes_semantics,narrows_allowed_values,changes_auth))
