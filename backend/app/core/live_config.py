from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
import json

@dataclass(frozen=True)
class LiveProfile:
    timeframe:str; market_type:str; symbol:str; symbol_filter_version:str; max_risk_fraction:float
    def digest(self): return sha256(json.dumps(asdict(self),sort_keys=True,separators=(',',':')).encode()).hexdigest()

@dataclass(frozen=True)
class ConfigChange:
    old_value:object; new_value:object; actor:str; reason:str; timestamp:datetime; config_hash:str

def validate_profile(p:LiveProfile,*,allowed_timeframes,allowed_market_types,valid_symbols):
    return p.timeframe in allowed_timeframes and p.market_type in allowed_market_types and p.symbol in valid_symbols and 0<p.max_risk_fraction<=.1

def emergency_risk_change(p:LiveProfile,new_risk:float,*,actor,reason,ts)->tuple[LiveProfile,ConfigChange]:
    if not (0<=new_risk<=p.max_risk_fraction): raise ValueError('emergency change may only reduce risk')
    n=LiveProfile(p.timeframe,p.market_type,p.symbol,p.symbol_filter_version,new_risk)
    return n,ConfigChange(p.max_risk_fraction,new_risk,actor,reason,ts,n.digest())
