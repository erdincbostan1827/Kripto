from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class MarketDataEnvelope:
    """Canonical, auditable wrapper around external market-data observations.

    Exchange timestamps and local receipt timestamps are retained separately so
    latency, staleness and replay/order checks can be evaluated without hiding
    network delay inside the payload.
    """

    source: str
    symbol: str
    timeframe: str
    exchange_time: datetime
    received_at: datetime
    payload: Any
    sequence: int | None = None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source is required")
        if not self.symbol.strip():
            raise ValueError("symbol is required")
        if not self.timeframe.strip():
            raise ValueError("timeframe is required")
        for name, value in (("exchange_time", self.exchange_time), ("received_at", self.received_at)):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.received_at < self.exchange_time:
            raise ValueError("received_at cannot precede exchange_time")
        if self.sequence is not None and self.sequence < 0:
            raise ValueError("sequence must be non-negative")

    @property
    def latency_ms(self) -> float:
        return (self.received_at - self.exchange_time).total_seconds() * 1000.0

    @property
    def timestamp(self) -> datetime:
        """Canonical event timestamp alias retained for reporting contracts."""
        return self.exchange_time

    @classmethod
    def from_exchange_ms(
        cls,
        *,
        source: str,
        symbol: str,
        timeframe: str,
        exchange_time_ms: int,
        payload: Any,
        received_at: datetime | None = None,
        sequence: int | None = None,
    ) -> "MarketDataEnvelope":
        return cls(
            source=source,
            symbol=symbol.upper(),
            timeframe=timeframe,
            exchange_time=datetime.fromtimestamp(exchange_time_ms / 1000, timezone.utc),
            received_at=received_at or datetime.now(timezone.utc),
            payload=payload,
            sequence=sequence,
        )


class SequenceGuard:
    """Detect duplicate and out-of-order observations per logical stream."""

    def __init__(self) -> None:
        self._last: dict[str, int] = {}

    def observe(self, stream_key: str, sequence: int) -> None:
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        previous = self._last.get(stream_key)
        if previous is not None:
            if sequence == previous:
                raise ValueError("duplicate market-data sequence")
            if sequence < previous:
                raise ValueError("out-of-order market-data sequence")
        self._last[stream_key] = sequence

    def last(self, stream_key: str) -> int | None:
        return self._last.get(stream_key)
