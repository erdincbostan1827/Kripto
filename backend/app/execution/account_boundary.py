from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class AccountIdentity:
    exchange: str
    account_id: str
    account_fingerprint: str
    market_type: str

class AccountBoundaryGuard:
    def __init__(self, expected: AccountIdentity): self.expected=expected
    def require(self, actual: AccountIdentity):
        if actual != self.expected:
            raise PermissionError('exchange account boundary mismatch')
        return True

@dataclass(frozen=True)
class ExternalActivityEvidence:
    balance_drift: tuple[str,...]
    position_drift: tuple[str,...]
    unknown_orders: tuple[str,...]
    missing_orders: tuple[str,...]
    @property
    def detected(self): return any((self.balance_drift,self.position_drift,self.unknown_orders,self.missing_orders))

def detect_external_activity(local, remote) -> ExternalActivityEvidence:
    bd=tuple(sorted(a for a in set(local.balances)|set(remote.balances) if Decimal(str(local.balances.get(a,0)))!=Decimal(str(remote.balances.get(a,0)))))
    pd=tuple(sorted(s for s in set(local.positions)|set(remote.positions) if Decimal(str(local.positions.get(s,0)))!=Decimal(str(remote.positions.get(s,0)))))
    uo=tuple(sorted(remote.open_order_ids-local.open_order_ids)); mo=tuple(sorted(local.open_order_ids-remote.open_order_ids))
    return ExternalActivityEvidence(bd,pd,uo,mo)

@dataclass(frozen=True)
class ExchangeAccountBoundary:
    exchange_account_id: str
    exchange: str
    account_fingerprint: str
    market_type: str
    margin_mode: str | None = None
    position_mode: str | None = None
    capabilities_hash: str | None = None
    permission_hash: str | None = None
    api_key_fingerprint: str | None = None
    status: str = 'ACTIVE'

    def require_compatible(self, other: 'ExchangeAccountBoundary') -> None:
        if self != other:
            raise PermissionError('exchange account/subaccount boundary changed')

from datetime import datetime, timezone

@dataclass(frozen=True)
class AccountLifecycleRecord:
    account_id: str
    created_at: datetime
    last_reconciled_at: datetime | None
    status: str
    deterministic_client_order_prefix: str
    api_key_fingerprint: str | None = None

    def __post_init__(self):
        if not self.account_id or not self.deterministic_client_order_prefix:
            raise ValueError('account id and client-order namespace required')
        if self.created_at.tzinfo is None:
            raise ValueError('created_at must be timezone-aware')
        if self.last_reconciled_at is not None and self.last_reconciled_at.tzinfo is None:
            raise ValueError('last_reconciled_at must be timezone-aware')
        if self.status not in {'ACTIVE','DEGRADED','RECONCILIATION_REQUIRED','DISABLED'}:
            raise ValueError('invalid account lifecycle status')

    def client_order_id(self, intent_id: str) -> str:
        clean=''.join(ch for ch in str(intent_id) if ch.isalnum() or ch in '-_')
        if not clean:
            raise ValueError('intent id required')
        return f'{self.deterministic_client_order_prefix}-{clean}'[:36]

    def mark_reconciled(self, at: datetime | None = None) -> 'AccountLifecycleRecord':
        at=at or datetime.now(timezone.utc)
        if at.tzinfo is None or at < self.created_at:
            raise ValueError('invalid reconciliation timestamp')
        return AccountLifecycleRecord(self.account_id,self.created_at,at,'ACTIVE',self.deterministic_client_order_prefix,self.api_key_fingerprint)
