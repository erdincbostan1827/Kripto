from __future__ import annotations

from dataclasses import dataclass, field
import time

from app.core.enums import RiskState


_ALLOWED_NEW_RISK = {RiskState.NORMAL, getattr(RiskState, "ACTIVE", RiskState.NORMAL)}


@dataclass(frozen=True)
class RecoveryChecks:
    data_healthy: bool = False
    exchange_healthy: bool = False
    private_stream_healthy: bool = False
    reconciliation_ok: bool = False
    no_orphan_orders: bool = False
    protective_orders_ok: bool = False
    risk_limits_ok: bool = False
    clock_ok: bool = False
    strategy_health_ok: bool = False

    @property
    def all_green(self) -> bool:
        return all(self.__dict__.values())


@dataclass
class RiskMachine:
    """Fail-closed operational risk-state controller.

    ``NORMAL`` is retained as a backwards-compatible local/PAPER alias. Production
    lifecycle states are explicit and recovery from HALTED/MANUAL_REVIEW_REQUIRED
    requires both green gates and human approval.
    """

    state: RiskState = RiskState.NORMAL
    reason: str = ""
    transition_log: list[tuple[str, str, str]] = field(default_factory=list)

    def _transition(self, target: RiskState, reason: str) -> None:
        previous = self.state
        self.state = target
        self.reason = reason
        self.transition_log.append((previous.value, target.value, reason))

    def halt(self, reason: str) -> None:
        self._transition(RiskState.HALTED, reason)

    def manual_review(self, reason: str) -> None:
        self._transition(RiskState.MANUAL_REVIEW_REQUIRED, reason)

    def reducing_only(self, reason: str) -> None:
        self._transition(RiskState.REDUCING_ONLY, reason)

    def restrict(self, reason: str) -> None:
        target = getattr(RiskState, "DEGRADED", RiskState.RESTRICTED)
        self._transition(target, reason)

    def recovery_pending(self, reason: str = "recovery checks pending") -> None:
        self._transition(getattr(RiskState, "RECOVERY_PENDING", RiskState.RESTRICTED), reason)

    def recover(
        self,
        human_approved: bool,
        checks_ok: bool | None = None,
        *,
        checks: RecoveryChecks | None = None,
        target: RiskState | None = None,
    ) -> None:
        green = checks.all_green if checks is not None else bool(checks_ok)
        if not human_approved or not green:
            self.recovery_pending("recovery requires human approval and green checks")
            raise PermissionError("recovery requires human approval and green checks")
        safe_target = target or RiskState.NORMAL
        active = getattr(RiskState, "ACTIVE", None)
        if active is not None and safe_target == active and self.state not in {
            getattr(RiskState, "RECOVERY_PENDING", RiskState.RESTRICTED),
            RiskState.RESTRICTED,
            getattr(RiskState, "DEGRADED", RiskState.RESTRICTED),
        }:
            raise PermissionError("ACTIVE recovery requires RECOVERY_PENDING/DEGRADED staging")
        self._transition(safe_target, "")

    def allow_new_risk(self) -> bool:
        return self.state in _ALLOWED_NEW_RISK

    def allowed_actions(self) -> frozenset[str]:
        if self.allow_new_risk():
            return frozenset({"OPEN", "REDUCE", "CANCEL", "CLOSE"})
        if self.state == RiskState.REDUCING_ONLY:
            return frozenset({"REDUCE", "CANCEL", "CLOSE"})
        if self.state in {RiskState.HALTED, RiskState.MANUAL_REVIEW_REQUIRED}:
            return frozenset({"CANCEL", "CLOSE", "RECOVER"})
        return frozenset({"REDUCE", "CANCEL", "CLOSE", "RECOVER"})


@dataclass
class RecoveryHysteresisGate:
    """Requires sustained healthy recovery evidence before ACTIVE is eligible.

    A single transient green sample is insufficient. Clock regressions fail closed.
    """
    min_healthy_seconds: float = 30.0
    min_consecutive_successes: int = 3
    first_green_at: float | None = None
    last_seen_at: float | None = None
    consecutive_successes: int = 0

    def observe(self, checks: RecoveryChecks, *, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else float(now)
        if self.last_seen_at is not None and now < self.last_seen_at:
            self.reset()
            raise ValueError("recovery clock moved backwards")
        self.last_seen_at = now
        if not checks.all_green:
            self.reset(keep_clock=True)
            return False
        if self.first_green_at is None:
            self.first_green_at = now
        self.consecutive_successes += 1
        return (
            self.consecutive_successes >= self.min_consecutive_successes
            and now - self.first_green_at >= self.min_healthy_seconds
        )

    def reset(self, *, keep_clock: bool = False) -> None:
        self.first_green_at = None
        self.consecutive_successes = 0
        if not keep_clock:
            self.last_seen_at = None
