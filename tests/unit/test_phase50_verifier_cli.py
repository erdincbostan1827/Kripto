from __future__ import annotations

import subprocess
from pathlib import Path


def test_external_verifier_cli_import_path_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(
        ["python", "scripts/verify_external_acceptance.py", "reports/external_acceptance/manifest_runtime.json"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert "ModuleNotFoundError" not in proc.stdout
    assert proc.returncode in {0, 2}
