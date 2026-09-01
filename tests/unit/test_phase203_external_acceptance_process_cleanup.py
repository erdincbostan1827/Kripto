from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import scripts.external_acceptance_runner as runner
import scripts.production_acceptance_orchestrator as orchestrator


def test_external_acceptance_run_uses_bounded_runner(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner.shutil, "which", lambda _tool: "/bin/tool")
    seen = {}

    def fake_run(command, *, cwd, timeout, env=None):
        seen.update(command=list(command), cwd=cwd, timeout=timeout, env=env)
        return subprocess.CompletedProcess(command, 0, "ok\n", None)

    monkeypatch.setattr(runner, "run_captured", fake_run)
    evidence = runner._run("probe", ["tool", "arg"], real_system=True, run_dir=tmp_path / "reports", timeout=17)
    assert evidence.status == "PASS"
    assert seen["command"] == ["tool", "arg"]
    assert seen["timeout"] == 17


def test_external_acceptance_timeout_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner.shutil, "which", lambda _tool: "/bin/tool")

    def fake_run(command, *, cwd, timeout, env=None):
        raise subprocess.TimeoutExpired(command, timeout, output="partial")

    monkeypatch.setattr(runner, "run_captured", fake_run)
    evidence = runner._run("probe", ["tool"], real_system=True, run_dir=tmp_path / "reports", timeout=3)
    assert evidence.status == "BLOCKED"
    assert evidence.blocker == "COMMAND_OR_NETWORK_TIMEOUT"
    assert "TIMEOUT" in (tmp_path / "reports" / "probe.log").read_text()


def test_orchestrator_cli_uses_bounded_runner(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(orchestrator, "ROOT", tmp_path)
    seen = {}

    def fake_run(command, *, cwd, timeout, env=None):
        seen.update(command=list(command), cwd=cwd, timeout=timeout)
        return subprocess.CompletedProcess(command, 4, "blocked\n", None)

    monkeypatch.setattr(orchestrator, "run_captured", fake_run)
    result = orchestrator._run_cli(["tool", "arg"], timeout=11)
    assert result["exit_code"] == 4
    assert seen["timeout"] == 11


def test_orchestrator_cli_timeout_fails_closed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(orchestrator, "ROOT", tmp_path)

    def fake_run(command, *, cwd, timeout, env=None):
        raise subprocess.TimeoutExpired(command, timeout, output="partial")

    monkeypatch.setattr(orchestrator, "run_captured", fake_run)
    result = orchestrator._run_cli(["tool"], timeout=2)
    assert result["exit_code"] is None
    assert result["blocker"] == "COMMAND_OR_NETWORK_TIMEOUT"
    assert result["output"] == "partial"
