import json
from pathlib import Path

import scripts.production_acceptance_orchestrator as orch


def test_orchestrator_is_plan_only_without_explicit_real_target(tmp_path, monkeypatch):
    monkeypatch.setattr(orch, "ROOT", tmp_path)
    called = {"execute": 0}
    monkeypatch.setattr(orch, "execute", lambda *a, **k: called.__setitem__("execute", called["execute"] + 1))
    result = orch.orchestrate(confirm_real=False)
    assert result["executed"] is False
    assert result["production_ready"] is False
    assert called["execute"] == 0
    assert (tmp_path / "reports/PRODUCTION_ACCEPTANCE_ORCHESTRATION.json").is_file()


def test_orchestrator_profile_set_covers_all_release_external_workflows():
    assert set(orch.PROFILES) == {"locks", "runtime", "restart-drills", "supply-chain", "pitr", "ha", "worm", "testnet", "provenance", "campaigns"}


def test_orchestrator_never_promotes_when_release_gate_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(orch, "ROOT", tmp_path)
    reports = tmp_path / "reports/external_acceptance"
    reports.mkdir(parents=True)
    monkeypatch.setattr(orch, "create_challenge", lambda root, path: {"challenge_id": "x"*16, "sha256": "a"*64})
    monkeypatch.setattr(orch, "verify_challenge", lambda *a, **k: {"verified": True})
    monkeypatch.setattr(orch, "execute", lambda profile, **k: {"selected_all_pass": True, "groups": {}, "manifest_sha256": "b"*64, "immutable_manifest": "m", "run_id": profile})
    monkeypatch.setattr(orch, "merge", lambda **k: {"selected_all_pass": True})
    monkeypatch.setattr(orch, "verify_manifest", lambda *a, **k: {"verified": True, "selected_all_pass": True})
    calls = iter([
        {"command": [], "exit_code": 0, "output": "manifest ok"},
        {"command": [], "exit_code": 1, "output": "gate blocked"},
        {"command": [], "exit_code": 0, "output": "dossier"},
    ])
    monkeypatch.setattr(orch, "_run_cli", lambda cmd, **kwargs: next(calls))
    result = orch.orchestrate(confirm_real=True, timeout=1)
    assert result["production_ready"] is False
    assert result["release_gate"]["exit_code"] == 1
