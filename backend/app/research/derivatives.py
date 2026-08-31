from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class DerivativesSnapshot:
    symbol: str
    provider_id: str
    information_id: str
    provider_timestamp: datetime
    available_at: datetime
    funding_rate: float | None = None
    predicted_funding_rate: float | None = None
    open_interest: float | None = None
    oi_change: float | None = None
    futures_basis: float | None = None
    annualized_basis: float | None = None
    mark_index_basis: float | None = None
    liquidation_intensity: float | None = None
    liquidation_imbalance: float | None = None
    taker_buy_sell_imbalance: float | None = None
    long_short_positioning: float | None = None
    positioning_methodology_reliable: bool = False

    def __post_init__(self) -> None:
        if self.provider_timestamp.tzinfo is None or self.available_at.tzinfo is None:
            raise ValueError("derivatives timestamps must be timezone-aware")
        if self.available_at < self.provider_timestamp:
            raise ValueError("available_at cannot precede provider_timestamp")
        if any(not value.strip() for value in (self.symbol, self.provider_id, self.information_id)):
            raise ValueError("derivatives identity fields required")


@dataclass(frozen=True)
class DerivativesContext:
    capability: bool
    stale: bool
    features: dict[str, float | None]
    contributing_information_ids: tuple[str, ...]
    standalone_trade_trigger_allowed: bool = False


def build_derivatives_context(
    snapshots: list[DerivativesSnapshot],
    *,
    as_of: datetime,
    max_age: timedelta = timedelta(minutes=5),
) -> DerivativesContext:
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    visible = [row for row in snapshots if row.available_at <= as_of]
    dedup: dict[str, DerivativesSnapshot] = {}
    for row in sorted(visible, key=lambda item: (item.available_at, item.provider_timestamp)):
        dedup[row.information_id] = row
    rows = list(dedup.values())
    fresh = [row for row in rows if as_of - row.provider_timestamp <= max_age]
    if not fresh:
        return DerivativesContext(False, bool(rows), {}, tuple(sorted(dedup)), False)
    latest = max(fresh, key=lambda row: row.available_at)
    features: dict[str, float | None] = {
        "funding_rate": latest.funding_rate,
        "predicted_funding_rate": latest.predicted_funding_rate,
        "open_interest": latest.open_interest,
        "oi_change": latest.oi_change,
        "futures_basis": latest.futures_basis,
        "annualized_basis": latest.annualized_basis,
        "mark_index_basis": latest.mark_index_basis,
        "liquidation_intensity": latest.liquidation_intensity,
        "liquidation_imbalance": latest.liquidation_imbalance,
        "taker_buy_sell_imbalance": latest.taker_buy_sell_imbalance,
        "long_short_positioning": latest.long_short_positioning if latest.positioning_methodology_reliable else None,
    }
    return DerivativesContext(True, False, features, tuple(sorted(dedup)), False)
