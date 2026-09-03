from __future__ import annotations

import sys
from pathlib import Path

import pytest

from backend.app.release.acceptance_contract import ACCEPTANCE_PLANS
import scripts.external.run_approved_drill as drill


EXPECTED_CANONICAL_COMMANDS = {
    ("restart-drills", "restart_semantic_evidence"): (
        "python", "scripts/external/run_approved_drill.py", "restart-drills"
    ),
    ("pitr", "pitr_drill"): ("python", "scripts/external/run_approved_drill.py", "pitr"),
    ("ha", "ha_drill"): ("python", "scripts/external/run_approved_drill.py", "ha"),
    ("worm", "worm_storage"): ("python", "scripts/external/run_approved_drill.py", "worm"),
    ("provenance", "artifact_sign_verify"): (
        "python", "scripts/external/run_approved_drill.py", "provenance"
    ),
}


def test_canonical_external_drills_are_python_cross_platform() -> None:
    for (profile, key), expected in EXPECTED_CANONICAL_COMMANDS.items():
        rows = {row_key: command for row_key, command, _ in ACCEPTANCE_PLANS[profile]}
        assert rows[key] == expected
        assert rows[key][0] == "python"
        assert "bash" not in rows[key]


def test_windows_shell_prefers_pwsh_without_shell_true() -> None:
    def which(name: str) -> str | None:
        return r"C:\Program Files\PowerShell\7\pwsh.exe" if name == "pwsh" else None

    argv = drill._shell_argv("Write-Output ok", platform_name="nt", which=which)
    assert argv[0].endswith("pwsh.exe")
    assert argv[-2:] == ["-Command", "Write-Output ok"]
    assert "-NoProfile" in argv
    assert "-NonInteractive" in argv


def test_windows_shell_falls_back_to_windows_powershell() -> None:
    def which(name: str) -> str | None:
        return r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" if name == "powershell" else None

    argv = drill._shell_argv("Write-Output ok", platform_name="nt", which=which)
    assert argv[0].endswith("powershell.exe")
    assert argv[-1] == "Write-Output ok"


def test_posix_shell_uses_explicit_bash_argv() -> None:
    argv = drill._shell_argv("printf ok", platform_name="posix", which=lambda name: "/bin/bash" if name == "bash" else None)
    assert argv == ["/bin/bash", "-lc", "printf ok"]


def test_missing_platform_shell_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="APPROVED_COMMAND_SHELL_UNAVAILABLE:POWERSHELL"):
        drill._shell_argv("x", platform_name="nt", which=lambda _name: None)
    with pytest.raises(RuntimeError, match="APPROVED_COMMAND_SHELL_UNAVAILABLE:BASH"):
        drill._shell_argv("x", platform_name="posix", which=lambda _name: None)


def test_command_failure_does_not_run_verifier_or_leak_command(monkeypatch: pytest.MonkeyPatch) -> None:
    secret_command = "approved-tool --token ultra-sensitive-literal"
    monkeypatch.setenv("RESTART_DRILL_COMMAND", secret_command)
    monkeypatch.setenv("RESTART_EVIDENCE_JSON", "reports/external_acceptance/restart.json")
    monkeypatch.setattr(drill, "_shell_argv", lambda command: ["runner", command])
    calls: list[tuple[list[str], str | None]] = []

    def run(argv: list[str], *, secret_command: str | None = None) -> int:
        calls.append((argv, secret_command))
        return 7

    monkeypatch.setattr(drill, "_run_redacted", run)
    with pytest.raises(RuntimeError) as excinfo:
        drill.run_profile("restart-drills")
    message = str(excinfo.value)
    assert message == "APPROVED_COMMAND_FAILED:restart-drills:EXIT_CODE:7"
    assert "ultra-sensitive-literal" not in message
    assert len(calls) == 1


def test_success_runs_evidence_verifier_with_current_python(monkeypatch: pytest.MonkeyPatch) -> None:
    evidence = "reports/external_acceptance/pitr.json"
    monkeypatch.setenv("PITR_DRILL_COMMAND", "approved-pitr-command")
    monkeypatch.setenv("PITR_EVIDENCE_JSON", evidence)
    monkeypatch.setattr(drill, "_shell_argv", lambda command: ["runner", command])
    calls: list[list[str]] = []

    def run(argv: list[str], *, secret_command: str | None = None) -> int:
        calls.append(argv)
        return 0

    monkeypatch.setattr(drill, "_run_redacted", run)
    assert drill.run_profile("pitr") == 0
    assert calls[0] == ["runner", "approved-pitr-command"]
    assert calls[1] == [sys.executable, "scripts/external/verify_drill_evidence.py", "pitr", evidence]


def test_verifier_failure_remains_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HA_DRILL_COMMAND", "approved-ha-command")
    monkeypatch.setenv("HA_EVIDENCE_JSON", "reports/external_acceptance/ha.json")
    monkeypatch.setattr(drill, "_shell_argv", lambda command: ["runner", command])
    results = iter((0, 2))
    monkeypatch.setattr(drill, "_run_redacted", lambda argv, secret_command=None: next(results))
    with pytest.raises(RuntimeError, match="ACCEPTANCE_EVIDENCE_VERIFICATION_FAILED:ha:EXIT_CODE:2"):
        drill.run_profile("ha")


def test_required_environment_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORM_ACCEPTANCE_COMMAND", raising=False)
    monkeypatch.delenv("WORM_EVIDENCE_JSON", raising=False)
    with pytest.raises(RuntimeError, match="REQUIRED_ACCEPTANCE_ENV_MISSING:WORM_ACCEPTANCE_COMMAND"):
        drill.run_profile("worm")


def test_approved_process_output_redacts_known_secret_env(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    secret = "phase240-super-secret-token"
    monkeypatch.setenv("BINANCE_API_KEY", secret)
    rc = drill._run_redacted([sys.executable, "-c", f"print({secret!r})"])
    captured = capsys.readouterr().out
    assert rc == 0
    assert secret not in captured
    assert "[REDACTED]" in captured


def test_launcher_source_never_uses_subprocess_shell_true() -> None:
    source = Path(drill.__file__).read_text(encoding="utf-8")
    assert "shell=True" not in source
