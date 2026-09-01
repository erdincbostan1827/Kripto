from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Mapping, Sequence

PROCESS_TREE_GRACE_SECONDS = 2.0


def terminate_process_tree(proc: subprocess.Popen[str], *, grace_seconds: float = PROCESS_TREE_GRACE_SECONDS) -> None:
    """Best-effort, fail-closed termination of a subprocess and its descendants."""
    if proc.poll() is not None:
        return
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
            proc.terminate()
    except (ProcessLookupError, OSError, subprocess.SubprocessError):
        try:
            proc.terminate()
        except (ProcessLookupError, OSError):
            pass

    deadline = time.monotonic() + max(0.0, grace_seconds)
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    if proc.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
    except (ProcessLookupError, OSError):
        pass


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
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    proc = subprocess.Popen(list(command), **popen_kwargs)
    try:
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
