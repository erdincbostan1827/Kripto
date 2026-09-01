from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.bounded_subprocess as bounded
import scripts.generate_release_manifest as release
import scripts.test_inventory as inventory
import scripts.verify_source_locks as locks


def test_run_captured_bytes_preserves_binary_stdout_and_stderr(tmp_path: Path):
    proc = bounded.run_captured_bytes(
        [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'A\\x00B');sys.stderr.buffer.write(b'E\\x00R')"],
        cwd=tmp_path,
        timeout=10,
    )
    assert proc.returncode == 0
    assert proc.stdout == b"A\x00B"
    assert proc.stderr == b"E\x00R"


def test_release_manifest_git_timeout_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(release, "ROOT", tmp_path)
    monkeypatch.setattr(
        release,
        "run_captured_bytes",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired(a[0], k.get("timeout", 10))),
    )
    assert release.git_sha() == "UNAVAILABLE"
    assert release.migration_head() == "UNKNOWN"


def test_source_lock_git_timeout_does_not_verify_repository(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(
        locks,
        "run_captured_bytes",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired(a[0], k.get("timeout", 10))),
    )
    monkeypatch.setattr(locks, "verify_source_package_identity", lambda *a, **k: {"verified": False, "problems": ["NO_PACKAGE"]})
    result = locks.verify_source_locks(tmp_path)
    assert result["verified"] is False
    assert result["repository_verified"] is False
    assert result["identity_verified"] is False
    assert any("GIT_UNAVAILABLE:TimeoutExpired" in p for p in result["problems"])


def test_test_inventory_git_timeout_rejects_identity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(
        inventory,
        "run_captured_bytes",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired(a[0], k.get("timeout", 10))),
    )
    assert inventory._git_sha(tmp_path) is None


def test_release_manifest_git_show_failure_never_matches_head(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(release, "ROOT", tmp_path)
    path = tmp_path / "uv.lock"
    path.write_bytes(b"working")

    def fake(command, **kwargs):
        if command[1:3] == ["ls-files", "--error-unmatch"]:
            return subprocess.CompletedProcess(command, 0, b"uv.lock\n", b"")
        if command[1] == "show":
            return subprocess.CompletedProcess(command, 1, b"", b"missing")
        raise AssertionError(command)

    monkeypatch.setattr(release, "run_captured_bytes", fake)
    state = release.git_tracked_file_state(path)
    assert state["tracked"] is True
    assert state["matches_head"] is False
    assert state["source_compliant"] is False
