from __future__ import annotations

from pathlib import Path

import pytest

from scripts.external import phase266_campaign_cycle as cycle

CANDIDATE = "a" * 40
TOPOLOGY_HASH = "b" * 64
TELEMETRY_KEY = "phase266-test-telemetry-hmac-key-material-000000000000000000"


class _FakeCollector:
    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.counter = 0

    def snapshot(self, symbol: str) -> dict[str, object]:
        self.counter += 1
        return {
            "observation_id": f"real-observation-{self.counter}",
            "symbol": symbol.upper(),
            "bid_price": "100.00",
            "ask_price": "100.01",
            "market_data_origin": "REAL",
            "public_origin": cycle.PUBLIC_BINANCE_ORIGIN,
        }


class _FakeClassifier:
    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def classify(self, symbol: str) -> str:
        assert symbol.upper() == "BTCUSDT"
        return "TREND_UP"


def test_cycle_accumulates_attested_real_samples_without_manufacturing_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cycle, "_git_sha", lambda: CANDIDATE)
    monkeypatch.setattr(cycle, "ReadOnlyBinancePublicCollector", _FakeCollector)
    monkeypatch.setattr(cycle, "ReadOnlyBinanceRegimeClassifier", _FakeClassifier)
    monkeypatch.setenv(cycle.TELEMETRY_KEY_ENV, TELEMETRY_KEY)

    result = cycle.run_cycle(
        candidate=CANDIDATE,
        state_dir=(tmp_path / "persistent-state").resolve(),
        environment_id="phase266-test-environment",
        topology_hash=TOPOLOGY_HASH,
        symbol="BTCUSDT",
        samples=3,
        interval_seconds=0,
        timeout_seconds=1,
    )

    assert result["classification"] == cycle.CLASSIFICATION
    assert result["samples_collected_this_cycle"] == 3
    assert result["regimes_observed_this_cycle"] == ["TREND_UP"]
    assert result["event_counts"]["acceptance_eligible"] == 7
    assert result["event_counts"]["unattested_audit"] == 0
    assert result["metrics"]["paper"]["effective_sample_size"] == 3.0
    assert result["metrics"]["paper"]["real_market_data"] is True
    assert result["metrics"]["paper"]["long_examples"] == 0
    assert result["metrics"]["paper"]["exit_examples"] == 0
    assert result["metrics"]["live-shadow"]["observations"] == 3
    assert result["metrics"]["live-shadow"]["real_orders_submitted"] == 0
    assert result["metrics"]["live-shadow"]["exchange_submit_calls"] == 0
    assert result["metrics"]["live-shadow"]["kill_switch_tested"] is True
    assert "PRIVATE_STREAM_INCOMPLETE" in result["blockers"]
    assert any(str(item).startswith("PAPER:") for item in result["blockers"])
    assert "LIVE_SHADOW_INCOMPLETE" in result["blockers"]
    assert "PROFITABILITY_INCOMPLETE" in result["blockers"]
    assert result["acceptance_ready"] is False
    assert result["live_enabled"] is False
    assert result["production_ready"] is False


def test_cycle_rejects_stale_candidate_before_any_market_collection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cycle, "_git_sha", lambda: "c" * 40)
    monkeypatch.setenv(cycle.TELEMETRY_KEY_ENV, TELEMETRY_KEY)

    with pytest.raises(PermissionError, match="exact current git HEAD"):
        cycle.run_cycle(
            candidate=CANDIDATE,
            state_dir=(tmp_path / "persistent-state").resolve(),
            environment_id="phase266-test-environment",
            topology_hash=TOPOLOGY_HASH,
            symbol="BTCUSDT",
            samples=1,
            interval_seconds=0,
            timeout_seconds=1,
        )


def test_cycle_requires_strong_runner_only_telemetry_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cycle, "_git_sha", lambda: CANDIDATE)
    monkeypatch.setenv(cycle.TELEMETRY_KEY_ENV, "too-short")

    with pytest.raises(ValueError, match="at least 32"):
        cycle.run_cycle(
            candidate=CANDIDATE,
            state_dir=(tmp_path / "persistent-state").resolve(),
            environment_id="phase266-test-environment",
            topology_hash=TOPOLOGY_HASH,
            symbol="BTCUSDT",
            samples=1,
            interval_seconds=0,
            timeout_seconds=1,
        )


def test_status_output_cannot_escape_repository_root(tmp_path: Path) -> None:
    outside = (tmp_path / "status.json").resolve()
    with pytest.raises(ValueError, match="inside repository root"):
        cycle._write_output(outside.as_posix(), {"production_ready": False})
