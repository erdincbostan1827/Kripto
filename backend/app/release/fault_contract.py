from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FaultKind(str, Enum):
    REST_TIMEOUT = "REST_TIMEOUT"
    DNS_FAILURE = "DNS_FAILURE"


@dataclass(frozen=True)
class FaultDecision:
    fault: FaultKind
    allow_new_risk: bool
    require_reconciliation: bool
    health: str
    reason: str


def evaluate_external_fault(fault: FaultKind) -> FaultDecision:
    if fault is FaultKind.REST_TIMEOUT:
        return FaultDecision(fault, False, True, "DEGRADED", "REST_OUTCOME_UNKNOWN")
    if fault is FaultKind.DNS_FAILURE:
        return FaultDecision(fault, False, True, "DOWN", "DNS_RESOLUTION_FAILED")
    raise ValueError("unsupported fault")
