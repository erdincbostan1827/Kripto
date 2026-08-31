from __future__ import annotations

import subprocess
from pathlib import Path

from backend.app.release.acceptance_challenge import create_challenge, verify_challenge


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase153@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase153"], cwd=root, check=True)
    (root / "seed.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def test_phase153_challenge_from_source_package_without_git_is_fail_closed(tmp_path: Path, monkeypatch):
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    created = create_challenge(tmp_path, path)
    assert created["schema_version"] == "2.3"
    assert created["git_identity_available_at_creation"] is False
    assert created["git_commit_sha"] == "UNAVAILABLE"
    assert created["git_tree_sha"] == "UNAVAILABLE"

    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    checked = verify_challenge(path, root=tmp_path, require_trust=True)
    assert checked["verified"] is False
    assert "CHALLENGE_GIT_IDENTITY_UNAVAILABLE_AT_CREATION" in checked["problems"]
    assert "CHALLENGE_GIT_IDENTITY_UNAVAILABLE" in checked["problems"]
    assert "CHALLENGE_NOT_GIT_BOUND" in checked["problems"]


def test_phase153_clean_git_challenge_remains_valid_with_external_trust(tmp_path: Path, monkeypatch):
    git_sha = _git(tmp_path)
    path = tmp_path / "reports/external_acceptance/release_challenge.json"
    created = create_challenge(tmp_path, path)
    assert created["schema_version"] == "2.3"
    assert created["git_identity_available_at_creation"] is True
    assert created["git_commit_sha"] == git_sha

    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", 'test -f "$ACCEPTANCE_CHALLENGE_PATH"')
    checked = verify_challenge(path, root=tmp_path, require_trust=True)
    assert checked["verified"] is True
    assert checked["trust_verified"] is True
    assert checked["git_identity_available_at_creation"] is True


def test_phase153_orchestrator_fails_before_profiles_when_new_challenge_is_not_git_bound(tmp_path: Path, monkeypatch):
    import scripts.production_acceptance_orchestrator as orchestrator

    monkeypatch.setattr(orchestrator, "ROOT", tmp_path)
    monkeypatch.setenv("ACCEPTANCE_CHALLENGE_VERIFY_COMMAND", "true")
    called: list[str] = []
    monkeypatch.setattr(orchestrator, "execute", lambda profile, **kwargs: called.append(profile))

    result = orchestrator.orchestrate(confirm_real=True, profiles=("runtime", "testnet"))
    assert result["executed"] is False
    assert result["production_ready"] is False
    assert result["blocker"] == "NEW_CHALLENGE_NOT_VERIFIED"
    assert called == []
    assert "CHALLENGE_GIT_IDENTITY_UNAVAILABLE" in result["challenge_verification"]["problems"]
