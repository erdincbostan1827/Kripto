from __future__ import annotations

import subprocess
from pathlib import Path

from scripts import bootstrap_dependency_locks as mod


def test_phase198_timeout_terminates_entire_resolver_process_tree(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mod, "LOCK_RESOLUTION_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(mod, "PROCESS_TREE_GRACE_SECONDS", 0.0)
    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/npm")

    class FakeProc:
        pid = 424242
        returncode = None
        killed = False
        communicate_calls = 0

        def communicate(self, timeout=None):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise subprocess.TimeoutExpired(["npm", "install"], timeout, output="partial registry output")
            self.returncode = -9
            return ("partial registry output", None)

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.killed = True
            self.returncode = -9

    proc = FakeProc()
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(mod.os, "name", "other")

    result = mod._run(["npm", "install"], tmp_path, offline=False)
    assert result["ok"] is False
    assert result["blocker"] == "COMMAND_OR_NETWORK_TIMEOUT"
    assert result["process_tree_terminated"] is True
    assert "partial registry output" in result["output"]


def test_phase198_posix_tree_kill_targets_process_group(monkeypatch):
    calls: list[tuple[int, int]] = []

    class FakeProc:
        pid = 777
        returncode = None
        def poll(self):
            return self.returncode

    proc = FakeProc()
    monkeypatch.setattr(mod.os, "name", "posix")
    monkeypatch.setattr(mod, "PROCESS_TREE_GRACE_SECONDS", 0.0)

    def fake_killpg(pid: int, sig: int):
        calls.append((pid, sig))
        if sig == mod.signal.SIGKILL:
            proc.returncode = -9

    monkeypatch.setattr(mod.os, "killpg", fake_killpg)
    mod._terminate_process_tree(proc)
    assert calls[0] == (777, mod.signal.SIGTERM)
    assert calls[-1] == (777, mod.signal.SIGKILL)
