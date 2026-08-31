from __future__ import annotations

import json
from pathlib import Path

from scripts.external_acceptance_preflight import evaluate

ROOT = Path(__file__).resolve().parents[2]


def test_phase28_preflight_is_fail_closed_and_never_calls_readiness_acceptance():
    payload = evaluate()
    assert payload["classification"] == "EXTERNAL_ACCEPTANCE_PREFLIGHT_ONLY_NOT_ACCEPTANCE_EVIDENCE"
    assert "never means" in payload["truth_policy"]
    assert {"dependency_locks","container_runtime","credentialed_testnet","transferred_supply_chain_contract","signing_tooling"} <= set(payload["groups"])
    assert all(c["status"] in {"READY","BLOCKED"} for c in payload["checks"])


def test_phase28_preflight_redacts_testnet_credentials(monkeypatch):
    monkeypatch.setenv("BINANCE_TESTNET_API_KEY", "super-secret-key")
    monkeypatch.setenv("BINANCE_TESTNET_API_SECRET", "super-secret-secret")
    payload = evaluate()
    encoded = json.dumps(payload)
    assert "super-secret-key" not in encoded and "super-secret-secret" not in encoded
    env_checks = [c for c in payload["checks"] if c["key"].startswith("env:BINANCE_TESTNET_")]
    assert env_checks and all(c["detail"] == "PRESENT_REDACTED" for c in env_checks)


def test_phase28_missing_source_locks_remain_current_fail_closed_truth_without_historical_reports():
    payload = evaluate()
    lock_checks = {c["key"]: c for c in payload["checks"] if c["key"] in {"file:uv.lock", "file:frontend/package-lock.json"}}
    assert set(lock_checks) == {"file:uv.lock", "file:frontend/package-lock.json"}
    assert all(c["status"] == "BLOCKED" for c in lock_checks.values())
    assert payload["groups"]["dependency_locks"] is False
