from __future__ import annotations

import asyncio
import inspect
import json
import random
import time
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable

import websockets


@dataclass(frozen=True)
class PublicMarketEvent:
    stream: str
    event_type: str
    symbol: str | None
    event_time_ms: int | None
    payload: dict


@dataclass(frozen=True)
class PublicStreamHealth:
    stale: bool
    sequence_gaps: int
    delayed_events: int
    out_of_order_events: int
    clock_anomaly: bool
    reconnects: int
    bad_messages: int

    @property
    def healthy(self) -> bool:
        return not (
            self.stale
            or self.sequence_gaps
            or self.delayed_events
            or self.out_of_order_events
            or self.clock_anomaly
            or self.bad_messages
        )


class BinancePublicMarketStream:
    BASE_URL = "wss://stream.binance.com:9443/stream"

    def __init__(
        self,
        symbols: Iterable[str],
        timeframes: Iterable[str] = ("1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"),
        stale_after_seconds: float = 10.0,
        max_event_delay_ms: int = 5000,
        connector=None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        wall_time_ms: Callable[[], int] = lambda: int(time.time() * 1000),
        jitter: Callable[[], float] = random.random,
    ):
        normalized = tuple(dict.fromkeys(symbol.lower() for symbol in symbols if symbol.strip()))
        if not normalized:
            raise ValueError("at least one symbol is required")
        self.symbols = normalized
        self.timeframes = tuple(timeframes)
        self.stale_after_seconds = float(stale_after_seconds)
        self.max_event_delay_ms = int(max_event_delay_ms)
        self.connector = connector or websockets.connect
        self.sleep = sleep
        self.monotonic = monotonic
        self.wall_time_ms = wall_time_ms
        self.jitter = jitter
        self.last_message_at: float | None = None
        self.reconnects = 0
        self.bad_messages = 0
        self.sequence_gaps = 0
        self.delayed_events = 0
        self.out_of_order_events = 0
        self.clock_anomaly = False
        self._last_depth_final: dict[str, int] = {}
        self._last_event_time_ms: dict[str, int] = {}

    @property
    def streams(self) -> tuple[str, ...]:
        streams: list[str] = []
        for symbol in self.symbols:
            streams.extend((f"{symbol}@trade", f"{symbol}@bookTicker", f"{symbol}@depth@100ms"))
            streams.extend(f"{symbol}@kline_{tf}" for tf in self.timeframes)
        return tuple(streams)

    @property
    def url(self) -> str:
        return f"{self.BASE_URL}?streams={'/'.join(self.streams)}"

    def is_stale(self, now: float | None = None) -> bool:
        if self.last_message_at is None:
            return True
        current = self.monotonic() if now is None else now
        if current < self.last_message_at:
            self.clock_anomaly = True
            return True
        return current - self.last_message_at > self.stale_after_seconds

    @staticmethod
    def parse(raw: str | bytes) -> PublicMarketEvent:
        doc = json.loads(raw)
        stream = str(doc.get("stream", ""))
        payload = doc.get("data", doc)
        if not isinstance(payload, dict):
            raise ValueError("unexpected public stream payload")
        suffix = stream.split("@", 1)[1] if "@" in stream else "unknown"
        event_type = str(payload.get("e") or suffix.split("@", 1)[0])
        symbol = payload.get("s")
        event_time = payload.get("E")
        return PublicMarketEvent(stream, event_type, str(symbol) if symbol else None, int(event_time) if event_time is not None else None, payload)

    def observe(self, event: PublicMarketEvent) -> None:
        """Track packet integrity without silently repairing or reordering data."""
        key = event.stream or (event.symbol or "UNKNOWN")
        if event.event_time_ms is not None:
            previous_time = self._last_event_time_ms.get(key)
            if previous_time is not None and event.event_time_ms < previous_time:
                self.out_of_order_events += 1
            else:
                self._last_event_time_ms[key] = event.event_time_ms
            if self.wall_time_ms() - event.event_time_ms > self.max_event_delay_ms:
                self.delayed_events += 1

        # Binance diff-depth messages expose U=first update id and u=final update id.
        first = event.payload.get("U")
        final = event.payload.get("u")
        if first is not None and final is not None and "@depth" in event.stream:
            first_i, final_i = int(first), int(final)
            previous_final = self._last_depth_final.get(key)
            if previous_final is not None:
                if final_i <= previous_final:
                    self.out_of_order_events += 1
                elif first_i > previous_final + 1:
                    self.sequence_gaps += 1
            if previous_final is None or final_i > previous_final:
                self._last_depth_final[key] = final_i

    def health(self, now: float | None = None) -> PublicStreamHealth:
        return PublicStreamHealth(
            stale=self.is_stale(now),
            sequence_gaps=self.sequence_gaps,
            delayed_events=self.delayed_events,
            out_of_order_events=self.out_of_order_events,
            clock_anomaly=self.clock_anomaly,
            reconnects=self.reconnects,
            bad_messages=self.bad_messages,
        )

    async def run(self, handler: Callable[[PublicMarketEvent], object], stop_event: asyncio.Event) -> None:
        attempt = 0
        while not stop_event.is_set():
            try:
                async with self.connector(self.url, ping_interval=20, ping_timeout=20, close_timeout=5, max_queue=1024) as websocket:
                    attempt = 0
                    async for raw in websocket:
                        now = self.monotonic()
                        if self.last_message_at is not None and now < self.last_message_at:
                            self.clock_anomaly = True
                        self.last_message_at = now
                        try:
                            event = self.parse(raw)
                            self.observe(event)
                        except (ValueError, TypeError, json.JSONDecodeError):
                            # A poison payload must not tear down every symbol on the combined stream.
                            self.bad_messages += 1
                            continue
                        result = handler(event)
                        if inspect.isawaitable(result):
                            await result
                        if stop_event.is_set():
                            break
            except asyncio.CancelledError:
                raise
            except Exception:
                if stop_event.is_set():
                    return
                self.reconnects += 1
                delay = min(30.0, 0.5 * (2**attempt)) + self.jitter() * 0.25
                attempt = min(attempt + 1, 8)
                await self.sleep(delay)
