from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


ALLOWED_DATA_TYPES = {
    "MACRO",
    "ETF_FLOW",
    "FUNDING",
    "OPEN_INTEREST",
    "LIQUIDATION",
    "ONCHAIN",
    "NEWS_SENTIMENT",
    "EXCHANGE_STATUS_FILTER",
}


@dataclass(frozen=True)
class AvailabilityRecord:
    record_id: str
    data_type: str
    key: str
    value: Any
    event_time: datetime
    published_at: datetime
    available_at: datetime
    persisted_at: datetime
    source: str
    vintage_id: str | None = None

    def __post_init__(self) -> None:
        if self.data_type not in ALLOWED_DATA_TYPES:
            raise ValueError("unsupported point-in-time data_type")
        if any(ts.tzinfo is None for ts in (self.event_time, self.published_at, self.available_at, self.persisted_at)):
            raise ValueError("all point-in-time timestamps must be timezone-aware")
        if not self.event_time <= self.published_at <= self.available_at <= self.persisted_at:
            raise ValueError("event/published/available/persisted timestamps must be monotonic")
        if any(not str(value).strip() for value in (self.record_id, self.key, self.source)):
            raise ValueError("record identity/source fields are required")
        if self.data_type == "MACRO" and not (self.vintage_id or "").strip():
            raise ValueError("macro records require vintage_id/realtime release identity")


class PointInTimeStore:
    def __init__(self) -> None:
        self._records: list[AvailabilityRecord] = []

    def append(self, record: AvailabilityRecord) -> AvailabilityRecord:
        if any(existing.record_id == record.record_id for existing in self._records):
            raise ValueError("record id duplicate")
        self._records.append(record)
        return record

    def available_as_of(self, as_of: datetime, *, data_type: str | None = None, key: str | None = None) -> tuple[AvailabilityRecord, ...]:
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        rows = [
            row
            for row in self._records
            if row.available_at <= as_of
            and (data_type is None or row.data_type == data_type)
            and (key is None or row.key == key)
        ]
        return tuple(sorted(rows, key=lambda row: (row.event_time, row.available_at, row.record_id)))

    def latest_available(self, as_of: datetime, *, data_type: str, key: str) -> AvailabilityRecord | None:
        rows = self.available_as_of(as_of, data_type=data_type, key=key)
        return rows[-1] if rows else None
