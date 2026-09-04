from __future__ import annotations

from app.release.acceptance_challenge import _trust_command_argv


def test_phase257_windows_challenge_verifier_uses_pwsh() -> None:
    command = "python scripts/verify_release_challenge.py"

    argv = _trust_command_argv(command, platform_name="nt")

    assert argv == ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command]


def test_phase257_posix_challenge_verifier_preserves_bash_contract() -> None:
    command = "python scripts/verify_release_challenge.py"

    argv = _trust_command_argv(command, platform_name="posix")

    assert argv == ["bash", "-lc", command]
