from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from decimal import Decimal
from sqlalchemy import select,func
from app.database.models import LeaderLease,CapitalReservationRow

@dataclass(frozen=True)
class PersistentLease:
    account_id:str; instance_id:str; fencing_token:int; expires_at:datetime

class DatabaseLeaderRegistry:
    def __init__(self,session_factory): self.sf=session_factory
    def acquire(self,account_id,instance_id,ttl=10,now=None):
        now=now or datetime.now(timezone.utc); expires=now+timedelta(seconds=ttl)
        with self.sf() as s:
            q=select(LeaderLease).where(LeaderLease.account_id==account_id)
            if s.bind and s.bind.dialect.name=='postgresql': q=q.with_for_update()
            row=s.scalar(q)
            if row and _aware(row.expires_at)>now and row.instance_id!=instance_id: raise PermissionError('leader already active')
            token=(row.fencing_token if row and row.instance_id==instance_id and _aware(row.expires_at)>now else (row.fencing_token+1 if row else 1))
            if row is None: row=LeaderLease(account_id=account_id,instance_id=instance_id,fencing_token=token,expires_at=expires,updated_at=now); s.add(row)
            else: row.instance_id=instance_id; row.fencing_token=token; row.expires_at=expires; row.updated_at=now
            s.commit(); return PersistentLease(account_id,instance_id,token,expires)
    def validate(self,account_id,instance_id,token,now=None):
        now=now or datetime.now(timezone.utc)
        with self.sf() as s: row=s.get(LeaderLease,account_id)
        return bool(row and row.instance_id==instance_id and row.fencing_token==token and _aware(row.expires_at)>now)
    def heartbeat(self,account_id,instance_id,token,ttl=10,now=None):
        now=now or datetime.now(timezone.utc); expires=now+timedelta(seconds=ttl)
        with self.sf() as s:
            q=select(LeaderLease).where(LeaderLease.account_id==account_id)
            if s.bind and s.bind.dialect.name=='postgresql': q=q.with_for_update()
            row=s.scalar(q)
            if not row or row.instance_id!=instance_id or row.fencing_token!=token or _aware(row.expires_at)<=now:
                raise PermissionError('cannot heartbeat stale or expired leader lease')
            row.expires_at=expires; row.updated_at=now; s.commit()
            return PersistentLease(account_id,instance_id,token,expires)

class DatabaseCapitalReservations:
    def __init__(self,session_factory): self.sf=session_factory
    def reserve(self,intent_id,amount,available,asset='USDT',account_id='default',ttl=60,now=None):
        now=now or datetime.now(timezone.utc); amount=Decimal(amount); expires=now+timedelta(seconds=ttl)
        with self.sf() as s:
            existing=s.get(CapitalReservationRow,intent_id)
            if existing and existing.released_at is None and _aware(existing.expires_at)>now: return existing
            q=select(func.coalesce(func.sum(CapitalReservationRow.amount),0)).where(CapitalReservationRow.exchange_account_id==account_id,CapitalReservationRow.asset==asset,CapitalReservationRow.released_at.is_(None),CapitalReservationRow.expires_at>now)
            used=Decimal(str(s.scalar(q) or 0))
            if used+amount>Decimal(available): raise ValueError('insufficient unreserved capital')
            if existing is None: existing=CapitalReservationRow(intent_id=intent_id,exchange_account_id=account_id,amount=amount,asset=asset,expires_at=expires); s.add(existing)
            else: existing.amount=amount; existing.asset=asset; existing.expires_at=expires; existing.released_at=None
            s.commit(); return existing
    @property
    def items(self):
        now=datetime.now(timezone.utc)
        with self.sf() as s: rows=s.scalars(select(CapitalReservationRow).where(CapitalReservationRow.released_at.is_(None),CapitalReservationRow.expires_at>now)).all()
        return {x.intent_id:x for x in rows}
    def release(self,intent_id):
        with self.sf() as s:
            row=s.get(CapitalReservationRow,intent_id)
            if row: row.released_at=datetime.now(timezone.utc); s.commit()

def _aware(dt): return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class FencingTokenGuard:
    """Process-local monotonic fencing check for side-effect boundaries.

    DatabaseLeaderRegistry remains authoritative; this guard prevents an older
    token already observed by a worker from being accepted later in that worker.
    """
    def __init__(self):
        self._highest: dict[str, int] = {}

    def accept(self, account_id: str, token: int) -> bool:
        token = int(token)
        highest = self._highest.get(account_id)
        if highest is not None and token < highest:
            return False
        self._highest[account_id] = token if highest is None else max(highest, token)
        return True

    def require(self, account_id: str, token: int) -> None:
        if not self.accept(account_id, token):
            raise PermissionError('stale fencing token')

class PersistentIntentLedger:
    """Durable intent idempotency boundary for exchange side effects.

    The intent is committed as SUBMITTED before the external exchange call. On
    restart, an existing intent is never blindly re-submitted: terminal/known
    durable state is returned, while SUBMITTED/UNKNOWN is reconciled by stable
    client_order_id and remains UNKNOWN if exchange truth cannot be proven.
    """
    def __init__(self, session_factory):
        self.sf = session_factory

    @staticmethod
    def _assert_same_intent(record, intent) -> None:
        expected = (intent.account_id, intent.symbol, intent.side, intent.order_type, Decimal(intent.quantity))
        actual = (record.account_id, record.symbol, record.side, record.order_type, Decimal(record.quantity))
        if actual != expected:
            raise ValueError('intent_id collision with different economic order')

    @staticmethod
    def _to_record(row):
        from app.core.enums import OrderState
        from app.exchange.models import OrderRecord
        state = OrderState(row.status)
        return OrderRecord(
            row.intent_id, row.exchange_account_id, row.symbol, row.side,
            row.order_type, Decimal(str(row.quantity)), state,
            Decimal(str(row.price)) if row.price is not None else None,
            Decimal(str(row.stop_price)) if row.stop_price is not None else None,
            exchange_order_id=row.exchange_order_id,
            client_order_id=row.client_order_id,
        )

    def get(self, intent_id: str):
        from app.database.models import Order
        with self.sf() as s:
            row = s.scalar(select(Order).where(Order.intent_id == intent_id))
            return None if row is None else self._to_record(row)

    def reserve_before_side_effect(self, intent) -> tuple[object, bool]:
        """Return (record, created). Unique intent_id is the durable mutex."""
        import uuid
        from sqlalchemy.exc import IntegrityError
        from app.database.models import Order
        from app.core.enums import OrderState

        with self.sf() as s:
            existing = s.scalar(select(Order).where(Order.intent_id == intent.intent_id))
            if existing is not None:
                record = self._to_record(existing)
                self._assert_same_intent(record, intent)
                return record, False
            row = Order(
                id=uuid.uuid4().hex,
                intent_id=intent.intent_id,
                exchange_account_id=intent.account_id,
                symbol=intent.symbol,
                side=intent.side,
                order_type=intent.order_type,
                quantity=intent.quantity,
                price=intent.price,
                stop_price=intent.stop_price,
                status=OrderState.SUBMITTED.value,
                exchange_order_id=None,
                client_order_id=intent.client_order_id or f'ctp-{intent.intent_id}',
            )
            s.add(row)
            try:
                s.commit()
            except IntegrityError:
                s.rollback()
                existing = s.scalar(select(Order).where(Order.intent_id == intent.intent_id))
                if existing is None:
                    raise
                record = self._to_record(existing)
                self._assert_same_intent(record, intent)
                return record, False
            s.refresh(row)
            return self._to_record(row), True

    def mark(self, intent_id: str, record) -> None:
        from app.database.models import Order
        with self.sf() as s:
            row = s.scalar(select(Order).where(Order.intent_id == intent_id))
            if row is None:
                raise LookupError(f'unknown durable intent {intent_id}')
            row.status = record.state.value
            row.exchange_order_id = record.exchange_order_id
            if record.client_order_id:
                row.client_order_id = record.client_order_id
            s.commit()

    def reconcile_existing(self, exchange, intent_id: str, expected_intent=None):
        """Resolve a durable pre-existing intent without blind re-submit."""
        from app.core.enums import OrderState
        current = self.get(intent_id)
        if current is None:
            return None
        if expected_intent is not None:
            self._assert_same_intent(current, expected_intent)
        if current.state not in {OrderState.SUBMITTED, OrderState.UNKNOWN}:
            return current
        remote = exchange.get_order(
            current.symbol,
            order_id=current.exchange_order_id,
            client_order_id=current.client_order_id,
        )
        if remote is not None:
            self.mark(intent_id, remote)
            return remote
        current.state = OrderState.UNKNOWN
        self.mark(intent_id, current)
        return current


class DatabaseExecutionFence:
    """Final side-effect fencing check for multi-instance execution.

    The authoritative persistent lease is revalidated immediately before an
    exchange side effect, and a process-local monotonic guard rejects any token
    older than one already observed by this worker.
    """
    def __init__(self, leader_registry):
        self.registry = leader_registry
        self.guard = FencingTokenGuard()

    def require_current(self, account_id: str, instance_id: str, token: int, now=None) -> None:
        self.guard.require(account_id, token)
        if not self.registry.validate(account_id, instance_id, token, now=now):
            raise PermissionError('stale or expired LIVE fencing token at side-effect boundary')
