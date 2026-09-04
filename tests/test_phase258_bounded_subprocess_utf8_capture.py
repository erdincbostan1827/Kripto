from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.bounded_subprocess import run_captured, run_captured_split, start_process_group


ROOT = Path(__file__).resolve().parents[1]


def _emit_invalid_utf8_code(*, split: bool = False) -> str:
    if split:
        return (
            "import sys; "
            "sys.stdout.buffer.write(b'out\\x81tail'); "
            "sys.stdout.buffer.flush(); "
            "sys.stderr.buffer.write(b'err\\x81tail'); "
            "sys.stderr.buffer.flush()"
        )
    return "import sys; sys.stdout.buffer.write(b'prefix\\x81suffix'); sys.stdout.buffer.flush()"


def test_run_captured_replaces_undecodable_bytes_instead_of_crashing() -> None:
    result = run_captured(
        [sys.executable, "-c", _emit_invalid_utf8_code()],
        cwd=ROOT,
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stdout == "prefix\ufffdsuffix"


def test_run_captured_split_replaces_undecodable_bytes_on_both_streams() -> None:
    result = run_captured_split(
        [sys.executable, "-c", _emit_invalid_utf8_code(split=True)],
        cwd=ROOT,
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stdout == "out\ufffdtail"
    assert result.stderr == "err\ufffdtail"


def test_start_process_group_text_mode_uses_safe_utf8_decoding() -> None:
    proc = start_process_group(
        [sys.executable, "-c", _emit_invalid_utf8_code(split=True)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(timeout=10)

    assert proc.returncode == 0
    assert stdout == "out\ufffdtail"
    assert stderr == "err\ufffdtail"
