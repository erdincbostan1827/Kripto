from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class AccountingEvidence:
    order_id:str
    fill_id:str|None
    signal_fingerprint:str|None
    fee:Decimal=Decimal('0')
    funding:Decimal=Decimal('0')
    realized_pnl:Decimal=Decimal('0')
    unrealized_pnl:Decimal|None=None
    transfer_amount:Decimal|None=None
    transfer_reconciled:bool=False

@dataclass(frozen=True)
class LedgerLifecyclePolicy:
    native_partitioning:bool=True
    retention_days:int=365
    archival_after_days:int=90
    compression_optional:bool=True
    timescaledb_required:bool=False

@dataclass(frozen=True)
class AccountingValidation:
    ok:bool
    reasons:tuple[str,...]


def validate_accounting_evidence(e:AccountingEvidence, *, require_signal_fingerprint:bool=True)->AccountingValidation:
    reasons=[]
    if not e.order_id: reasons.append('ORDER_REFERENCE_REQUIRED')
    if e.fill_id is None and any(Decimal(str(v))!=0 for v in (e.fee,e.funding,e.realized_pnl)):
        reasons.append('FILL_REFERENCE_REQUIRED_FOR_REALIZED_ACTIVITY')
    if require_signal_fingerprint and not e.signal_fingerprint:
        reasons.append('SIGNAL_FINGERPRINT_REQUIRED')
    if Decimal(str(e.fee))<0: reasons.append('NEGATIVE_FEE_INVALID')
    if e.transfer_amount is not None and not e.transfer_reconciled:
        reasons.append('MANUAL_TRANSFER_RECONCILIATION_REQUIRED')
    return AccountingValidation(not reasons,tuple(reasons))


def validate_ledger_lifecycle(policy:LedgerLifecyclePolicy)->AccountingValidation:
    reasons=[]
    if not policy.native_partitioning: reasons.append('NATIVE_PARTITIONING_REQUIRED')
    if policy.retention_days<=0: reasons.append('RETENTION_POLICY_REQUIRED')
    if policy.archival_after_days<=0 or policy.archival_after_days>=policy.retention_days: reasons.append('ARCHIVAL_WINDOW_INVALID')
    if policy.timescaledb_required: reasons.append('TIMESCALEDB_MUST_REMAIN_OPTIONAL')
    return AccountingValidation(not reasons,tuple(reasons))
