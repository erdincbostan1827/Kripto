from pathlib import Path

import scripts.external.run_all_external_requirements as master

ROOT = Path(__file__).resolve().parents[2]


def test_phase144_master_plan_covers_all_open_requirements_without_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(master, "OUT", tmp_path / "master.json")
    called = {"canonical": 0, "frontend": 0, "tauri": 0}
    monkeypatch.setattr(master, "orchestrate", lambda **k: called.__setitem__("canonical", called["canonical"] + 1))
    monkeypatch.setattr(master, "run_frontend_browser", lambda **k: called.__setitem__("frontend", called["frontend"] + 1))
    monkeypatch.setattr(master, "evaluate_tauri_build", lambda **k: called.__setitem__("tauri", called["tauri"] + 1))
    result = master.execute_all(confirm_real=False, timeout=1)
    assert result["executed"] is False
    assert result["open_requirement_count"] == 100
    assert result["mapped_requirement_count"] == 100
    assert result["unmapped_requirement_count"] == 0
    assert result["production_ready"] is False
    assert called == {"canonical": 0, "frontend": 0, "tauri": 0}
    assert "REAL_TARGET_NOT_EXPLICITLY_CONFIRMED" in result["blockers"]


def test_phase144_master_never_promotes_if_any_standalone_required_step_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(master, "OUT", tmp_path / "master.json")
    monkeypatch.setattr(master, "orchestrate", lambda **k: {
        "production_ready": True,
        "profiles": {"locks": {"selected_all_pass": True}, "runtime": {"selected_all_pass": True}},
    })
    monkeypatch.setattr(master, "run_frontend_browser", lambda **k: {
        "verified": True, "git_commit_sha": "a" * 40, "manifest_sha256": "b" * 64,
        "frontend_lock_sha256": "c" * 64, "blockers": [],
    })
    monkeypatch.setattr(master, "evaluate_tauri_build", lambda **k: {
        "verified": False, "frontend_lock_sha256": "c" * 64, "cargo_lock_sha256": None,
        "blockers": ["TAURI_CARGO_LOCK_MISSING"],
    })
    result = master.execute_all(confirm_real=True, timeout=1)
    assert result["canonical_profiles_pass"] is True
    assert result["standalone_required_steps_pass"] is False
    assert result["production_ready"] is False
    assert "DESKTOP_BUILD_READINESS_NOT_PASS" in result["blockers"]


def test_phase144_readiness_dossier_surfaces_single_master_command():
    source = (ROOT / "scripts/production_readiness_dossier.py").read_text(encoding="utf-8")
    assert "run-all-external" in source
    assert "scripts/external/run_all_external_requirements.py --confirm-real-target" in source
    assert "master_all_external_requirements" in source
