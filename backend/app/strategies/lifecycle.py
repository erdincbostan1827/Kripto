from __future__ import annotations
from dataclasses import dataclass
STATES=('DRAFT','BACKTEST_VALIDATED','OOS_VALIDATED','PAPER_VALIDATED','TESTNET_VALIDATED','SHADOW_VALIDATED','LIVE_APPROVED')
EVIDENCE_BY_TARGET={'BACKTEST_VALIDATED':'backtest','OOS_VALIDATED':'oos','PAPER_VALIDATED':'paper','TESTNET_VALIDATED':'testnet','SHADOW_VALIDATED':'live_shadow','LIVE_APPROVED':'final_profitability'}
@dataclass
class StrategyLifecycle:
    strategy_id:str; state:str='DRAFT'
    def promote(self,target:str,evidence:dict,human_approved=False):
        if target not in STATES: raise ValueError('invalid lifecycle target')
        cur=STATES.index(self.state); nxt=STATES.index(target)
        if nxt!=cur+1: raise PermissionError('strategy lifecycle cannot skip validation stages')
        key=EVIDENCE_BY_TARGET[target]
        if not evidence.get(key,False): raise PermissionError(f'missing {key} evidence')
        if target=='LIVE_APPROVED' and not human_approved: raise PermissionError('human approval required')
        self.state=target; return self.state

@dataclass(frozen=True)
class StrategyVersionManifest:
    strategy_version:str
    config_hash:str
    git_commit_sha:str
    dataset_version:str
    indicator_version:str
    execution_model_version:str
    risk_model_version:str
    def validate(self):
        values=(self.strategy_version,self.config_hash,self.git_commit_sha,self.dataset_version,self.indicator_version,self.execution_model_version,self.risk_model_version)
        if any(not str(x).strip() for x in values): raise ValueError('strategy promotion provenance is incomplete')
        return self
