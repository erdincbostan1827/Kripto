from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

import scripts.bounded_subprocess as bounded
import scripts.external.frontend_browser_acceptance as browser


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def test_start_process_group_uses_isolated_posix_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    seen = {}
    class FakeProc: pass
    def fake_popen(command, **kwargs):
        seen['command'] = command
        seen.update(kwargs)
        return FakeProc()
    monkeypatch.setattr(bounded.subprocess, 'Popen', fake_popen)
    bounded.start_process_group(['cmd'], cwd=tmp_path, env={'X':'1'})
    assert seen['command'] == ['cmd']
    assert seen['shell'] is False
    if os.name == 'posix':
        assert seen['start_new_session'] is True


def test_frontend_browser_server_uses_bounded_process_group_primitives():
    text = Path(browser.__file__).read_text(encoding='utf-8')
    assert 'server = start_process_group(' in text
    assert 'terminate_process_tree(server)' in text
    assert 'server = subprocess.Popen(' not in text


@pytest.mark.skipif(os.name != 'posix', reason='POSIX process-group lifecycle contract')
def test_operation_lock_exec_kills_descendant_after_leader_exits(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    lock_dir = tmp_path / 'lock'
    lock_dir.mkdir()
    child_pid_file = tmp_path / 'child.pid'
    code = (
        "import subprocess,sys,pathlib; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        f"pathlib.Path({str(child_pid_file)!r}).write_text(str(p.pid))"
    )
    proc = subprocess.run(
        [
            sys.executable, str(root / 'scripts/operation_lock_exec.py'),
            '--lock-dir', str(lock_dir), '--operation', 'phase210-test',
            '--heartbeat-check-seconds', '0.05', '--', sys.executable, '-c', code,
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    assert child_pid_file.exists()
    child_pid = int(child_pid_file.read_text())
    deadline = time.time() + 5
    while _pid_alive(child_pid) and time.time() < deadline:
        time.sleep(0.05)
    assert not _pid_alive(child_pid)
    assert not (lock_dir / '.ctp-operation.lock').exists()
