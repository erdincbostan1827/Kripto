from __future__ import annotations

import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal/process-group contract")
def test_sigterm_to_runner_cleans_active_child_process_group(tmp_path: Path):
    repo = Path(__file__).resolve().parents[2]
    leader_pid = tmp_path / "leader.pid"
    child_pid = tmp_path / "child.pid"
    driver = tmp_path / "driver.py"
    driver.write_text(
        textwrap.dedent(
            f"""
            import sys
            from pathlib import Path
            sys.path.insert(0, {str(repo)!r})
            from scripts.bounded_subprocess import run_captured
            code = (
                "import os,subprocess,sys,time,pathlib; "
                "pathlib.Path({str(leader_pid)!r}).write_text(str(os.getpid())); "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                "pathlib.Path({str(child_pid)!r}).write_text(str(p.pid)); "
                "time.sleep(60)"
            )
            run_captured([sys.executable, '-c', code], cwd=Path({str(tmp_path)!r}), timeout=120)
            """
        ),
        encoding="utf-8",
    )
    proc = subprocess.Popen([sys.executable, str(driver)], cwd=repo)
    deadline = time.time() + 15
    while (not leader_pid.exists() or not child_pid.exists()) and time.time() < deadline:
        time.sleep(0.05)
    assert leader_pid.exists() and child_pid.exists()
    leader = int(leader_pid.read_text())
    child = int(child_pid.read_text())
    assert _pid_alive(leader)
    assert _pid_alive(child)

    os.kill(proc.pid, signal.SIGTERM)
    proc.wait(timeout=10)
    assert proc.returncode == -signal.SIGTERM

    deadline = time.time() + 5
    while (_pid_alive(leader) or _pid_alive(child)) and time.time() < deadline:
        time.sleep(0.05)
    assert not _pid_alive(leader)
    assert not _pid_alive(child)
