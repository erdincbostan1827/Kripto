from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _help(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, script, "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


def test_phase208_direct_cli_imports_work_for_hardened_helpers():
    for script in (
        "scripts/test_inventory.py",
        "scripts/trusted_signing_adapter.py",
        "scripts/external/frontend_browser_acceptance.py",
        "scripts/external/tauri_build_readiness.py",
    ):
        result = _help(script)
        assert result.returncode == 0, (script, result.stdout, result.stderr)
        assert "ModuleNotFoundError" not in result.stderr
