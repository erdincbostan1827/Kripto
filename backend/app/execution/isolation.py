from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import threading


class AccountRiskLocks:
    """Per-account in-process critical-section locks.

    Database fencing remains authoritative for multi-process LIVE deployments;
    this registry prevents same-process submit/reconcile races from observing or
    mutating shared account risk concurrently.
    """

    def __init__(self):
        self._guard = threading.Lock()
        self._locks: dict[str, threading.RLock] = {}

    def _for(self, account_id: str) -> threading.RLock:
        with self._guard:
            return self._locks.setdefault(account_id, threading.RLock())

    @contextmanager
    def hold(self, account_id: str):
        lock = self._for(account_id)
        with lock:
            yield


@dataclass(frozen=True)
class SymbolIsolationRecord:
    account_id: str
    symbol: str
    reason: str


class SymbolRiskIsolation:
    """Quarantine ambiguous activity at symbol scope when safe to do so."""

    def __init__(self):
        self._lock = threading.RLock()
        self._blocked: dict[tuple[str, str], SymbolIsolationRecord] = {}

    def block(self, account_id: str, symbol: str, reason: str) -> SymbolIsolationRecord:
        key = (account_id, symbol.upper())
        record = SymbolIsolationRecord(account_id, symbol.upper(), reason)
        with self._lock:
            self._blocked[key] = record
        return record

    def clear(self, account_id: str, symbol: str) -> None:
        with self._lock:
            self._blocked.pop((account_id, symbol.upper()), None)

    def is_blocked(self, account_id: str, symbol: str) -> bool:
        with self._lock:
            return (account_id, symbol.upper()) in self._blocked

    def reason(self, account_id: str, symbol: str) -> str | None:
        with self._lock:
            record = self._blocked.get((account_id, symbol.upper()))
            return record.reason if record else None
