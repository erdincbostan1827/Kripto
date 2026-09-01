from __future__ import annotations

from pathlib import Path

import pytest

from scripts import bootstrap_dependency_locks as mod


def test_phase201_keyboard_interrupt_terminates_resolver_tree_and_propagates(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/npm")

    class FakeProc:
        pid = 9876
        returncode = None
        communicate_calls = 0

        def communicate(self, timeout=None):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise KeyboardInterrupt()
            return ("", None)

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    proc = FakeProc()
    terminated = []
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: proc)

    def fake_terminate_process_tree(value):
        assert value is proc
        value.returncode = -15
        terminated.append(True)

    monkeypatch.setattr(mod, "_terminate_process_tree", fake_terminate_process_tree)

    with pytest.raises(KeyboardInterrupt):
        mod._run(["npm", "install"], tmp_path, offline=False)

    assert terminated == [True]
    assert proc.poll() is not None
    assert proc.communicate_calls == 2


def test_phase201_system_exit_also_cleans_resolver_tree_and_propagates(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(mod.shutil, "which", lambda _: "/usr/bin/uv")

    class FakeProc:
        pid = 1111
        returncode = None
        communicate_calls = 0

        def communicate(self, timeout=None):
            self.communicate_calls += 1
            if self.communicate_calls == 1:
                raise SystemExit(7)
            return ("", None)

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    proc = FakeProc()
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(mod, "_terminate_process_tree", lambda value: setattr(value, "returncode", -15))

    with pytest.raises(SystemExit) as exc:
        mod._run(["uv", "lock"], tmp_path, offline=False)

    assert exc.value.code == 7
    assert proc.poll() is not None
    assert proc.communicate_calls == 2
