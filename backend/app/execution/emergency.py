from __future__ import annotations
from dataclasses import dataclass
from app.core.enums import RiskState

@dataclass(frozen=True)
class EmergencyPolicy:
    close_positions_on_stop: bool = False
    cancel_unprotected_entry_orders: bool = True
    preserve_protective_orders: bool = True

@dataclass(frozen=True)
class EmergencyResult:
    risk_state: RiskState
    cancel_unprotected_entry_orders: bool
    preserve_protective_orders: bool
    close_positions: bool
    reason: str

class EmergencyController:
    def __init__(self, risk_machine, policy: EmergencyPolicy | None = None):
        self.risk = risk_machine
        self.policy = policy or EmergencyPolicy()

    def emergency_stop(self, reason: str = "OPERATOR_EMERGENCY_STOP") -> EmergencyResult:
        self.risk.halt(reason)
        return EmergencyResult(
            RiskState.HALTED,
            self.policy.cancel_unprotected_entry_orders,
            self.policy.preserve_protective_orders,
            self.policy.close_positions_on_stop,
            reason,
        )

    def panic_close(self, human_approved: bool, reason: str = "OPERATOR_PANIC_CLOSE") -> EmergencyResult:
        if not human_approved:
            raise PermissionError("panic close requires explicit human approval")
        self.risk.halt(reason)
        return EmergencyResult(RiskState.HALTED, True, True, True, reason)
