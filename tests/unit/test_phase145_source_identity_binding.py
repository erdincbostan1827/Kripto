from pathlib import Path

import scripts.external.run_all_external_requirements as master
from scripts.external.tauri_build_readiness import evaluate

ROOT = Path(__file__).resolve().parents[2]


def _canonical(sha: str) -> dict:
    return {
        "production_ready": True,
        "challenge": {"git_commit_sha": sha},
        "challenge_verification": {"git_commit_sha": sha, "verified": True},
        "profiles": {"locks": {"selected_all_pass": True}, "runtime": {"selected_all_pass": True}},
    }


def test_phase145_master_requires_same_source_identity_across_canonical_browser_and_desktop(tmp_path, monkeypatch):
    expected = "1" * 40
    monkeypatch.setattr(master, "OUT", tmp_path / "master.json")
    monkeypatch.setattr(master, "_current_git_sha", lambda: expected)
    monkeypatch.setattr(master, "orchestrate", lambda **k: _canonical(expected))
    monkeypatch.setattr(master, "run_frontend_browser", lambda **k: {
        "verified": True,
        "git_commit_sha": expected,
        "manifest_sha256": "a" * 64,
        "frontend_lock_sha256": "b" * 64,
        "blockers": [],
    })
    monkeypatch.setattr(master, "evaluate_tauri_build", lambda **k: {
        "verified": True,
        "git_commit_sha": "2" * 40,
        "manifest_sha256": "c" * 64,
        "frontend_lock_sha256": "b" * 64,
        "cargo_lock_sha256": "d" * 64,
        "blockers": [],
    })
    result = master.execute_all(confirm_real=True, timeout=1)
    assert result["canonical_profiles_pass"] is True
    assert result["standalone_required_steps_pass"] is True
    assert result["source_identity_binding"]["verified"] is False
    assert "SOURCE_IDENTITY_MISMATCH:tauri_git_sha" in result["source_identity_binding"]["problems"]
    assert "SOURCE_IDENTITY_BINDING_NOT_PASS" in result["blockers"]
    assert result["production_ready"] is False


def test_phase145_master_accepts_identity_binding_only_when_git_and_frontend_lock_match(tmp_path, monkeypatch):
    expected = "3" * 40
    lock = "e" * 64
    monkeypatch.setattr(master, "OUT", tmp_path / "master.json")
    monkeypatch.setattr(master, "_current_git_sha", lambda: expected)
    monkeypatch.setattr(master, "orchestrate", lambda **k: _canonical(expected))
    monkeypatch.setattr(master, "run_frontend_browser", lambda **k: {
        "verified": True, "git_commit_sha": expected, "manifest_sha256": "a" * 64,
        "frontend_lock_sha256": lock, "blockers": [],
    })
    monkeypatch.setattr(master, "evaluate_tauri_build", lambda **k: {
        "verified": True, "git_commit_sha": expected, "manifest_sha256": "c" * 64,
        "frontend_lock_sha256": lock, "cargo_lock_sha256": "d" * 64, "blockers": [],
    })
    result = master.execute_all(confirm_real=True, timeout=1)
    assert result["source_identity_binding"]["verified"] is True
    assert result["source_identity_binding"]["problems"] == []
    assert result["all_required_execution_steps_pass"] is True
    assert result["production_ready"] is True


def test_phase145_tauri_readiness_persists_immutable_git_bound_manifest():
    result = evaluate(confirm_real=False, timeout=1)
    assert result["git_commit_sha"] is not None
    assert result["run_id"]
    assert result["run_directory"].startswith("reports/external_acceptance/tauri_build_runs/")
    assert len(result["manifest_sha256"]) == 64
    manifest = ROOT / result["run_directory"] / "manifest.json"
    assert manifest.is_file()
    assert "GIT_IDENTITY_UNAVAILABLE" not in result["blockers"]
