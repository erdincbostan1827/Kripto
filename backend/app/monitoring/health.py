from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import socket
import ssl
import time
from urllib.parse import urlparse

import httpx
from sqlalchemy import text


@dataclass(frozen=True)
class ProbeResult:
    status: str
    latency_ms: float | None = None
    detail: str | None = None

    @property
    def healthy(self) -> bool:
        return self.status in {"UP", "MOCK_UP"}


def database_probe(engine):
    def probe() -> ProbeResult:
        started = time.perf_counter()
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return ProbeResult("UP", (time.perf_counter() - started) * 1000)
        except Exception:
            return ProbeResult("DOWN", (time.perf_counter() - started) * 1000, "database probe failed")
    return probe


def redis_ping_probe(redis_url: str, timeout_seconds: float = 1.0):
    parsed = urlparse(redis_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or (6380 if parsed.scheme == "rediss" else 6379)

    def probe() -> ProbeResult:
        started = time.perf_counter()
        sock = None
        try:
            sock = socket.create_connection((host, port), timeout=timeout_seconds)
            if parsed.scheme == "rediss":
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            sock.settimeout(timeout_seconds)
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            reply = sock.recv(64)
            ok = reply.startswith(b"+PONG")
            return ProbeResult("UP" if ok else "DOWN", (time.perf_counter() - started) * 1000, None if ok else "unexpected redis response")
        except Exception:
            return ProbeResult("DOWN", (time.perf_counter() - started) * 1000, "redis probe failed")
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    ...
    return probe


def exchange_time_probe(base_url: str, max_clock_drift_seconds: float = 2.0, timeout_seconds: float = 2.0):
    endpoint = base_url.rstrip("/") + "/api/v3/time"

    def probe() -> ProbeResult:
        started = time.perf_counter()
        try:
            response = httpx.get(endpoint, timeout=timeout_seconds)
            response.raise_for_status()
            server_ms = int(response.json()["serverTime"])
            local_ms = int(time.time() * 1000)
            drift = abs(local_ms - server_ms) / 1000
            ok = drift <= max_clock_drift_seconds
            return ProbeResult("UP" if ok else "DOWN", (time.perf_counter() - started) * 1000, f"clock_drift_seconds={drift:.3f}")
        except Exception:
            return ProbeResult("DOWN", (time.perf_counter() - started) * 1000, "exchange time probe failed")
    return probe


class HealthService:
    CORE_COMPONENTS = ("database", "redis", "exchange", "clock")
    OPERATIONAL_COMPONENTS = CORE_COMPONENTS + ("websocket", "data_freshness", "trading_engine", "telegram", "strategy_engine", "risk_configuration", "disk_space", "memory", "stale_blocked_symbols", "portfolio_concentration")

    def __init__(self, probes: dict[str, object] | None = None, fail_closed: bool = False, required_components: tuple[str, ...] | None = None):
        self.probes = probes or {}
        self.fail_closed = fail_closed
        self.required_components = required_components or (tuple(self.probes.keys()) if self.probes else self.CORE_COMPONENTS)

    @classmethod
    def mock_development(cls) -> "HealthService":
        mock = lambda: ProbeResult("MOCK_UP", 0.0, "development mock probe")
        return cls({"database": mock, "redis": mock, "exchange": mock, "clock": mock}, fail_closed=False)

    @classmethod
    def production(cls, engine=None, redis_url: str | None = None, exchange_base_url: str | None = None, max_clock_drift_seconds: float = 2.0) -> "HealthService":
        probes: dict[str, object] = {}
        if engine is not None:
            probes["database"] = database_probe(engine)
        if redis_url:
            probes["redis"] = redis_ping_probe(redis_url)
        if exchange_base_url:
            probes["exchange"] = exchange_time_probe(exchange_base_url, max_clock_drift_seconds)
            probes["clock"] = probes["exchange"]
        return cls(probes, fail_closed=True, required_components=cls.OPERATIONAL_COMPONENTS)

    def snapshot(self) -> dict:
        status: dict[str, object] = {}
        components = self.required_components
        ready = True
        for component in components:
            probe = self.probes.get(component)
            if probe is None:
                result = ProbeResult("UNCONFIGURED" if self.fail_closed else "MOCK_UP", None, "probe not configured")
            else:
                try:
                    value = probe()
                    if isinstance(value, ProbeResult):
                        result = value
                    else:
                        result = ProbeResult("UP" if bool(value) else "DOWN")
                except Exception:
                    result = ProbeResult("DOWN", None, "probe raised exception")
            status[component] = result.status
            status[f"{component}_latency_ms"] = result.latency_ms
            if result.detail:
                status[f"{component}_detail"] = result.detail
            ready = ready and result.healthy
        status["ready_for_new_risk"] = bool(ready)
        status["checked_at"] = datetime.now(timezone.utc).isoformat()
        return status
