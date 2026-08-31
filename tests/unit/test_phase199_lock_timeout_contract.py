from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import bootstrap_dependency_locks as mod


def test_phase199_timeout_contract_accepts_bounded_values():
    assert mod._validated_timeout_seconds("5") == 5.0
    assert mod._validated_timeout_seconds(mod.MIN_LOCK_RESOLUTION_TIMEOUT_SECONDS) == mod.MIN_LOCK_RESOLUTION_TIMEOUT_SECONDS
    assert mod._validated_timeout_seconds(mod.MAX_LOCK_RESOLUTION_TIMEOUT_SECONDS) == mod.MAX_LOCK_RESOLUTION_TIMEOUT_SECONDS


@pytest.mark.parametrize("raw", ["bad", 0, -1, 3600.1])
def test_phase199_timeout_contract_rejects_invalid_values(raw):
    with pytest.raises(ValueError):
        mod._validated_timeout_seconds(raw)


def test_phase199_cli_invalid_timeout_fails_closed_without_resolver_execution(tmp_path: Path, monkeypatch):
    report = tmp_path / "report.json"
    called = False

    def fake_bootstrap(**kwargs):
        nonlocal called
        called = True
        raise AssertionError("resolver must not run")

    monkeypatch.setattr(mod, "bootstrap", fake_bootstrap)
    rc = mod.main(["--timeout-seconds", "0", "--report", str(report)])
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert rc == 2
    assert called is False
    assert payload["classification"] == "DEPENDENCY_LOCK_BOOTSTRAP_FAIL_CLOSED"
    assert payload["error"] == "ValueError"
    assert "LOCK_RESOLUTION_TIMEOUT_OUT_OF_RANGE" in payload["message"]


def test_phase199_bootstrap_report_binds_effective_timeout(tmp_path: Path, monkeypatch):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\nversion="0.0.0"\n', encoding="utf-8")
    (tmp_path / "frontend" / "package.json").write_text('{"name":"x","version":"0.0.0"}', encoding="utf-8")
    monkeypatch.setattr(mod, "LOCK_RESOLUTION_TIMEOUT_SECONDS", 3.5)

    def fake_run(cmd, cwd, *, offline):
        return {"command": cmd, "exit_code": 1, "ok": False, "blocker": "TEST", "output": ""}

    monkeypatch.setattr(mod, "_run", fake_run)
    payload = mod.bootstrap(root=tmp_path)
    assert payload["committed"] is False
    assert payload["resolver_timeout_seconds"] == 3.5
