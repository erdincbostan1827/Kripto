from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_contract_parity_direct_cli_works():
    proc = subprocess.run(
        ['python', 'scripts/verify_acceptance_contract_parity.py'],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    assert proc.returncode == 0, proc.stdout
    assert 'PRODUCTION_ACCEPTANCE_CONTRACT_PARITY' in proc.stdout
    assert 'ModuleNotFoundError' not in proc.stdout
