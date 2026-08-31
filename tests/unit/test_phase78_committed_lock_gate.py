import json
import subprocess
from pathlib import Path

from scripts.generate_release_manifest import git_tracked_file_state
from scripts.release_gate import _git_lock_is_source_compliant


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.DEVNULL)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"; root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    (root / "seed.txt").write_text("seed\n")
    _git(root, "add", "seed.txt"); _git(root, "commit", "-qm", "seed")
    return root


def test_generated_untracked_lock_never_satisfies_source_gate(tmp_path):
    root = _repo(tmp_path)
    (root / "uv.lock").write_text("generated-in-ci\n")
    ok, reason = _git_lock_is_source_compliant(root, "uv.lock")
    assert not ok
    assert "not tracked" in reason


def test_modified_tracked_lock_never_satisfies_source_gate(tmp_path):
    root = _repo(tmp_path)
    (root / "uv.lock").write_text("committed\n")
    _git(root, "add", "uv.lock"); _git(root, "commit", "-qm", "lock")
    (root / "uv.lock").write_text("regenerated\n")
    ok, reason = _git_lock_is_source_compliant(root, "uv.lock")
    assert not ok
    assert "differs from Git HEAD" in reason


def test_committed_unchanged_lock_is_source_compliant(tmp_path):
    root = _repo(tmp_path)
    (root / "uv.lock").write_text("committed\n")
    _git(root, "add", "uv.lock"); _git(root, "commit", "-qm", "lock")
    assert _git_lock_is_source_compliant(root, "uv.lock") == (True, "PASS")
