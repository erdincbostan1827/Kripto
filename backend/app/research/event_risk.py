from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol


class EventCalendarAdapter(Protocol):
    def events(self, start: datetime, end: datetime) -> tuple["EconomicEvent", ...]: ...


TRACKED_EVENT_TYPES = {
    "FOMC",
    "FED_SPEECH",
    "NFP_EMPLOYMENT",
    "LIQUIDITY_RATE",
    "DXY_YIELDS_REAL_YIELDS",
    "SPOT_ETF_ETP_FLOW",
    "EXCHANGE_MAINTENANCE",
}


@dataclass(frozen=True)
class EconomicEvent:
    event_id: str
    event_type: str
    scheduled_time: datetime
    actual_release_time: datetime | None
    expected: float | None
    actual: float | None
    previous_vintage: float | None
    surprise: float | None
    source: str
    reliability: float

    def __post_init__(self) -> None:
        if self.event_type not in TRACKED_EVENT_TYPES:
            raise ValueError("unsupported event type")
        if self.scheduled_time.tzinfo is None or (self.actual_release_time is not None and self.actual_release_time.tzinfo is None):
            raise ValueError("event timestamps must be timezone-aware")
        if not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be in [0,1]")
        if not self.event_id.strip() or not self.source.strip():
            raise ValueError("event identity/source required")

    def as_of(self, timestamp: datetime) -> "EconomicEvent":
        if self.actual_release_time is None or self.actual_release_time <= timestamp:
            return self
        return EconomicEvent(
            event_id=self.event_id,
            event_type=self.event_type,
            scheduled_time=self.scheduled_time,
            actual_release_time=None,
            expected=self.expected,
            actual=None,
            previous_vintage=self.previous_vintage,
            surprise=None,
            source=self.source,
            reliability=self.reliability,
        )


@dataclass(frozen=True)
class EventRiskDecision:
    event_id: str
    no_new_entry: bool
    position_size_multiplier: float
    slippage_assumption_multiplier: float
    extra_confirmation_required: bool
    production_policy_enabled: bool
    reason: str


@dataclass(frozen=True)
class EventRiskPolicy:
    before_window: timedelta = timedelta(minutes=30)
    after_window: timedelta = timedelta(minutes=15)
    reduce_size_multiplier: float = 0.5
    slippage_multiplier: float = 1.5
    min_reliability: float = 0.7
    oos_effect_reported: bool = False

    def __post_init__(self) -> None:
        if not 0 < self.reduce_size_multiplier <= 1:
            raise ValueError("reduce_size_multiplier must be in (0,1]")
        if self.slippage_multiplier < 1:
            raise ValueError("slippage_multiplier must be >=1")
        if not 0 <= self.min_reliability <= 1:
            raise ValueError("min_reliability must be in [0,1]")

    def evaluate(self, event: EconomicEvent, *, now: datetime) -> EventRiskDecision:
        visible = event.as_of(now)
        in_window = event.scheduled_time - self.before_window <= now <= event.scheduled_time + self.after_window
        reliable = event.reliability >= self.min_reliability
        enabled = bool(self.oos_effect_reported)
        active = in_window and reliable and enabled
        reason = "EVENT_RISK_ACTIVE" if active else ("OOS_EFFECT_NOT_REPORTED" if in_window and reliable else "EVENT_RISK_INACTIVE")
        return EventRiskDecision(
            event_id=event.event_id,
            no_new_entry=active,
            position_size_multiplier=self.reduce_size_multiplier if active else 1.0,
            slippage_assumption_multiplier=self.slippage_multiplier if active else 1.0,
            extra_confirmation_required=active,
            production_policy_enabled=enabled,
            reason=reason,
        )
