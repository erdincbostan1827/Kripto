from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class AppendOnlyAuditSink(Protocol):
    @property
    def append_only(self) -> bool: ...
    @property
    def worm_capable(self) -> bool: ...
    def append(self, payload: bytes) -> str: ...


@dataclass(frozen=True)
class AuditStoragePolicy:
    require_append_only: bool = True
    require_worm_capable_for_production: bool = True

    def validate_sink(self, sink: AppendOnlyAuditSink, *, production: bool) -> None:
        if self.require_append_only and not bool(sink.append_only):
            raise ValueError("audit sink must be append-only")
        if production and self.require_worm_capable_for_production and not bool(sink.worm_capable):
            raise ValueError("production audit sink must be WORM-capable")
