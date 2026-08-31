from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import RiskState
from app.execution.reconciliation import AccountSnapshot, ReconciliationResult, reconcile
from app.risk.state import RecoveryChecks, RiskMachine


@dataclass(frozen=True)
class RestartRecoveryEvidence:
    reconciliation: ReconciliationResult
    checks: RecoveryChecks
    human_approved: bool

    @property
    def ready_for_active(self) -> bool:
        return not self.reconciliation.drift and self.checks.all_green and self.human_approved


class RestartRecoveryCoordinator:
    """Fail-closed startup/restart recovery gate.

    A restarted process begins in RECOVERY_PENDING. It must compare the durable
    local snapshot with the exchange snapshot and satisfy all recovery gates.
    Drift moves the system to MANUAL_REVIEW_REQUIRED. ACTIVE can only be reached
    after explicit human approval and green checks.
    """

    def __init__(self, risk_machine: RiskMachine | None = None):
        self.risk = risk_machine or RiskMachine(state=RiskState.STARTING, reason="process startup")
        self.last_evidence: RestartRecoveryEvidence | None = None

    def begin(self) -> None:
        self.risk.recovery_pending("restart reconciliation required")

    def evaluate(
        self,
        *,
        local: AccountSnapshot,
        exchange: AccountSnapshot,
        checks: RecoveryChecks,
        human_approved: bool,
    ) -> RestartRecoveryEvidence:
        if self.risk.state not in {RiskState.STARTING, RiskState.RECOVERY_PENDING, RiskState.MANUAL_REVIEW_REQUIRED}:
            raise PermissionError("restart recovery can only run from startup/recovery states")

        result = reconcile(local, exchange)
        effective_checks = RecoveryChecks(
            data_healthy=checks.data_healthy,
            exchange_healthy=checks.exchange_healthy,
            private_stream_healthy=checks.private_stream_healthy,
            reconciliation_ok=checks.reconciliation_ok and not result.drift,
            no_orphan_orders=checks.no_orphan_orders and not any(item.startswith(("UNKNOWN_ORDER:", "MISSING_EXCHANGE_ORDER:")) for item in result.drift),
            protective_orders_ok=checks.protective_orders_ok,
            risk_limits_ok=checks.risk_limits_ok,
            clock_ok=checks.clock_ok,
            strategy_health_ok=checks.strategy_health_ok,
        )
        evidence = RestartRecoveryEvidence(result, effective_checks, human_approved)
        self.last_evidence = evidence

        if result.drift:
            self.risk.manual_review("restart reconciliation drift: " + ",".join(result.drift))
            return evidence

        if not human_approved or not effective_checks.all_green:
            self.risk.recovery_pending("restart recovery gates incomplete")
            return evidence

        # Stage through RECOVERY_PENDING explicitly; RiskMachine forbids a direct
        # HALTED/STARTING -> ACTIVE transition.
        if self.risk.state != RiskState.RECOVERY_PENDING:
            self.risk.recovery_pending("restart recovery gates passed")
        self.risk.recover(human_approved=True, checks=effective_checks, target=RiskState.ACTIVE)
        return evidence

@dataclass(frozen=True)
class DurableOrderRecovery:
    intent_id: str
    status: str
    ordered_quantity: str
    filled_quantity: str
    remaining_quantity: str
    consistent: bool


def recover_durable_order(session_factory, intent_id: str) -> DurableOrderRecovery:
    """Reconstruct an order after restart from committed order/fill rows.

    Fill rows are authoritative for executed quantity. Contradictory durable
    status (for example FILLED with only a partial fill) is marked inconsistent
    so startup recovery can remain fail-closed.
    """
    from decimal import Decimal
    from sqlalchemy import select
    from app.database.models import Order, Fill

    with session_factory() as session:
        order = session.scalar(select(Order).where(Order.intent_id == intent_id))
        if order is None:
            raise LookupError(f'unknown durable intent: {intent_id}')
        fills = session.scalars(select(Fill).where(Fill.order_id == order.id)).all()
        filled = sum((Decimal(str(row.quantity)) for row in fills), Decimal('0'))
        quantity = Decimal(str(order.quantity))
        remaining = max(Decimal('0'), quantity - filled)
        status = str(order.status)
        consistent = filled <= quantity
        if status == 'FILLED':
            consistent = consistent and filled == quantity
        if status in {'CREATED', 'SUBMITTED', 'ACKNOWLEDGED'}:
            consistent = consistent and filled == 0
        if status == 'PARTIALLY_FILLED':
            consistent = consistent and Decimal('0') < filled < quantity
        return DurableOrderRecovery(
            intent_id=intent_id,
            status=status,
            ordered_quantity=str(quantity),
            filled_quantity=str(filled),
            remaining_quantity=str(remaining),
            consistent=consistent,
        )

@dataclass(frozen=True)
class PrivateStreamReconnectEvidence:
    reconciliation: ReconciliationResult
    stream_healthy: bool
    requires_human_review: bool


class PrivateStreamRecoveryCoordinator:
    """REST truth reconciliation after private-stream disconnect/reconnect."""

    def __init__(self, risk_machine: RiskMachine, local_snapshot_provider):
        self.risk = risk_machine
        self.local_snapshot_provider = local_snapshot_provider
        self.disconnected = False
        self.auth_expired = False
        self.last_evidence: PrivateStreamReconnectEvidence | None = None

    def on_disconnect(self, reason: str = 'PRIVATE_STREAM_DISCONNECTED') -> None:
        self.disconnected = True
        self.risk.restrict(reason)

    def on_auth_expired(self) -> None:
        self.auth_expired = True
        self.disconnected = True
        self.risk.restrict('PRIVATE_STREAM_AUTH_EXPIRED')

    def on_reconnect(self, exchange, *, stream_healthy: bool, auth_refreshed: bool = True) -> PrivateStreamReconnectEvidence:
        local = self.local_snapshot_provider()
        balances = {k: v for k, v in exchange.get_balance().items()}
        positions_raw = exchange.get_positions()
        if isinstance(positions_raw, dict):
            positions = positions_raw
        else:
            positions = {}
            for item in positions_raw:
                if isinstance(item, dict):
                    symbol = item.get('symbol')
                    quantity = item.get('quantity', 0)
                else:
                    symbol = getattr(item, 'symbol', None)
                    quantity = getattr(item, 'quantity', 0)
                if symbol:
                    positions[str(symbol)] = quantity
        open_orders = exchange.get_open_orders()
        open_ids = {str(order.exchange_order_id) for order in open_orders if order.exchange_order_id is not None}
        remote = AccountSnapshot(balances=balances, positions=positions, open_order_ids=open_ids)
        result = reconcile(local, remote)
        auth_ok = (not self.auth_expired) or auth_refreshed
        effective_stream_healthy = stream_healthy and auth_ok
        requires_review = bool(result.drift) or not effective_stream_healthy
        evidence = PrivateStreamReconnectEvidence(result, effective_stream_healthy, requires_review)
        self.last_evidence = evidence
        self.disconnected = False
        if auth_ok:
            self.auth_expired = False
        if result.drift:
            self.risk.manual_review('PRIVATE_STREAM_RECONNECT_DRIFT:' + ','.join(result.drift))
        elif not effective_stream_healthy:
            self.risk.recovery_pending('private stream reconnect/auth not healthy')
        else:
            self.risk.recovery_pending('private stream reconciled; recovery approval required')
        return evidence

@dataclass(frozen=True)
class StreamFreshnessEvidence:
    healthy: bool
    age_seconds: float
    reason: str

def validate_private_stream_freshness(*, now_monotonic: float, last_message_monotonic: float | None, max_age_seconds: float) -> StreamFreshnessEvidence:
    if last_message_monotonic is None:
        return StreamFreshnessEvidence(False,float('inf'),'NO_PRIVATE_STREAM_MESSAGE')
    age=now_monotonic-last_message_monotonic
    if age < 0:
        return StreamFreshnessEvidence(False,age,'MONOTONIC_CLOCK_REGRESSION')
    if age > max_age_seconds:
        return StreamFreshnessEvidence(False,age,'PRIVATE_STREAM_STALE')
    return StreamFreshnessEvidence(True,age,'HEALTHY')
