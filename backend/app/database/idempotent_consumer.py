from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Callable, Protocol


class ReceiptStore(Protocol):
    def claim(self, consumer_id: str, event_id: str) -> bool: ...
    def release(self, consumer_id: str, event_id: str) -> None: ...


class InMemoryReceiptStore:
    """Reference receipt store; production adapters can bind the same contract to PostgreSQL."""

    def __init__(self) -> None:
        self._seen: set[tuple[str, str]] = set()
        self._lock = RLock()

    def claim(self, consumer_id: str, event_id: str) -> bool:
        key = (consumer_id, event_id)
        with self._lock:
            if key in self._seen:
                return False
            self._seen.add(key)
            return True

    def release(self, consumer_id: str, event_id: str) -> None:
        with self._lock:
            self._seen.discard((consumer_id, event_id))


@dataclass(frozen=True)
class ConsumeResult:
    applied: bool
    duplicate: bool


class IdempotentConsumer:
    """Exactly-once side-effect facade over at-least-once event delivery.

    A receipt is claimed before handling. If handling fails, the claim is released so a retry can run.
    Successful duplicate deliveries are ignored deterministically.
    """

    def __init__(self, consumer_id: str, receipt_store: ReceiptStore, handler: Callable[[dict], None]) -> None:
        if not consumer_id.strip():
            raise ValueError("consumer_id is required")
        self._consumer_id = consumer_id
        self._store = receipt_store
        self._handler = handler

    def consume(self, *, event_id: str, payload: dict) -> ConsumeResult:
        if not event_id.strip():
            raise ValueError("event_id is required")
        if not self._store.claim(self._consumer_id, event_id):
            return ConsumeResult(applied=False, duplicate=True)
        try:
            self._handler(payload)
        except Exception:
            self._store.release(self._consumer_id, event_id)
            raise
        return ConsumeResult(applied=True, duplicate=False)
