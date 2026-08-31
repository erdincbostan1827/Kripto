from __future__ import annotations

import json
from pathlib import Path

import scripts.external_acceptance_runner as runner


def test_plan_covers_all_external_p0_domains():
    keys = {key for key, _, _ in runner.build_plan("all")}
    assert {"backend_lock", "frontend_lock", "frontend_build", "docker_compose_up", "postgres_migration", "redis_ping",
            "transferred_supply_chain_verification", "pitr_drill", "ha_drill", "binance_testnet"} <= keys


def test_simulation_never_promotes_to_external_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(runner.shutil, "which", lambda _: "/bin/true")
    class P:
        returncode = 0
        stdout = "ok\n"
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: P())
    ev = runner._run("sim", ["fake", "arg"], real_system=False)
    assert ev.status == "BLOCKED"
    assert ev.blocker == "SIMULATED_NOT_EXTERNAL_ACCEPTANCE"


def test_credentials_are_redacted(monkeypatch):
    monkeypatch.setenv("BINANCE_TESTNET_API_KEY", "super-secret-key")
    monkeypatch.setenv("BINANCE_TESTNET_API_SECRET", "super-secret-secret")
    ok, detail = runner._credential_guard()
    assert ok is True
    assert detail == "PRESENT_REDACTED"
    assert "super-secret" not in detail


def test_missing_tool_is_blocked_and_hashed(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(runner.shutil, "which", lambda _: None)
    ev = runner._run("missing", ["no-such-tool"], real_system=True)
    assert ev.status == "BLOCKED"
    assert ev.blocker == "TOOL_UNAVAILABLE:no-such-tool"
    assert len(ev.sha256) == 64


def test_manifest_never_contains_credential_values(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports")
    monkeypatch.setenv("BINANCE_TESTNET_API_KEY", "KEY-DO-NOT-LEAK")
    monkeypatch.setenv("BINANCE_TESTNET_API_SECRET", "SECRET-DO-NOT-LEAK")
    monkeypatch.setattr(runner, "build_plan", lambda profile: [])
    payload = runner.execute("all", confirm_real=False, timeout=1)
    text = json.dumps(payload)
    assert "KEY-DO-NOT-LEAK" not in text
    assert "SECRET-DO-NOT-LEAK" not in text
    assert payload["credentials"]["binance_testnet"] == "PRESENT_REDACTED"


def test_group_status_requires_every_member_to_pass():
    def ev(key, status):
        return runner.Evidence(key, status, True, tuple(), 0, None, "x", "0" * 64, "now")
    evidence = [ev("backend_lock", "PASS"), ev("frontend_lock", "PASS"), ev("frontend_build", "BLOCKED")]
    assert runner._group_status(evidence)["dependency_locks_and_frontend_build"] == "BLOCKED"

