from __future__ import annotations
from decimal import Decimal
from sqlalchemy import select
from app.database.models import AccountBalance,Position,Order
from app.execution.reconciliation import AccountSnapshot

ACTIVE={'CREATED','SUBMITTED','ACKNOWLEDGED','PARTIALLY_FILLED','CANCEL_PENDING','UNKNOWN'}
class DatabaseAccountSnapshotProvider:
    def __init__(self,session_factory): self.sf=session_factory
    def snapshot(self,account_id):
        with self.sf() as s:
            balances={x.asset:Decimal(str(x.free))+Decimal(str(x.locked)) for x in s.scalars(select(AccountBalance).where(AccountBalance.exchange_account_id==account_id)).all()}
            positions={x.symbol:Decimal(str(x.quantity)) for x in s.scalars(select(Position).where(Position.exchange_account_id==account_id)).all() if Decimal(str(x.quantity))!=0}
            orders={x.exchange_order_id for x in s.scalars(select(Order).where(Order.exchange_account_id==account_id,Order.status.in_(ACTIVE))).all() if x.exchange_order_id}
        return AccountSnapshot(balances,positions,orders)
