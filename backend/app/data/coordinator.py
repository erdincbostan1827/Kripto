from __future__ import annotations

from dataclasses import dataclass

from app.core.backpressure import PriorityEventBuffer, QueuedEvent
from app.data.rate_limit import RateLimitBudget


@dataclass(frozen=True, order=True)
class MarketSubscription:
    symbol: str
    stream: str
    timeframe: str | None = None

    @property
    def key(self) -> str:
        suffix = f"_{self.timeframe}" if self.timeframe else ""
        return f"{self.symbol.lower()}@{self.stream}{suffix}"


class MarketDataCoordinator:
    def __init__(self, max_streams_per_connection: int = 200, queue_size: int = 2048):
        if max_streams_per_connection <= 0 or queue_size <= 0:
            raise ValueError("coordinator capacities must be positive")
        self.max_streams_per_connection = max_streams_per_connection
        self.queue = PriorityEventBuffer(maxsize=queue_size)
        self.registry: dict[str, tuple[MarketSubscription, ...]] = {}
        self.freshness: dict[str, float] = {}
        self.rate_limits = RateLimitBudget()
        self.connection_generation: dict[str, int] = {}

    def build_registry(self, subscriptions: list[MarketSubscription]) -> dict[str, tuple[MarketSubscription, ...]]:
        unique = sorted({subscription.key: subscription for subscription in subscriptions}.values(), key=lambda item: item.key)
        self.registry = {}
        for offset in range(0, len(unique), self.max_streams_per_connection):
            connection_id = f"market-{offset // self.max_streams_per_connection + 1}"
            self.registry[connection_id] = tuple(unique[offset : offset + self.max_streams_per_connection])
        self.connection_generation = {key: self.connection_generation.get(key, 0) for key in self.registry}
        return dict(self.registry)

    def resubscribe_plan(self, connection_id: str) -> tuple[str, ...]:
        if connection_id not in self.registry:
            raise KeyError(connection_id)
        return tuple(item.key for item in self.registry[connection_id])


    def reconnect_resubscribe_all(self) -> dict[str, tuple[str, ...]]:
        """Return a complete deterministic resubscription plan for every shard."""
        plans: dict[str, tuple[str, ...]] = {}
        for connection_id in sorted(self.registry):
            self.connection_generation[connection_id] = self.connection_generation.get(connection_id, 0) + 1
            plans[connection_id] = self.resubscribe_plan(connection_id)
        return plans

    def configure_fallback_budget(self, key: str, limit: float, interval_seconds: float, now: float) -> None:
        self.rate_limits.configure(key, limit, interval_seconds, now=now)

    def allow_rest_with_fallback(self, primary_key: str, fallback_key: str, weight: float, now: float) -> str | None:
        return self.rate_limits.allow_with_fallback(primary_key, fallback_key, weight=weight, now=now)

    def mark_symbol_fresh(self, symbol: str, observed_at: float) -> None:
        self.freshness[symbol.upper()] = float(observed_at)

    def stale_symbols(self, now: float, max_age_seconds: float) -> set[str]:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        current = float(now)
        return {
            symbol
            for symbol, observed_at in self.freshness.items()
            if current - observed_at > max_age_seconds
        }

    def enqueue(self, category: str, payload: object) -> bool:
        return self.queue.put(QueuedEvent(category=category, payload=payload))

    def configure_runtime_budget(self, key: str, limit: float, interval_seconds: float, now: float) -> None:
        self.rate_limits.configure(key, limit, interval_seconds, now=now)

    def allow_rest(self, key: str, weight: float, priority: str, now: float) -> bool:
        return self.rate_limits.allow(key, weight=weight, priority=priority, now=now)

    def rate_telemetry(self, key: str) -> dict[str, float]:
        budget = self.rate_limits.budgets[key]
        return {
            "limit": budget.limit,
            "used": budget.used,
            "remaining": self.rate_limits.remaining(key),
            "interval_seconds": budget.interval_seconds,
        }

    @staticmethod
    def reconciliation_delay(base_seconds: float, jitter_fraction: float, jitter_value: float) -> float:
        if base_seconds <= 0 or not 0 <= jitter_fraction <= 1 or not 0 <= jitter_value <= 1:
            raise ValueError("invalid reconciliation schedule parameters")
        return base_seconds * (1 + jitter_fraction * jitter_value)

    @staticmethod
    def rest_reconciliation_due(last_verified_at: float | None, now: float, interval_seconds: float) -> bool:
        """Return whether an authoritative REST cross-check is due.

        WebSocket streams remain the low-latency path; this method schedules a
        periodic REST truth check without allowing a negative clock jump to
        silently postpone reconciliation.
        """
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        current = float(now)
        if last_verified_at is None:
            return True
        previous = float(last_verified_at)
        if current < previous:
            raise ValueError("monotonic clock moved backwards")
        return current - previous >= interval_seconds

    @staticmethod
    def stale_risk_scope(shared_critical_feed_stale: bool, symbol_is_stale: bool) -> str:
        if shared_critical_feed_stale:
            return "GLOBAL_RESTRICT"
        if symbol_is_stale:
            return "BLOCK_SYMBOL"
        return "NORMAL"

    def validate_subscription_coverage(self, symbols: set[str] | list[str] | tuple[str, ...]) -> bool:
        """Verify every configured symbol has at least one registered stream."""
        expected = {str(symbol).upper() for symbol in symbols}
        actual = {
            subscription.symbol.upper()
            for shard in self.registry.values()
            for subscription in shard
        }
        if expected != actual:
            missing = sorted(expected - actual)
            unexpected = sorted(actual - expected)
            raise RuntimeError(f'incomplete market-data subscription coverage missing={missing} unexpected={unexpected}')
        return True

    def subscription_telemetry(self) -> dict[str, int]:
        subscriptions = [subscription for shard in self.registry.values() for subscription in shard]
        return {
            'websocket_subscriptions': len(subscriptions),
            'websocket_shards': len(self.registry),
            'unique_symbols': len({item.symbol.upper() for item in subscriptions}),
        }
