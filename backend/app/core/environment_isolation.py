from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EnvironmentBoundary:
    name:str
    database_namespace:str
    redis_namespace:str
    exchange_key_identity:str
    webhook_endpoint_id:str
    encryption_key_id:str
    uses_real_capital:bool=False


def validate_environment_isolation(*envs:EnvironmentBoundary)->tuple[str,...]:
    """Reject shared mutable/security namespaces across DEV/STAGING/PROD."""
    if len({e.name for e in envs})!=len(envs): raise ValueError('duplicate environment name')
    fields=('database_namespace','redis_namespace','exchange_key_identity','webhook_endpoint_id','encryption_key_id')
    issues=[]
    for field in fields:
        seen={}
        for e in envs:
            value=getattr(e,field)
            if not value: issues.append(f'MISSING_{field.upper()}:{e.name}')
            elif value in seen: issues.append(f'SHARED_{field.upper()}:{seen[value]}:{e.name}')
            else: seen[value]=e.name
    for e in envs:
        if e.name.upper() in {'DEV','STAGING'} and e.uses_real_capital:
            issues.append(f'NON_PROD_REAL_CAPITAL_FORBIDDEN:{e.name}')
    return tuple(sorted(issues))
