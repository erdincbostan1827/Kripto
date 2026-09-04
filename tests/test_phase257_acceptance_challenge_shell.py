from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.release import acceptance_challenge as challenge  # noqa: E402


def test_trust_shell_argv_windows_prefers_pwsh(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(name: str) -> str | None:
        return {"pwsh": r"C:\Program Files\PowerShell\7\pwsh.exe", "powershell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"}.get(name)

    monkeypatch.setattr(challenge.shutil, "which", fake_which)

    argv = challenge._trust_shell_argv("Write-Output ok", platform_name="Windows")

    assert argv == [
        r"C:\Program Files\PowerShell\7\pwsh.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "Write-Output ok",
    ]


def test_trust_shell_argv_windows_falls_back_to_windows_powershell(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(name: str) -> str | None:
        return r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" if name == "powershell" else None

    monkeypatch.setattr(challenge.shutil, "which", fake_which)

    argv = challenge._trust_shell_argv("Write-Output ok", platform_name="windows")

    assert argv[0].lower().endswith("powershell.exe")
    assert argv[-2:] == ["-Command", "Write-Output ok"]


def test_trust_shell_argv_windows_without_powershell_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(challenge.shutil, "which", lambda _name: None)

    with pytest.raises(RuntimeError, match="POWERSHELL_NOT_FOUND"):
        challenge._trust_shell_argv("Write-Output ok", platform_name="Windows")


def test_trust_shell_argv_posix_requires_bash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(challenge.shutil, "which", lambda name: "/usr/bin/bash" if name == "bash" else None)

    assert challenge._trust_shell_argv("printf ok", platform_name="Linux") == [
        "/usr/bin/bash",
        "-lc",
        "printf ok",
    ]


def _valid_challenge_payload() -> dict[str, object]:
    return {
        "schema_version": challenge.CURRENT_CHALLENGE_SCHEMA,
        "classification": "EXTERNAL_ACCEPTANCE_RELEASE_CHALLENGE",
        "challenge_id": "0123456789abcdef0123456789abcdef",
        "git_commit_sha": "a" * 40,
        "git_tree_sha": "b" * 40,
        "git_identity_available_at_creation": True,
        "source_worktree_clean_at_creation": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "release_campaign_bound": True,
        "acceptance_contract_sha256": "contract-sha",
    }


def _stub_valid_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(challenge, "_git_sha", lambda _root: "a" * 40)
    monkeypatch.setattr(challenge, "_git_tree_sha", lambda _root: "b" * 40)
    monkeypatch.setattr(challenge, "_tracked_source_dirty_paths", lambda _root, extra_ignored=None: [])
    monkeypatch.setattr(challenge, "acceptance_contract_sha256", lambda: "contract-sha")
    monkeypatch.setattr(challenge, "_trust_shell_argv", lambda command: ["pwsh", "-NoProfile", "-Command", command])


def test_external_trust_nonzero_remains_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "challenge.json"
    path.write_text(json.dumps(_valid_challenge_payload()), encoding="utf-8")
    _stub_valid_repo(monkeypatch)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "Write-Output rejected")
    monkeypatch.setattr(challenge, "run_captured", lambda *args, **kwargs: SimpleNamespace(returncode=9, stdout="", stderr="rejected"))

    result = challenge.verify_challenge(path, root=tmp_path, require_trust=True)

    assert result["verified"] is False
    assert result["trust_verified"] is False
    assert result["trust_status"] == "EXTERNAL_COMMAND_REJECTED"
    assert "CHALLENGE_TRUST_VERIFICATION_FAILED" in result["problems"]


def test_external_trust_shell_error_remains_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "challenge.json"
    path.write_text(json.dumps(_valid_challenge_payload()), encoding="utf-8")
    _stub_valid_repo(monkeypatch)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "Write-Output rejected")
    monkeypatch.setattr(challenge, "_trust_shell_argv", lambda _command: (_ for _ in ()).throw(RuntimeError("POWERSHELL_NOT_FOUND")))

    result = challenge.verify_challenge(path, root=tmp_path, require_trust=True)

    assert result["verified"] is False
    assert result["trust_verified"] is False
    assert result["trust_status"] == "EXTERNAL_COMMAND_ERROR:RuntimeError"
    assert "CHALLENGE_TRUST_VERIFICATION_ERROR" in result["problems"]
