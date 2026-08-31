from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OnChainSnapshot:
    asset: str
    event_time: datetime
    available_at: datetime
    methodology_version: str
    exchange_inflow: float
    exchange_outflow: float
    active_addresses: float
    realized_cap_metric: float
    mvrv: float
    sopr: float
    miner_related_flows: float
    stablecoin_exchange_flows: float
    revised: bool = False

    def __post_init__(self) -> None:
        if self.event_time.tzinfo is None or self.available_at.tzinfo is None:
            raise ValueError("on-chain timestamps must be timezone-aware")
        if self.available_at < self.event_time:
            raise ValueError("available_at cannot precede event_time")
        if not self.methodology_version.strip():
            raise ValueError("provider methodology version required")

    @property
    def net_exchange_flow(self) -> float:
        return self.exchange_inflow - self.exchange_outflow


@dataclass(frozen=True)
class OnChainContext:
    capability: bool
    features: dict[str, float]
    provider_methodology_version: str | None
    revision_or_latency_possible: bool
    intraday_entry_trigger_allowed: bool
    production_score_weight: float


def build_onchain_context(
    snapshot: OnChainSnapshot | None,
    *,
    as_of: datetime,
    requested_weight: float,
    oos_contribution_proven: bool,
) -> OnChainContext:
    if not 0 <= requested_weight <= 1:
        raise ValueError("requested_weight must be in [0,1]")
    if snapshot is None or snapshot.available_at > as_of:
        return OnChainContext(False, {}, None, True, False, 0.0)
    weight = requested_weight if oos_contribution_proven else 0.0
    return OnChainContext(
        True,
        {
            "exchange_inflow": snapshot.exchange_inflow,
            "exchange_outflow": snapshot.exchange_outflow,
            "net_exchange_flow": snapshot.net_exchange_flow,
            "active_addresses": snapshot.active_addresses,
            "realized_cap_metric": snapshot.realized_cap_metric,
            "mvrv": snapshot.mvrv,
            "sopr": snapshot.sopr,
            "miner_related_flows": snapshot.miner_related_flows,
            "stablecoin_exchange_flows": snapshot.stablecoin_exchange_flows,
        },
        snapshot.methodology_version,
        True,
        False,
        weight,
    )
