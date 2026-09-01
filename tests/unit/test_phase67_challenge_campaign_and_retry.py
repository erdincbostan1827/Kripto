from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from backend.app.release.acceptance_challenge import create_challenge, verify_challenge
import scripts.production_acceptance_orchestrator as orchestrator


def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase67@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase67"], cwd=root, check=True)
    (root / "seed").write_text("seed\n")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def test_new_challenge_uses_release_campaign_semantics(tmp_path: Path) -> None:
    _git(tmp_path)
    path = tmp_path / "challenge.json"
    created = create_challenge(tmp_path, path)
    payload = json.loads(path.read_text())
    assert payload["schema_version"] == "2.3"
    assert payload["release_campaign_bound"] is True
    assert "single_release_use" not in payload
    checked = verify_challenge(path, root=tmp_path)
    assert checked["verified"] is True
    assert checked["release_campaign_bound"] is True
    assert checked["sha256"] == created["sha256"]


def test_v1_challenge_is_backward_compatible(tmp_path: Path) -> None:
    sha = _git(tmp_path)
    path = tmp_path / "challenge.json"
    path.write_text(json.dumps({
        "schema_version": "1.0",
        "classification": "EXTERNAL_ACCEPTANCE_RELEASE_CHALLENGE",
        "challenge_id": "0123456789abcdef0123456789abcdef",
        "git_commit_sha": sha,
        "created_at": "2026-08-28T12:00:00+00:00",
        "single_release_use": True,
    }))
    checked = verify_challenge(path, root=tmp_path, max_age_hours=100000)
    assert "CHALLENGE_SCHEMA_UNSUPPORTED" not in checked["problems"]
    assert checked["release_campaign_bound"] is True


def test_orchestrator_reuse_rejects_unverified_challenge(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(orchestrator, "ROOT", tmp_path)
    called = []
    monkeypatch.setattr(orchestrator, "execute", lambda *a, **k: called.append((a, k)))
    result = orchestrator.orchestrate(confirm_real=True, profiles=("runtime",), reuse_current_challenge=True)
    assert result["production_ready"] is False
    assert result["blocker"] == "CURRENT_CHALLENGE_NOT_REUSABLE"
    assert called == []


def test_orchestrator_selected_profiles_only(monkeypatch, tmp_path: Path) -> None:
    _git(tmp_path)
    monkeypatch.setattr(orchestrator, "ROOT", tmp_path)
    monkeypatch.setattr(orchestrator, "verify_challenge", lambda *a, **k: {"verified": True})
    calls = []
    monkeypatch.setattr(orchestrator, "execute", lambda profile, **kwargs: calls.append(profile) or {"selected_all_pass": False, "groups": {}})
    monkeypatch.setattr(orchestrator, "merge", lambda **kwargs: {"selected_all_pass": False})
    monkeypatch.setattr(orchestrator, "verify_manifest", lambda *a, **k: {"verified": False, "selected_all_pass": False})
    monkeypatch.setattr(orchestrator, "_run_cli", lambda command, **kwargs: {"command": command, "exit_code": 2, "output": "blocked"})
    result = orchestrator.orchestrate(confirm_real=True, profiles=("runtime", "testnet"))
    assert calls == ["runtime", "testnet"]
    assert result["selected_profiles"] == ["runtime", "testnet"]
    assert result["production_ready"] is False


def test_orchestrator_rejects_unknown_profile(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(orchestrator, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        orchestrator.orchestrate(confirm_real=False, profiles=("not-real",))
