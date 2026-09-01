from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

import backend.app.release.acceptance_challenge as challenge_mod
import backend.app.release.evidence_ledger_checkpoint as checkpoint_mod
from backend.app.release.acceptance_challenge import create_challenge, verify_challenge
from backend.app.release.acceptance_harness import run_command_attempt


def _git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p211@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase211"], cwd=root, check=True)
    (root / "seed").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)


def test_challenge_git_status_timeout_is_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path)
    original = challenge_mod.run_captured

    def fake(command, **kwargs):
        if list(command[:2]) == ["git", "status"]:
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 10))
        return original(command, **kwargs)

    monkeypatch.setattr(challenge_mod, "run_captured", fake)
    path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    doc = create_challenge(tmp_path, path)
    assert doc["source_worktree_clean_at_creation"] is False

    result = verify_challenge(path, root=tmp_path, require_trust=False)
    assert result["verified"] is False
    assert "CHALLENGE_SOURCE_DIRTY_AT_CREATION" in result["problems"]
    assert "CHALLENGE_SOURCE_STATUS_UNAVAILABLE" in result["problems"]


def test_challenge_external_trust_timeout_stays_unverified(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path)
    path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    create_challenge(tmp_path, path)
    original = challenge_mod.run_captured

    def fake(command, **kwargs):
        if command[:2] == ["bash", "-lc"]:
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 60), output="partial")
        return original(command, **kwargs)

    monkeypatch.setattr(challenge_mod, "run_captured", fake)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "sleep 999")
    result = verify_challenge(path, root=tmp_path, require_trust=True)
    assert result["verified"] is False
    assert "CHALLENGE_TRUST_VERIFICATION_ERROR" in result["problems"]
    assert result["trust_status"] == "EXTERNAL_COMMAND_ERROR:TimeoutExpired"


def test_acceptance_harness_timeout_kills_descendant_process(tmp_path: Path) -> None:
    marker = tmp_path / "child.pid"
    command = [
        "bash",
        "-lc",
        f"sleep 60 & child=$!; echo $child > {marker}; sleep 60",
    ]
    attempt = run_command_attempt(
        key="p211-timeout",
        command=command,
        root=tmp_path,
        evidence_dir=tmp_path / "evidence",
        real_system=True,
        timeout_seconds=1,
    )
    assert attempt.status == "BLOCKED"
    assert attempt.blocker == "TIMEOUT"
    assert marker.is_file()
    child_pid = int(marker.read_text().strip())
    time.sleep(0.2)
    with pytest.raises(ProcessLookupError):
        os.kill(child_pid, 0)


def test_ledger_checkpoint_trust_command_uses_bounded_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], float]] = []

    def fake(command, **kwargs):
        calls.append((list(command), float(kwargs["timeout"])))
        return subprocess.CompletedProcess(list(command), 0, "ok", None)

    monkeypatch.setattr(checkpoint_mod, "run_captured", fake)
    # This assertion is intentionally structural: the verifier's external trust
    # command must stay routed through the shared bounded process primitive.
    source = Path(checkpoint_mod.__file__).read_text(encoding="utf-8")
    assert 'run_captured(\n                ["bash", "-lc", trust_command]' in source
    assert "subprocess.run(" not in source
