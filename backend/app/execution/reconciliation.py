from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from app.core.enums import RiskState
@dataclass(frozen=True)
class AccountSnapshot:
    balances:dict[str,Decimal]; positions:dict[str,Decimal]; open_order_ids:set[str]
@dataclass(frozen=True)
class ReconciliationResult:
    drift:list[str]; risk_state:RiskState

def reconcile(local:AccountSnapshot,exchange:AccountSnapshot)->ReconciliationResult:
    drift=[]
    for asset in set(local.balances)|set(exchange.balances):
        if local.balances.get(asset,Decimal('0'))!=exchange.balances.get(asset,Decimal('0')): drift.append(f'UNKNOWN_BALANCE_CHANGE:{asset}')
    for sym in set(local.positions)|set(exchange.positions):
        if local.positions.get(sym,Decimal('0'))!=exchange.positions.get(sym,Decimal('0')): drift.append(f'UNKNOWN_POSITION_CHANGE:{sym}')
    for oid in exchange.open_order_ids-local.open_order_ids: drift.append(f'UNKNOWN_ORDER:{oid}')
    for oid in local.open_order_ids-exchange.open_order_ids: drift.append(f'MISSING_EXCHANGE_ORDER:{oid}')
    return ReconciliationResult(drift,RiskState.MANUAL_REVIEW_REQUIRED if drift else RiskState.NORMAL)

@dataclass(frozen=True)
class CancelResolution:
    state: str
    action: str
    order_id: str


def resolve_cancel_timeout(*, exchange, symbol: str, order_id: str, local_state: str) -> CancelResolution:
    """Resolve an ambiguous/cancel-timeout strictly from exchange truth.

    Never assumes that a timed-out cancel succeeded. Missing or still-open
    exchange state remains UNKNOWN and requires reconciliation/manual review.
    """
    remote = exchange.get_order(symbol, order_id=order_id)
    if remote is None:
        return CancelResolution('UNKNOWN', 'MANUAL_REVIEW_REQUIRED', order_id)
    status = getattr(remote.state, 'value', str(remote.state))
    if status in {'FILLED', 'CANCELLED', 'REJECTED', 'FAILED'}:
        return CancelResolution(status, 'APPLY_EXCHANGE_TRUTH', order_id)
    if status in {'ACKNOWLEDGED', 'PARTIALLY_FILLED', 'CANCEL_PENDING', 'SUBMITTED'}:
        return CancelResolution(status, 'RECONCILE_AND_RETRY_CANCEL', order_id)
    return CancelResolution('UNKNOWN', 'MANUAL_REVIEW_REQUIRED', order_id)


@dataclass(frozen=True)
class ProtectiveCoverageResult:
    uncovered_symbols: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.uncovered_symbols


def validate_protective_coverage(position_quantities: dict[str, Decimal], protective_symbols: set[str]) -> ProtectiveCoverageResult:
    """Fail closed when an exposed symbol has no confirmed protective order coverage."""
    exposed = {symbol for symbol, qty in position_quantities.items() if Decimal(str(qty)) != 0}
    return ProtectiveCoverageResult(tuple(sorted(exposed - set(protective_symbols))))

@dataclass(frozen=True)
class OrphanOrderAction:
    order_id: str
    action: str
    reason: str


def plan_orphan_order_recovery(local: AccountSnapshot, exchange: AccountSnapshot, *, allow_cancel_unknown: bool=False) -> tuple[OrphanOrderAction,...]:
    """Create a fail-closed recovery plan; never silently adopts unknown orders."""
    actions=[]
    for oid in sorted(exchange.open_order_ids-local.open_order_ids):
        actions.append(OrphanOrderAction(oid,'CANCEL_AND_RECONCILE' if allow_cancel_unknown else 'MANUAL_REVIEW','EXCHANGE_ORDER_NOT_IN_LOCAL_LEDGER'))
    for oid in sorted(local.open_order_ids-exchange.open_order_ids):
        actions.append(OrphanOrderAction(oid,'QUERY_HISTORY_AND_RECONCILE','LOCAL_ACTIVE_ORDER_MISSING_ON_EXCHANGE'))
    return tuple(actions)

@dataclass(frozen=True)
class CompositeReconciliationEvidence:
    local: AccountSnapshot
    exchange: AccountSnapshot
    balance_checked: bool
    positions_checked: bool
    open_orders_checked: bool
    local_database_checked: bool


@dataclass(frozen=True)
class CompositeReconciliationResult:
    complete: bool
    drift: tuple[str, ...]
    risk_state: RiskState
    missing_checks: tuple[str, ...]


def reconcile_composite(evidence: CompositeReconciliationEvidence) -> CompositeReconciliationResult:
    """Require all four truth domains before reconciliation may be declared complete."""
    checks = {
        "EXCHANGE_BALANCE": evidence.balance_checked,
        "EXCHANGE_POSITIONS": evidence.positions_checked,
        "EXCHANGE_OPEN_ORDERS": evidence.open_orders_checked,
        "LOCAL_DATABASE": evidence.local_database_checked,
    }
    missing = tuple(sorted(name for name, ok in checks.items() if not ok))
    if missing:
        return CompositeReconciliationResult(False, (), RiskState.MANUAL_REVIEW_REQUIRED, missing)
    base = reconcile(evidence.local, evidence.exchange)
    return CompositeReconciliationResult(not base.drift, tuple(base.drift), base.risk_state, ())
