from __future__ import annotations

import errno
from dataclasses import dataclass


class PersistentStorageUnavailable(RuntimeError):
    """Raised when a durability-critical write cannot be completed."""


@dataclass(frozen=True)
class StorageFailure:
    kind: str
    detail: str


def classify_storage_failure(exc: BaseException) -> StorageFailure:
    text = str(exc).lower()
    original = getattr(exc, "orig", None)
    original_errno = getattr(original, "errno", None)
    if original_errno == errno.ENOSPC or "disk is full" in text or "no space left on device" in text:
        return StorageFailure("DISK_FULL", str(exc))
    if "readonly" in text or "read-only" in text:
        return StorageFailure("READ_ONLY", str(exc))
    if "database is locked" in text or "could not connect" in text or "connection" in text:
        return StorageFailure("DATABASE_UNAVAILABLE", str(exc))
    return StorageFailure("PERSISTENCE_WRITE_FAILED", str(exc))
