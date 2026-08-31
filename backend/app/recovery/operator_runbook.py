from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryStep(str, Enum):
    RESTART_SERVICES = "RESTART_SERVICES"
    READ_DURABLE_DATABASE = "READ_DURABLE_DATABASE"
    FETCH_EXCHANGE_TRUTH = "FETCH_EXCHANGE_TRUTH"
    RECONCILE = "RECONCILE"
    IDENTIFY_OPEN_RISK = "IDENTIFY_OPEN_RISK"
    VERIFY_PROTECTIVE_ORDERS = "VERIFY_PROTECTIVE_ORDERS"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"
    RESUME_REDUCING_ONLY = "RESUME_REDUCING_ONLY"
    RESUME_ACTIVE = "RESUME_ACTIVE"


@dataclass(frozen=True)
class RecoveryEvidence:
    database_read_ok: bool
    exchange_truth_ok: bool
    reconciliation_drift: tuple[str, ...]
    open_risk_identified: bool
    protective_orders_ok: bool
    clock_ok: bool
    data_ok: bool
    human_approved: bool


@dataclass(frozen=True)
class RecoveryPlan:
    steps: tuple[RecoveryStep, ...]
    target_state: str
    reasons: tuple[str, ...]


def plan_operator_recovery(evidence: RecoveryEvidence) -> RecoveryPlan:
    steps = (
        RecoveryStep.RESTART_SERVICES,
        RecoveryStep.READ_DURABLE_DATABASE,
        RecoveryStep.FETCH_EXCHANGE_TRUTH,
        RecoveryStep.RECONCILE,
        RecoveryStep.IDENTIFY_OPEN_RISK,
        RecoveryStep.VERIFY_PROTECTIVE_ORDERS,
    )
    reasons: list[str] = []
    if not evidence.database_read_ok:
        reasons.append("DATABASE_READ_FAILED")
    if not evidence.exchange_truth_ok:
        reasons.append("EXCHANGE_TRUTH_UNAVAILABLE")
    if evidence.reconciliation_drift:
        reasons.append("RECONCILIATION_DRIFT")
    if not evidence.open_risk_identified:
        reasons.append("OPEN_RISK_NOT_IDENTIFIED")
    if not evidence.protective_orders_ok:
        reasons.append("PROTECTIVE_ORDERS_NOT_VERIFIED")
    if not evidence.clock_ok:
        reasons.append("CLOCK_NOT_HEALTHY")
    if not evidence.data_ok:
        reasons.append("MARKET_DATA_NOT_HEALTHY")

    if reasons:
        return RecoveryPlan(steps, "MANUAL_REVIEW_REQUIRED", tuple(reasons))
    if not evidence.human_approved:
        return RecoveryPlan(steps + (RecoveryStep.REQUIRE_HUMAN_APPROVAL,), "RECOVERY_PENDING", ("HUMAN_APPROVAL_REQUIRED",))
    return RecoveryPlan(
        steps + (RecoveryStep.REQUIRE_HUMAN_APPROVAL, RecoveryStep.RESUME_REDUCING_ONLY, RecoveryStep.RESUME_ACTIVE),
        "ACTIVE",
        (),
    )
