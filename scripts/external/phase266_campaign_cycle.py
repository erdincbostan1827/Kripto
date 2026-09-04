#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.release.campaign_collector import (
    PUBLIC_BINANCE_ORIGIN,
    ReadOnlyBinancePublicCollector,
    acceptance_blockers,
    collection_event_counts,
    collection_path,
    derive_collection_metrics,
    environment_id_hash,
    initialize_collection,
    load_collection,
)
from app.release.campaign_runtime_adapter import ProtectedCampaignRuntimeAdapter

CLASSIFICATION = "PHASE266_PROTECTED_REAL_CAMPAIGN_SAMPLING_STATUS_NOT_ACCEPTANCE_EVIDENCE"
TELEMETRY_KEY_ENV = "PHASE265_TELEMETRY_HMAC_KEY"
MIN_KLINES = 12


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _exact_hex(value: str, length: int, *, field: str) -> str:
    normalized = str(value).strip().lower()
    if len(normalized) != length or any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError(f"{field} must be exact {length}-character lowercase hex")
    return normalized


def _git_sha() -> str:
    git_dir = ROOT / ".git"
    if not git_dir.is_dir():
        raise RuntimeError("Phase266 requires a regular Git checkout")
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref: "):
        return _exact_hex(head, 40, field="git HEAD")
    ref = head[5:].strip()
    if not ref.startswith("refs/") or ".." in ref.split("/") or "\\" in ref:
        raise ValueError("git HEAD contains an unsafe ref")
    loose = git_dir / Path(*ref.split("/"))
    if loose.is_file():
        return _exact_hex(loose.read_text(encoding="utf-8").strip(), 40, field="git HEAD")
    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "^")):
                continue
            parts = stripped.split(" ", 1)
            if len(parts) == 2 and parts[1].strip() == ref:
                return _exact_hex(parts[0].strip(), 40, field="git HEAD")
    raise RuntimeError("git HEAD ref could not be resolved")


def _telemetry_key() -> str:
    value = os.getenv(TELEMETRY_KEY_ENV, "")
    if len(value.encode("utf-8")) < 32:
        raise ValueError(f"{TELEMETRY_KEY_ENV} must contain at least 32 UTF-8 bytes")
    return value


class ReadOnlyBinanceRegimeClassifier:
    """Classify a coarse market regime from public Binance spot klines only."""

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 30:
            raise ValueError("timeout_seconds must be in (0, 30]")
        self._timeout_seconds = float(timeout_seconds)

    def classify(self, symbol: str) -> str:
        normalized = str(symbol).strip().upper()
        if not normalized or not normalized.isalnum() or len(normalized) > 20:
            raise ValueError("invalid Binance public-market symbol")
        with httpx.Client(
            base_url=PUBLIC_BINANCE_ORIGIN,
            timeout=self._timeout_seconds,
            follow_redirects=False,
        ) as client:
            response = client.get(
                "/api/v3/klines",
                params={"symbol": normalized, "interval": "1h", "limit": 24},
            )
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, list) or len(payload) < MIN_KLINES:
            raise ValueError("Binance kline response is too short for regime classification")
        closes: list[Decimal] = []
        for row in payload:
            if not isinstance(row, list) or len(row) < 5:
                raise ValueError("Binance kline row is malformed")
            try:
                close = Decimal(str(row[4]))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("Binance kline close is invalid") from exc
            if close <= 0:
                raise ValueError("Binance kline close must be positive")
            closes.append(close)
        first, last = closes[0], closes[-1]
        change_pct = (last - first) / first * Decimal("100")
        if change_pct >= Decimal("0.75"):
            return "TREND_UP"
        if change_pct <= Decimal("-0.75"):
            return "TREND_DOWN"
        return "RANGE"


def run_cycle(
    *,
    candidate: str,
    state_dir: Path,
    environment_id: str,
    topology_hash: str,
    symbol: str,
    samples: int,
    interval_seconds: float,
    timeout_seconds: float,
) -> dict[str, Any]:
    candidate = _exact_hex(candidate, 40, field="candidate SHA")
    topology = _exact_hex(topology_hash, 64, field="topology hash")
    environment_id = str(environment_id).strip()
    if not environment_id:
        raise ValueError("acceptance environment id must be non-empty")
    if _git_sha() != candidate:
        raise PermissionError("Phase266 candidate must equal exact current git HEAD")
    if samples < 1 or samples > 20:
        raise ValueError("samples must be in [1, 20]")
    if interval_seconds < 0 or interval_seconds > 300:
        raise ValueError("interval_seconds must be in [0, 300]")
    if timeout_seconds <= 0 or timeout_seconds > 30:
        raise ValueError("timeout_seconds must be in (0, 30]")

    telemetry_key = _telemetry_key()
    state_dir = state_dir.expanduser().resolve()
    path = collection_path(state_dir, repository_root=ROOT, candidate_sha=candidate)
    env_hash = environment_id_hash(environment_id)
    if not path.exists():
        initialize_collection(
            path,
            repository_root=ROOT,
            candidate_sha=candidate,
            environment_hash=env_hash,
            topology_hash=topology,
        )
    load_collection(
        path,
        candidate_sha=candidate,
        environment_hash=env_hash,
        topology_hash=topology,
        telemetry_key=telemetry_key,
    )

    collector = ReadOnlyBinancePublicCollector(timeout_seconds=timeout_seconds)
    classifier = ReadOnlyBinanceRegimeClassifier(timeout_seconds=timeout_seconds)
    adapter = ProtectedCampaignRuntimeAdapter(collection=path, telemetry_key=telemetry_key)

    last_snapshot: dict[str, Any] | None = None
    regimes_observed: list[str] = []
    for index in range(samples):
        observed_at = _utc_now()
        snapshot = collector.snapshot(symbol)
        regime = classifier.classify(symbol)
        regimes_observed.append(regime)
        adapter.record_paper_quote(
            snapshot,
            market_regime=regime,
            observed_at=observed_at,
            long_intent=None,
            latency_ms=50,
        )
        shadow_decision = {
            "TREND_UP": "LONG",
            "TREND_DOWN": "EXIT",
            "RANGE": "HOLD",
        }[regime]
        adapter.record_live_shadow_observation(
            snapshot,
            strategy_decision=shadow_decision,
            observed_at=observed_at,
        )
        last_snapshot = snapshot
        if interval_seconds and index + 1 < samples:
            time.sleep(interval_seconds)

    rows_before_kill = load_collection(path, telemetry_key=telemetry_key)
    shadow_before_kill = derive_collection_metrics(rows_before_kill)["live-shadow"]
    if shadow_before_kill.get("kill_switch_tested") is not True:
        if last_snapshot is None:
            raise RuntimeError("Phase266 has no real snapshot for kill-switch validation")
        adapter.test_live_shadow_kill_switch(last_snapshot, observed_at=_utc_now())

    rows = load_collection(
        path,
        candidate_sha=candidate,
        environment_hash=env_hash,
        topology_hash=topology,
        telemetry_key=telemetry_key,
    )
    metrics = derive_collection_metrics(rows)
    blockers = acceptance_blockers(metrics)
    return {
        "schema_version": "1.0",
        "classification": CLASSIFICATION,
        "candidate_sha": candidate,
        "acceptance_environment_id_hash": env_hash,
        "topology_hash": topology,
        "collection_path": str(path),
        "samples_collected_this_cycle": samples,
        "regimes_observed_this_cycle": sorted(set(regimes_observed)),
        "event_counts": collection_event_counts(rows),
        "metrics": metrics,
        "blockers": blockers,
        "acceptance_ready": not blockers,
        "live_enabled": False,
        "production_ready": False,
        "truth_policy": (
            "Phase266 only accumulates fresh HMAC-attested protected-runtime observations "
            "from pinned public Binance market data. It never backdates observations, never "
            "submits exchange orders, and never treats sampling progress as campaign acceptance."
        ),
    }


def _write_output(path_value: str | None, payload: dict[str, Any]) -> None:
    if not path_value:
        return
    destination = Path(path_value)
    if not destination.is_absolute():
        destination = ROOT / destination
    destination = destination.resolve()
    try:
        destination.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Phase266 status output must stay inside repository root") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase266 protected real-campaign sampling cycle")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--topology-hash", required=True)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--output")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        result = run_cycle(
            candidate=args.candidate,
            state_dir=Path(args.state_dir),
            environment_id=args.environment_id,
            topology_hash=args.topology_hash,
            symbol=args.symbol,
            samples=args.samples,
            interval_seconds=args.interval_seconds,
            timeout_seconds=args.timeout_seconds,
        )
        _write_output(args.output, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        failure = {
            "schema_version": "1.0",
            "classification": CLASSIFICATION,
            "error": type(exc).__name__,
            "message": str(exc),
            "acceptance_ready": False,
            "live_enabled": False,
            "production_ready": False,
        }
        try:
            _write_output(args.output, failure)
        except Exception:
            pass
        print(json.dumps(failure, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
