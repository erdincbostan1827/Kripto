from __future__ import annotations
from decimal import Decimal
import time
import hashlib

class OrderBookIntegrityError(RuntimeError):
    """Raised when local order-book sequence or price integrity is violated."""

class LocalOrderBook:
    def __init__(self, monotonic=time.monotonic):
        self.last_update_id: int | None = None
        self.bids: dict[Decimal, Decimal] = {}
        self.asks: dict[Decimal, Decimal] = {}
        self.valid = False
        self.gap_count = 0
        self.resync_count = 0
        self.stale_event_count = 0
        self.last_update_at: float | None = None
        self.checksum_verified: bool | None = None
        self._monotonic = monotonic

    def load_snapshot(self,last_update_id:int,bids,asks):
        self.last_update_id=last_update_id
        self.bids={Decimal(str(p)):Decimal(str(q)) for p,q in bids if Decimal(str(q))>0}
        self.asks={Decimal(str(p)):Decimal(str(q)) for p,q in asks if Decimal(str(q))>0}
        try:
            self._validate()
        except OrderBookIntegrityError:
            self.valid=False
            raise
        self.valid=True
        self.resync_count += 1
        self.last_update_at=self._monotonic()

    def apply_delta(self,first_id:int,last_id:int,bids,asks):
        if self.last_update_id is None or not self.valid:
            raise OrderBookIntegrityError('snapshot required')
        if last_id <= self.last_update_id:
            self.stale_event_count += 1
            return False
        expected=self.last_update_id+1
        if not (first_id<=expected<=last_id):
            self.gap_count += 1
            self.valid=False
            raise OrderBookIntegrityError('sequence gap')
        for side,updates in ((self.bids,bids),(self.asks,asks)):
            for p,q in updates:
                p,q=Decimal(str(p)),Decimal(str(q))
                if q==0:
                    side.pop(p,None)
                else:
                    side[p]=q
        self.last_update_id=last_id
        try:
            self._validate()
        except OrderBookIntegrityError:
            self.valid=False
            raise
        self.last_update_at=self._monotonic()
        return True

    def _validate(self):
        if self.bids and self.asks and max(self.bids)>=min(self.asks):
            raise OrderBookIntegrityError('crossed book')


    def canonical_checksum_payload(self, depth: int | None = None) -> bytes:
        """Deterministic local book representation for venue-provided checksum contracts."""
        bids = sorted(self.bids.items(), reverse=True)
        asks = sorted(self.asks.items())
        if depth is not None:
            if depth <= 0:
                raise ValueError("depth must be positive")
            bids, asks = bids[:depth], asks[:depth]
        parts=[]
        for side, levels in (("B", bids), ("A", asks)):
            for price, qty in levels:
                parts.append(f"{side}:{price.normalize()}:{qty.normalize()}")
        return "|".join(parts).encode()

    def verify_exchange_checksum(self, expected_hex: str | None, *, depth: int | None = None) -> bool:
        """Verify checksum when the venue supplies one; absence is explicitly conditional."""
        if expected_hex is None:
            self.checksum_verified = None
            return True
        if not self.valid:
            raise OrderBookIntegrityError("cannot checksum INVALID order book")
        actual = hashlib.sha256(self.canonical_checksum_payload(depth)).hexdigest()
        ok = actual == expected_hex.casefold()
        self.checksum_verified = ok
        if not ok:
            self.valid = False
            raise OrderBookIntegrityError("exchange checksum mismatch; resync required")
        return True

    def require_valid(self):
        if not self.valid:
            raise OrderBookIntegrityError('order book is INVALID; resync required')
        return self

    def age_seconds(self, now: float | None = None):
        if self.last_update_at is None:
            return None
        current=self._monotonic() if now is None else now
        if current < self.last_update_at:
            raise OrderBookIntegrityError('monotonic clock moved backwards')
        return current-self.last_update_at

    @property
    def best_bid(self): return max(self.bids) if self.bids else None
    @property
    def best_ask(self): return min(self.asks) if self.asks else None
    @property
    def spread(self):
        if self.best_bid is None or self.best_ask is None: return None
        return self.best_ask-self.best_bid
    @property
    def locked(self): return bool(self.bids and self.asks and self.best_bid==self.best_ask)
    @property
    def depth_imbalance(self):
        bid=sum(self.bids.values(),Decimal('0')); ask=sum(self.asks.values(),Decimal('0'))
        total=bid+ask
        return Decimal('0') if total==0 else (bid-ask)/total
