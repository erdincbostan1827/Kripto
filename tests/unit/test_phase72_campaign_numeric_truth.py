from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.campaign_acceptance import CLASSIFICATIONS, verify_campaign_evidence


def _write_source(root: Path) -> dict[str, str]:
    p = root / "reports/external_acceptance/source.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("real evidence source\n", encoding="utf-8")
    return {"path": str(p.relative_to(root)), "sha256": sha256(p.read_bytes()).hexdigest()}


def _payload(root: Path, kind: str, metrics: dict) -> dict:
    challenge_path = root / "reports/external_acceptance/release_challenge.json"
    challenge = create_challenge(root, challenge_path)
    return {
        "schema_version": "1.0",
        "classification": CLASSIFICATIONS[kind],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": "UNAVAILABLE",
        "real_system": True,
        "executed": True,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "source_artifacts": [_write_source(root)],
        "metrics": metrics,
    }


def _verify(tmp_path: Path, kind: str, metrics: dict) -> dict:
    path = tmp_path / f"{kind}.json"
    path.write_text(json.dumps(_payload(tmp_path, kind, metrics), allow_nan=True), encoding="utf-8")
    return verify_campaign_evidence(path, kind=kind, root=tmp_path)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_paper_nonfinite_metrics_fail_closed(tmp_path: Path, bad: float):
    metrics = {
        "effective_sample_size": bad, "calendar_days": 31, "market_regimes": ["trend", "range"],
        "long_examples": 30, "exit_examples": 30, "short_examples": 0, "active_market_type": "SPOT",
        "cost_stress_passed": True, "latency_stress_passed": True, "independent_oos_passed": True,
        "execution_divergence_bps": 10, "real_market_data": True,
    }
    result = _verify(tmp_path, "paper", metrics)
    assert not result["verified"]
    assert "NON_FINITE_OR_INVALID_NUMERIC_METRIC" in result["problems"]


@pytest.mark.parametrize("field", ["effective_sample_size", "net_expectancy_bps", "bootstrap_ci_lower_bps", "probabilistic_sharpe_ratio"])
def test_profitability_nonfinite_metrics_fail_closed(tmp_path: Path, field: str):
    metrics = {
        "real_point_in_time_data": True, "independent_oos": True, "leakage_checks_passed": True,
        "cost_stress_passed": True, "survivorship_controls_passed": True, "effective_sample_size": 180,
        "net_expectancy_bps": 5.0, "bootstrap_ci_lower_bps": 1.0, "probabilistic_sharpe_ratio": 0.97,
    }
    metrics[field] = float("nan")
    result = _verify(tmp_path, "profitability", metrics)
    assert not result["verified"]
    assert "NON_FINITE_OR_INVALID_NUMERIC_METRIC" in result["problems"]


def test_count_metrics_reject_bool_and_fractional_values(tmp_path: Path):
    private = {
        "credentialed_testnet": True, "auth_lifecycle_passed": True, "reconnect_passed": True,
        "rest_reconciliation_passed": True, "duplicate_event_idempotency_passed": True,
        "out_of_order_protection_passed": True, "secrets_redacted": True, "observed_events": True,
    }
    assert not _verify(tmp_path, "private-stream", private)["verified"]

    shadow = {
        "real_market_data": True, "calendar_days": 7.5, "observations": 120,
        "real_orders_submitted": 0, "exchange_submit_calls": 0,
        "kill_switch_tested": True, "reconciliation_passed": True,
    }
    result = _verify(tmp_path, "live-shadow", shadow)
    assert not result["verified"]
    assert "NON_FINITE_OR_INVALID_NUMERIC_METRIC" in result["problems"]
