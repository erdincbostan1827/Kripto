from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class OptionsSnapshot:
    symbol: str
    event_time: datetime
    available_at: datetime
    atm_implied_volatility: float
    term_structure: float
    skew: float
    risk_reversal: float
    put_call_open_interest_or_volume: float
    implied_expected_move: float
    realized_volatility: float

    def __post_init__(self) -> None:
        if self.event_time.tzinfo is None or self.available_at.tzinfo is None:
            raise ValueError("options timestamps must be timezone-aware")
        if self.available_at < self.event_time:
            raise ValueError("available_at cannot precede event_time")
        if self.atm_implied_volatility < 0 or self.realized_volatility < 0 or self.implied_expected_move < 0:
            raise ValueError("volatility inputs cannot be negative")


@dataclass(frozen=True)
class OptionsContext:
    capability: bool
    features: dict[str, float]
    event_risk_score: float
    volatility_expansion_score: float
    tail_risk_score: float
    stop_distance_multiplier: float
    position_size_multiplier: float
    standalone_trade_trigger_allowed: bool = False


def build_options_context(
    snapshot: OptionsSnapshot | None,
    *,
    as_of: datetime,
    max_age: timedelta = timedelta(hours=1),
) -> OptionsContext:
    if snapshot is None or snapshot.available_at > as_of or as_of - snapshot.event_time > max_age:
        return OptionsContext(False, {}, 0.0, 0.0, 0.0, 1.0, 1.0, False)
    iv_rv_spread = snapshot.atm_implied_volatility - snapshot.realized_volatility
    expansion = max(0.0, iv_rv_spread)
    tail = max(0.0, abs(snapshot.skew), abs(snapshot.risk_reversal))
    event_risk = max(0.0, snapshot.implied_expected_move, expansion)
    stop_multiplier = min(2.0, max(1.0, 1.0 + event_risk))
    position_multiplier = max(0.25, min(1.0, 1.0 / stop_multiplier))
    return OptionsContext(
        True,
        {
            "atm_implied_volatility": snapshot.atm_implied_volatility,
            "term_structure": snapshot.term_structure,
            "skew": snapshot.skew,
            "risk_reversal": snapshot.risk_reversal,
            "put_call_open_interest_or_volume": snapshot.put_call_open_interest_or_volume,
            "implied_expected_move": snapshot.implied_expected_move,
            "iv_realized_volatility_spread": iv_rv_spread,
        },
        event_risk,
        expansion,
        tail,
        stop_multiplier,
        position_multiplier,
        False,
    )
