from __future__ import annotations

from dataclasses import dataclass
from app.core.enums import RiskState


@dataclass(frozen=True)
class ExchangeFailureResult:
    risk_state: RiskState
    protection_verified: bool
    alert_delivered: bool
    reconnect_attempted: bool


class ExchangeFailureCoordinator:
    """Fail-closed exchange outage orchestration.

    New risk is halted first. Protective-order verification and alerting are
    attempted independently, then reconnect is attempted. Failures never reopen
    risk automatically.
    """

    def __init__(self, risk_machine, *, protection_check, critical_alert, reconnect):
        self.risk = risk_machine
        self.protection_check = protection_check
        self.critical_alert = critical_alert
        self.reconnect = reconnect

    def handle(self, reason: str = "EXCHANGE_UNAVAILABLE") -> ExchangeFailureResult:
        self.risk.halt(reason)
        protection_verified = False
        alert_delivered = False
        reconnect_attempted = False
        try:
            protection_verified = bool(self.protection_check())
        except Exception:
            protection_verified = False
        try:
            self.critical_alert(f"CRITICAL: {reason}; new risk halted; protection_verified={protection_verified}")
            alert_delivered = True
        except Exception:
            alert_delivered = False
        try:
            reconnect_attempted = True
            self.reconnect()
        except Exception:
            reconnect_attempted = True
        return ExchangeFailureResult(self.risk.state, protection_verified, alert_delivered, reconnect_attempted)
