from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
RISK_INCREASING_KEYS={'risk_per_trade','max_daily_loss','max_weekly_loss','max_drawdown','max_portfolio_exposure','max_single_asset_exposure','max_open_positions'}
def config_hash(config:dict): return hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class ConfigChangeAssessment:
    risk_increasing:bool; changed_keys:tuple[str,...]; old_hash:str; new_hash:str

def assess_change(old:dict,new:dict):
    changed=tuple(sorted(k for k in set(old)|set(new) if old.get(k)!=new.get(k))); increasing=False
    for k in changed:
        if k in RISK_INCREASING_KEYS:
            try: increasing=increasing or float(new.get(k,0))>float(old.get(k,0))
            except Exception: increasing=True
    return ConfigChangeAssessment(increasing,changed,config_hash(old),config_hash(new))

@dataclass(frozen=True)
class LiveConfigDecision:
    allowed: bool
    requires_restart: bool
    requires_human_approval: bool
    reason: str
    assessment: ConfigChangeAssessment

class LiveConfigGuard:
    """Immutable LIVE config boundary: runtime risk increases never hot-apply."""
    def __init__(self, active_config: dict):
        self.active_config=dict(active_config); self.active_hash=config_hash(self.active_config)
    def evaluate(self, candidate: dict) -> LiveConfigDecision:
        a=assess_change(self.active_config,candidate)
        if not a.changed_keys:
            return LiveConfigDecision(True,False,False,'NO_CHANGE',a)
        if a.risk_increasing:
            return LiveConfigDecision(False,True,True,'RISK_INCREASING_CONFIG_REQUIRES_APPROVED_RESTART',a)
        return LiveConfigDecision(False,True,False,'LIVE_CONFIG_CHANGE_REQUIRES_RESTART',a)
    def require_unchanged(self, candidate: dict) -> None:
        if config_hash(candidate)!=self.active_hash: raise PermissionError('LIVE config mutated at runtime')

@dataclass(frozen=True)
class ConfigValidation:
    valid: bool
    errors: tuple[str,...]

def validate_risk_config(config: dict, *, risk_per_trade_hard_cap: float=0.05) -> ConfigValidation:
    errors=[]
    rpt=float(config.get('risk_per_trade',0))
    if not (0 < rpt <= risk_per_trade_hard_cap): errors.append('RISK_PER_TRADE_OUT_OF_RANGE')
    if float(config.get('min_risk_reward',1)) <= 0: errors.append('MIN_RISK_REWARD_INVALID')
    daily=float(config.get('max_daily_loss',0)); drawdown=float(config.get('max_drawdown',0))
    if daily < 0 or drawdown < 0 or daily > drawdown: errors.append('LOSS_DRAWDOWN_RELATION_INVALID')
    alloc=config.get('tp_allocations')
    if alloc is not None and abs(sum(float(x) for x in alloc)-1.0)>1e-9: errors.append('TP_ALLOCATION_SUM_INVALID')
    return ConfigValidation(not errors,tuple(errors))
