from __future__ import annotations
from dataclasses import dataclass

VALID={'PASS','FAIL','SKIPPED'}
@dataclass(frozen=True)
class AcceptanceCaseEvidence:
    case_id:str; status:str; test_environment:str; exact_reason:str; evidence_reference:str; known_limitation:str|None; executed:bool
    def __post_init__(self):
        if self.status not in VALID: raise ValueError('invalid acceptance status')
        if not all((self.case_id,self.test_environment,self.exact_reason,self.evidence_reference)): raise ValueError('complete evidence required')
        if self.status=='PASS' and not self.executed: raise ValueError('written-but-not-executed test cannot PASS')

@dataclass(frozen=True)
class MultiAssetAcceptanceSnapshot:
    reserved_balance_ok:bool; drawdown_adaptive_allocation_ok:bool; same_symbol_duplicate_prevention_ok:bool; backpressure_under_burst_ok:bool
    memory_soak_ok:bool; representative_liquidity_classes_ok:bool; multi_position_reconciliation_ok:bool; multi_symbol_order_fill_ok:bool; quote_asset_risk_ok:bool
    unresolved_critical_incidents:int; human_approval_ok:bool; evidence:tuple[AcceptanceCaseEvidence,...]
    def blockers(self)->tuple[str,...]:
        b=[]
        checks=(('RESERVED_BALANCE',self.reserved_balance_ok),('DRAWDOWN_ADAPTIVE_ALLOCATION',self.drawdown_adaptive_allocation_ok),('DUPLICATE_PREVENTION',self.same_symbol_duplicate_prevention_ok),('BACKPRESSURE',self.backpressure_under_burst_ok),('MEMORY_SOAK',self.memory_soak_ok),('LIQUIDITY_CLASSES',self.representative_liquidity_classes_ok),('MULTI_POSITION_RECONCILIATION',self.multi_position_reconciliation_ok),('MULTI_SYMBOL_ORDER_FILL',self.multi_symbol_order_fill_ok),('QUOTE_ASSET_RISK',self.quote_asset_risk_ok),('HUMAN_APPROVAL',self.human_approval_ok))
        b.extend(k for k,v in checks if not v)
        if self.unresolved_critical_incidents!=0: b.append('UNRESOLVED_CRITICAL_INCIDENTS')
        if not self.evidence or any(e.status!='PASS' for e in self.evidence): b.append('ACCEPTANCE_EVIDENCE_NOT_ALL_PASS')
        return tuple(b)
    def assert_accepted(self):
        b=self.blockers()
        if b: raise RuntimeError(','.join(b))
