from __future__ import annotations

import subprocess

import pytest

import scripts.bounded_subprocess as bounded


class FakeProc:
    def __init__(self, *, timeout_once: bool = False, interrupt_once: bool = False):
        self.pid = 43210
        self.returncode = None
        self._timeout_once = timeout_once
        self._interrupt_once = interrupt_once
        self._calls = 0
        self.terminated = False

    def communicate(self, timeout=None):
        self._calls += 1
        if self._interrupt_once and self._calls == 1:
            raise KeyboardInterrupt()
        if self._timeout_once and self._calls == 1:
            raise subprocess.TimeoutExpired(["pytest"], timeout or 1, output="partial")
        self.returncode = -15 if self.terminated else 0
        return ("final", None)

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.terminated = True
        self.returncode = -9


def test_timeout_terminates_process_tree_and_preserves_timeout(monkeypatch, tmp_path):
    proc = FakeProc(timeout_once=True)
    monkeypatch.setattr(bounded.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(bounded, "terminate_process_tree", lambda p: p.terminate())
    with pytest.raises(subprocess.TimeoutExpired) as exc:
        bounded.run_captured(["python", "-m", "pytest"], cwd=tmp_path, timeout=1)
    assert proc.terminated is True
    assert exc.value.output == "final"


def test_keyboard_interrupt_terminates_process_tree_then_reraises(monkeypatch, tmp_path):
    proc = FakeProc(interrupt_once=True)
    monkeypatch.setattr(bounded.subprocess, "Popen", lambda *a, **k: proc)
    monkeypatch.setattr(bounded, "terminate_process_tree", lambda p: p.terminate())
    with pytest.raises(KeyboardInterrupt):
        bounded.run_captured(["python", "-m", "pytest"], cwd=tmp_path, timeout=1)
    assert proc.terminated is True


def test_posix_process_group_uses_term_then_kill_when_needed(monkeypatch):
    class Stubborn:
        pid = 77
        def poll(self): return None
        def terminate(self): pass
        def kill(self): pass
    signals = []
    monkeypatch.setattr(bounded.os, "name", "posix")
    monkeypatch.setattr(bounded.os, "killpg", lambda pid, sig: signals.append((pid, sig)))
    monkeypatch.setattr(bounded.time, "monotonic", iter([0.0, 1.0]).__next__)
    monkeypatch.setattr(bounded.time, "sleep", lambda _: None)
    bounded.terminate_process_tree(Stubborn(), grace_seconds=0.1)
    assert signals[0] == (77, bounded.signal.SIGTERM)
    assert signals[-1] == (77, bounded.signal.SIGKILL)
