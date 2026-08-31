from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import external_acceptance_preflight as preflight
from scripts.external_acceptance_runner import build_plan, _group_status, Evidence


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / "README").write_text("x\n")
    _git(root, "add", "README")
    _git(root, "commit", "-qm", "init")
    return root


def test_preflight_rejects_untracked_generated_locks(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    (root / "uv.lock").write_text("generated\n")
    (root / "frontend").mkdir()
    (root / "frontend/package-lock.json").write_text("{}\n")
    monkeypatch.setattr(preflight, "ROOT", root)
    checks = preflight._source_lock_checks()
    assert {c.status for c in checks} == {"BLOCKED"}
    assert all("NOT_TRACKED_IN_HEAD" in c.detail for c in checks)


def test_preflight_accepts_only_committed_unchanged_locks(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    (root / "uv.lock").write_text("committed\n")
    (root / "frontend").mkdir()
    (root / "frontend/package-lock.json").write_text("{}\n")
    _git(root, "add", "uv.lock", "frontend/package-lock.json")
    _git(root, "commit", "-qm", "locks")
    monkeypatch.setattr(preflight, "ROOT", root)
    checks = preflight._source_lock_checks()
    assert {c.status for c in checks} == {"READY"}
    assert all("matches_head=true" in c.detail for c in checks)


def test_lock_profile_runs_source_compliance_before_dependency_commands():
    plan = build_plan("locks")
    assert plan[0][0] == "source_lock_compliance"
    assert plan[0][1] == ["python", "scripts/verify_source_locks.py"]


def test_lock_group_cannot_pass_without_source_compliance_evidence():
    rows = [
        Evidence("backend_lock", "PASS", True, (), 0, None, None, None, "2026-01-01T00:00:00+00:00"),
        Evidence("frontend_lock", "PASS", True, (), 0, None, None, None, "2026-01-01T00:00:00+00:00"),
        Evidence("frontend_build", "PASS", True, (), 0, None, None, None, "2026-01-01T00:00:00+00:00"),
    ]
    assert _group_status(rows)["dependency_locks_and_frontend_build"] == "BLOCKED"
