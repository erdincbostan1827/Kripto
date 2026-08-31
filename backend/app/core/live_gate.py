from __future__ import annotations
from dataclasses import dataclass
from .enums import TradingMode

MANDATORY_GATES=("BACKTEST","OOS","WALK_FORWARD","PURGED_EMBARGO","ROBUSTNESS","PAPER","TESTNET","LIVE_SHADOW","EXECUTION_QUALITY","RISK","RECONCILIATION","SECURITY","HUMAN_APPROVAL")
@dataclass(frozen=True)
class LiveGateEvidence:
    release_id:str; gates:dict[str,bool]
    @property
    def approved(self)->bool: return all(self.gates.get(k,False) for k in MANDATORY_GATES)
    def blockers(self)->list[str]: return [k for k in MANDATORY_GATES if not self.gates.get(k,False)]

def require_live_gate(mode:TradingMode,evidence:LiveGateEvidence|None,confirmation_ok:bool)->None:
    if mode!=TradingMode.LIVE: return
    if evidence is None or not evidence.approved: raise PermissionError('LIVE evidence gates incomplete')
    if not confirmation_ok: raise PermissionError('LIVE human confirmation missing')
