from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import select
from app.database.models import LedgerEntry, Order, Fill

@dataclass(frozen=True)
class ReferentialIntegrityResult:
    valid: bool
    errors: tuple[str, ...]


def validate_execution_references(session, *, exchange_account_id: str) -> ReferentialIntegrityResult:
    """Validate order/fill/ledger references inside a single exchange-account boundary."""
    errors=[]
    orders={o.id:o for o in session.scalars(select(Order).where(Order.exchange_account_id==exchange_account_id)).all()}
    fills=session.scalars(select(Fill).where(Fill.exchange_account_id==exchange_account_id)).all()
    fill_ids={f.id for f in fills}
    trade_ids={f.trade_id for f in fills}
    for f in fills:
        if f.order_id not in orders:
            errors.append(f'FILL_ORDER_MISSING:{f.id}:{f.order_id}')
    ledger=session.scalars(select(LedgerEntry).where(LedgerEntry.exchange_account_id==exchange_account_id)).all()
    for e in ledger:
        rt=str(e.reference_type).upper()
        if rt=='ORDER' and e.reference_id not in orders:
            errors.append(f'LEDGER_ORDER_MISSING:{e.id}:{e.reference_id}')
        elif rt=='FILL' and e.reference_id not in fill_ids and e.reference_id not in trade_ids:
            errors.append(f'LEDGER_FILL_MISSING:{e.id}:{e.reference_id}')
    return ReferentialIntegrityResult(not errors, tuple(sorted(errors)))
