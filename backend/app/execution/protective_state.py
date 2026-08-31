from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from .protection import protection_coverage

class ProtectionState(str,Enum):
    FLAT='FLAT'
    PENDING_ACK='PENDING_ACK'
    PROTECTED='PROTECTED'
    UNPROTECTED_POSITION='UNPROTECTED_POSITION'

@dataclass(frozen=True)
class ProtectionAssessment:
    state:ProtectionState
    required:Decimal
    covered:Decimal
    local_synthetic_only:bool
    allow_new_risk:bool
    required_action:str


def assess_protection(position_qty,position_side,orders,*,protective_submit_pending=False,local_synthetic_stop=False,panic_close=False):
    required=abs(Decimal(position_qty))
    if required==0:
        return ProtectionAssessment(ProtectionState.FLAT,required,Decimal('0'),False,True,'NONE')
    covered=protection_coverage(required,position_side,orders)
    if covered>=required:
        return ProtectionAssessment(ProtectionState.PROTECTED,required,covered,False,True,'NONE')
    if protective_submit_pending:
        return ProtectionAssessment(ProtectionState.PENDING_ACK,required,covered,local_synthetic_stop,False,'WAIT_FOR_EXCHANGE_ACK')
    action='PANIC_CLOSE' if panic_close else 'REDUCING_ONLY_AND_RETRY_PROTECTION'
    return ProtectionAssessment(ProtectionState.UNPROTECTED_POSITION,required,covered,local_synthetic_stop,False,action)

class ProtectiveOrderSupervisor:
    """Turns protection assessment into explicit operational side effects.

    Exchange ACK remains the source of truth. Retry/alarm callbacks are injected
    so the supervisor is testable and does not silently claim protection.
    """
    def __init__(self,risk_machine,retry_submit,alert):
        self.risk=risk_machine; self.retry_submit=retry_submit; self.alert=alert
    def enforce(self,position_qty,position_side,orders,*,local_synthetic_stop=False,panic_close=False):
        a=assess_protection(position_qty,position_side,orders,local_synthetic_stop=local_synthetic_stop,panic_close=panic_close)
        if a.state==ProtectionState.UNPROTECTED_POSITION:
            if panic_close:
                self.risk.halt('UNPROTECTED_POSITION_PANIC_CLOSE') if hasattr(self.risk,'halt') else self.risk.restrict('UNPROTECTED_POSITION_PANIC_CLOSE')
            else:
                self.risk.restrict('UNPROTECTED_POSITION')
                self.retry_submit()
            self.alert({'severity':'CRITICAL','code':'UNPROTECTED_POSITION','synthetic_only':a.local_synthetic_only,'action':a.required_action})
        return a
