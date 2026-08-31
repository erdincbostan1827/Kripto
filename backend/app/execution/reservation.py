from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import threading
import time

@dataclass
class Reservation:
    intent_id: str
    amount: Decimal
    expires_at: float
    asset: str = 'USDT'
    account_id: str = 'default'
    available_at_reservation: Decimal | None = None

class CapitalReservations:
    """Thread-safe in-process capital reservation ledger.

    LIVE multi-process deployments should use DatabaseCapitalReservations; this
    implementation protects local/PAPER and single-process TESTNET execution
    against concurrent scanner/order submissions overcommitting free capital.
    """
    def __init__(self):
        self.items: dict[str, Reservation] = {}
        self._lock = threading.RLock()

    def reserve(self, intent_id, amount, available, ttl=60, now=None, asset='USDT', account_id='default'):
        now = time.time() if now is None else now
        amount = Decimal(amount)
        available = Decimal(available)
        if amount <= 0:
            raise ValueError('reservation amount must be positive')
        if available < 0:
            raise ValueError('available capital cannot be negative')
        with self._lock:
            self._prune_locked(now)
            if intent_id in self.items:
                return self.items[intent_id]
            used = sum((x.amount for x in self.items.values() if x.asset == asset), Decimal('0'))
            if used + amount > available:
                raise ValueError('insufficient unreserved capital')
            r = Reservation(intent_id, amount, now + ttl, asset, account_id, available)
            self.items[intent_id] = r
            return r

    def release(self, intent_id):
        with self._lock:
            return self.items.pop(intent_id, None)

    def prune(self, now=None):
        now = time.time() if now is None else now
        with self._lock:
            self._prune_locked(now)

    def total_reserved(self, asset='USDT') -> Decimal:
        with self._lock:
            return sum((x.amount for x in self.items.values() if x.asset == asset), Decimal('0'))

    def validate_live_balance(self, intent_id: str, balances: dict[str, Decimal]) -> None:
        """Revalidate shared collateral immediately before a LIVE mutation."""
        with self._lock:
            reservation = self.items.get(intent_id)
            if reservation is None:
                raise PermissionError('missing capital reservation')
            current = Decimal(str(balances.get(reservation.asset, Decimal('0'))))
            reserved = sum((x.amount for x in self.items.values() if x.asset == reservation.asset), Decimal('0'))
            if current < reserved:
                raise PermissionError('shared balance changed; reserved capital no longer covered')

    def _prune_locked(self, now):
        expired = [key for key, value in self.items.items() if value.expires_at <= now]
        for key in expired:
            self.items.pop(key, None)
