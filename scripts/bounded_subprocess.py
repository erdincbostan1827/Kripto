from __future__ import annotations

import os
import signal
import subprocess
import time
import threading
from pathlib import Path
from typing import Mapping, Sequence

PROCESS_TREE_GRACE_SECONDS = 2.0
TEXT_ENCODING = "utf-8"
TEXT_ERRORS = "replace"


class _ProcessSignalGuard:
    """Temporarily make external termination signals clean the active child tree first."""

    def __init__(self, proc: subprocess.Popen[str]):
        self.proc = proc
        self.previous: dict[int, object] = {}
        self.enabled = os.name == "posix" and threading.current_thread() is threading.main_thread()

    def __enter__(self):
        if not self.enabled:
            return self
        for signum in (signal.SIGTERM, signal.SIGHUP):
            previous = signal.getsignal(signum)
            self.previous[signum] = previous

            def handler(received, frame, *, _previous=previous):
                terminate_process_tree(self.proc)
                if _previous == signal.SIG_IGN:
                    return
                if callable(_previous):
                    _previous(received, frame)
                    return
                signal.signal(received, signal.SIG_DFL)
                signal.raise_signal(received)

            signal.signal(signum, handler)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.enabled:
            for signum, previous in self.previous.items():
                signal.signal(signum, previous)
        return False


def terminate_process_tree(proc: subprocess.Popen[str], *, grace_seconds: float = PROCESS_TREE_GRACE_SECONDS) -> None:
    """Best-effort, fail-closed termination of a subprocess and its descendants.

    On POSIX, the process-group id remains equal to the original leader pid even
    after the leader exits. Do not return early merely because proc.poll() is
    non-None: descendants may still be alive and holding inherited pipes open.
    """
    leader_exited = proc.poll() is not None
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGTERM)
        elif os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
        else:
            if not leader_exited:
                proc.terminate()
    except (ProcessLookupError, OSError, subprocess.SubprocessError):
        if not leader_exited:
            try:
                proc.terminate()
            except (ProcessLookupError, OSError):
                pass

    deadline = time.monotonic() + max(0.0, grace_seconds)
    if os.name == "posix":
        # The leader may already have exited while descendants remain. Probe the
        # process group itself rather than using proc.poll() as the liveness test.
        while time.monotonic() < deadline:
            try:
                os.killpg(proc.pid, 0)
            except ProcessLookupError:
                return
            except PermissionError:
                break
            time.sleep(0.05)
    else:
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        if proc.poll() is not None:
            return
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        elif not leader_exited:
            proc.kill()
    except (ProcessLookupError, OSError):
        pass


def start_process_group(
    command: Sequence[str],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    stdout=None,
    stderr=None,
    text: bool = False,
) -> subprocess.Popen:
    """Start a command in an isolated process group for explicit lifecycle control."""
    popen_kwargs: dict = {
        "cwd": cwd,
        "env": env,
        "stdout": stdout,
        "stderr": stderr,
        "text": text,
        "shell": False,
    }
    if text:
        popen_kwargs["encoding"] = TEXT_ENCODING
        popen_kwargs["errors"] = TEXT_ERRORS
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    return subprocess.Popen(list(command), **popen_kwargs)


def guard_process_signals(proc: subprocess.Popen):
    """Public signal-guard adapter for long-lived process-group lifecycles."""
    return _ProcessSignalGuard(proc)


def run_captured_bytes(
    command: Sequence[str],
    *,
    cwd: Path | str,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run with binary stdout/stderr capture and fail-closed process-tree cleanup.

    Release/source identity probes sometimes need byte-exact Git object contents.
    Keep those bytes intact while applying the same timeout/cancellation lifecycle
    guarantees as the text runners.
    """
    popen_kwargs: dict = {
        "cwd": cwd,
        "env": env,
        "text": False,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(list(command), **popen_kwargs)
    try:
        with _ProcessSignalGuard(proc):
            stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or b""
        partial_err = exc.stderr or b""
        if isinstance(partial_out, str):
            partial_out = partial_out.encode(errors="replace")
        if isinstance(partial_err, str):
            partial_err = partial_err.encode(errors="replace")
        terminate_process_tree(proc)
        try:
            final_out, final_err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            terminate_process_tree(proc, grace_seconds=0.0)
            final_out, final_err = proc.communicate(timeout=5)
        raise subprocess.TimeoutExpired(
            list(command), timeout, output=final_out or partial_out, stderr=final_err or partial_err
        ) from None
    except BaseException:
        terminate_process_tree(proc)
        try:
            proc.communicate(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            terminate_process_tree(proc, grace_seconds=0.0)
        raise

    return subprocess.CompletedProcess(list(command), proc.returncode, stdout or b"", stderr or b"")


def run_captured_split(
    command: Sequence[str],
    *,
    cwd: Path | str,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run with separate stdout/stderr while enforcing process-tree cleanup."""
    popen_kwargs: dict = {
        "cwd": cwd,
        "env": env,
        "text": True,
        "encoding": TEXT_ENCODING,
        "errors": TEXT_ERRORS,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(list(command), **popen_kwargs)
    try:
        with _ProcessSignalGuard(proc):
            stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ""
        partial_err = exc.stderr or ""
        if isinstance(partial_out, bytes):
            partial_out = partial_out.decode(errors="replace")
        if isinstance(partial_err, bytes):
            partial_err = partial_err.decode(errors="replace")
        terminate_process_tree(proc)
        try:
            final_out, final_err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            terminate_process_tree(proc, grace_seconds=0.0)
            final_out, final_err = proc.communicate(timeout=5)
        raise subprocess.TimeoutExpired(
            list(command), timeout, output=final_out or partial_out, stderr=final_err or partial_err
        ) from None
    except BaseException:
        terminate_process_tree(proc)
        try:
            proc.communicate(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            terminate_process_tree(proc, grace_seconds=0.0)
        raise

    # A child can exit while a descendant in the same process group keeps an
    # inherited pipe open. communicate() would only return once those handles
    # close, so successful return here means the captured pipes are drained.
    return subprocess.CompletedProcess(list(command), proc.returncode, stdout or "", stderr or "")


def run_captured(
    command: Sequence[str],
    *,
    cwd: Path | str,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command in its own process group and never orphan descendants on timeout/cancellation."""
    popen_kwargs: dict = {
        "cwd": cwd,
        "env": env,
        "text": True,
        "encoding": TEXT_ENCODING,
        "errors": TEXT_ERRORS,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(list(command), **popen_kwargs)
    try:
        with _ProcessSignalGuard(proc):
            output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        partial = exc.output or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        terminate_process_tree(proc)
        try:
            final_output, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                pass
            final_output, _ = proc.communicate()
        raise subprocess.TimeoutExpired(list(command), timeout, output=final_output or partial) from None
    except BaseException:
        terminate_process_tree(proc)
        try:
            proc.communicate(timeout=5)
        except (subprocess.TimeoutExpired, OSError):
            try:
                proc.kill()
            except (ProcessLookupError, OSError):
                pass
        raise

    return subprocess.CompletedProcess(list(command), proc.returncode, output or "", None)
