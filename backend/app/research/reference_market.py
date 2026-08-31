from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Protocol


class ReferenceMarketDataAdapter(Protocol):
    venue: str

    def quote(self, symbol: str, as_of: datetime) -> "VenueQuote | None": ...


@dataclass(frozen=True)
class VenueQuote:
    venue: str
    symbol: str
    bid: float
    ask: float
    last: float
    event_time: datetime
    available_at: datetime
    source_id: str

    def __post_init__(self) -> None:
        if self.event_time.tzinfo is None or self.available_at.tzinfo is None:
            raise ValueError("quote timestamps must be timezone-aware")
        if self.available_at < self.event_time:
            raise ValueError("available_at cannot precede event_time")
        if self.bid <= 0 or self.ask <= 0 or self.last <= 0 or self.bid > self.ask:
            raise ValueError("invalid quote")
        if not self.venue.strip() or not self.symbol.strip() or not self.source_id.strip():
            raise ValueError("quote identity required")

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

    @property
    def spread_bps(self) -> float:
        return (self.ask - self.bid) / self.mid * 10_000.0


@dataclass(frozen=True)
class ReferenceConsensus:
    capability: bool
    reference_price: float | None
    contributing_venues: tuple[str, ...]
    stale_venues: tuple[str, ...]
    abnormal_spread_venues: tuple[str, ...]
    isolated_bad_tick_venues: tuple[str, ...]
    venue_divergence_bps: float | None
    exchange_specific_dislocation: bool


def build_reference_consensus(
    quotes: list[VenueQuote],
    *,
    as_of: datetime,
    max_age: timedelta = timedelta(seconds=5),
    abnormal_spread_bps: float = 50.0,
    bad_tick_deviation_bps: float = 100.0,
) -> ReferenceConsensus:
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    visible = [row for row in quotes if row.available_at <= as_of]
    stale = sorted({row.venue for row in visible if as_of - row.event_time > max_age})
    fresh = [row for row in visible if row.venue not in stale]
    if not fresh:
        return ReferenceConsensus(False, None, (), tuple(stale), (), (), None, False)
    reference = float(median(row.mid for row in fresh))
    abnormal = sorted({row.venue for row in fresh if row.spread_bps > abnormal_spread_bps})
    bad_tick = sorted(
        {
            row.venue
            for row in fresh
            if abs(row.last - reference) / reference * 10_000.0 > bad_tick_deviation_bps
        }
    )
    reliable = [row for row in fresh if row.venue not in bad_tick]
    if reliable:
        reference = float(median(row.mid for row in reliable))
    divergence = max(
        max(abs(row.mid - reference), abs(row.last - reference)) / reference * 10_000.0
        for row in fresh
    )
    return ReferenceConsensus(
        capability=True,
        reference_price=reference,
        contributing_venues=tuple(sorted(row.venue for row in reliable)),
        stale_venues=tuple(stale),
        abnormal_spread_venues=tuple(abnormal),
        isolated_bad_tick_venues=tuple(bad_tick),
        venue_divergence_bps=float(divergence),
        exchange_specific_dislocation=bool(bad_tick or abnormal or divergence > bad_tick_deviation_bps),
    )
