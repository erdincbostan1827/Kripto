from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.release_gate import _git_lock_is_source_compliant, evaluate_release_gate
from scripts.verify_source_locks import verify_source_locks


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "phase100@example.invalid")
    _git(root, "config", "user.name", "Phase100")


def test_source_zip_without_git_metadata_is_fail_closed_not_exception(tmp_path: Path):
    (tmp_path / "frontend").mkdir()
    (tmp_path / "uv.lock").write_text("lock\n")
    (tmp_path / "frontend/package-lock.json").write_text("{}\n")
    result = verify_source_locks(tmp_path)
    assert result["verified"] is False
    assert result["repository_verified"] is False
    assert "GIT_REPOSITORY_UNAVAILABLE" in result["problems"]
    assert all(row["source_compliant"] is False for row in result["locks"])


def test_canonical_verifier_binds_locks_to_exact_head(tmp_path: Path):
    _repo(tmp_path)
    (tmp_path / "frontend").mkdir()
    (tmp_path / "uv.lock").write_text("backend\n")
    (tmp_path / "frontend/package-lock.json").write_text("{}\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "locks")
    result = verify_source_locks(tmp_path)
    assert result["verified"] is True
    assert result["repository_verified"] is True
    assert len(result["git_head"]) == 40
    assert _git_lock_is_source_compliant(tmp_path, "uv.lock") == (True, "PASS")
    assert _git_lock_is_source_compliant(tmp_path, "frontend/package-lock.json") == (True, "PASS")


def test_lock_change_after_commit_is_detected_by_both_gate_paths(tmp_path: Path):
    _repo(tmp_path)
    (tmp_path / "frontend").mkdir()
    (tmp_path / "uv.lock").write_text("backend\n")
    (tmp_path / "frontend/package-lock.json").write_text("{}\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "locks")
    (tmp_path / "uv.lock").write_text("tampered\n")
    result = verify_source_locks(tmp_path)
    assert result["verified"] is False
    assert "uv.lock:DIFFERS_FROM_HEAD" in result["problems"]
    assert _git_lock_is_source_compliant(tmp_path, "uv.lock") == (False, "uv.lock differs from Git HEAD")


def test_release_gate_reports_unverifiable_repository(tmp_path: Path):
    # Minimal files only: the important Phase 100 property is that repository identity
    # becomes an explicit blocker rather than an uncaught Git/process error.
    (tmp_path / "requirements_acceptance_matrix.yaml").write_text("requirements: []\n")
    (tmp_path / "RELEASE_MANIFEST.json").write_text('{"acceptance": {}, "live_enabled": false, "default_mode": "PAPER"}\n')
    blockers = evaluate_release_gate(tmp_path)
    assert "source repository identity is not verifiable" in blockers
