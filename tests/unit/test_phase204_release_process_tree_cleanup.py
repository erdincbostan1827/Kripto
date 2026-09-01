from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

import scripts.bounded_subprocess as bounded
import scripts.database_migration_guard as guard
import scripts.transactional_release_update as update


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def test_split_runner_preserves_stdout_and_stderr(tmp_path: Path):
    proc = bounded.run_captured_split(
        [sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr)"],
        cwd=tmp_path,
        timeout=5,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "out"
    assert proc.stderr.strip() == "err"


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_cleanup_reaches_descendant_after_group_leader_exits(tmp_path: Path):
    # Construct the exact edge case without relying on a fixed communicate()
    # timeout: wait until the leader has exited and its descendant is known alive,
    # then prove terminate_process_tree still reaches the process group.
    pid_file = tmp_path / "child.pid"
    code = (
        "import subprocess,sys,pathlib; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
        f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid))"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", code], cwd=tmp_path, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
    )
    deadline = time.time() + 10
    while (not pid_file.exists() or proc.poll() is None) and time.time() < deadline:
        time.sleep(0.05)
    assert pid_file.exists()
    assert proc.poll() == 0
    child_pid = int(pid_file.read_text())
    assert _pid_alive(child_pid)
    bounded.terminate_process_tree(proc, grace_seconds=0.5)
    deadline = time.time() + 3
    while _pid_alive(child_pid) and time.time() < deadline:
        time.sleep(0.05)
    assert not _pid_alive(child_pid)
    proc.communicate(timeout=2)


def test_database_probe_uses_bounded_split_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    seen = {}
    def fake(command, *, cwd, timeout):
        seen.update(command=command, cwd=cwd, timeout=timeout)
        return subprocess.CompletedProcess(command, 0, "m42\n", "")
    monkeypatch.setattr(guard, "run_captured_split", fake)
    assert guard.probe_database_head(["probe"], cwd=tmp_path, timeout_seconds=17) == "m42"
    assert seen == {"command": ["probe"], "cwd": tmp_path, "timeout": 17}


def test_post_cutover_timeout_fails_closed_via_bounded_runner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(update, "verify_runtime_binding", lambda root: {"accepted": True, "problems": []})
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0] if args else ["cmd"], kwargs.get("timeout", 1))
    monkeypatch.setattr(update, "run_captured_split", timeout)
    result = update.run_post_cutover_acceptance(tmp_path, command=["health"], timeout_seconds=3)
    assert result["accepted"] is False
    assert result["runtime_command"]["timed_out"] is True
    assert "POST_CUTOVER_RUNTIME_COMMAND_TIMEOUT" in result["problems"]


def test_split_runner_keyboard_interrupt_cleans_tree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    class FakeProc:
        pid = 12345
        returncode = None
        def communicate(self, timeout=None):
            raise KeyboardInterrupt()
        def poll(self):
            return self.returncode
    proc = FakeProc()
    cleaned = []
    monkeypatch.setattr(bounded.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(bounded, "terminate_process_tree", lambda p, **k: cleaned.append(p.pid))
    with pytest.raises(KeyboardInterrupt):
        bounded.run_captured_split(["cmd"], cwd=tmp_path, timeout=1)
    assert cleaned == [12345]
