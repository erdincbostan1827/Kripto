from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def test_external_acceptance_preflight_direct_cli_has_no_import_error():
    proc = subprocess.run(
        ["python", "scripts/external_acceptance_preflight.py"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    # A blocked preflight is expected locally; import/runtime crash is not.
    assert proc.returncode in {0, 2}, proc.stdout
    assert "ModuleNotFoundError" not in proc.stdout
    assert '"classification": "EXTERNAL_ACCEPTANCE_PREFLIGHT_ONLY_NOT_ACCEPTANCE_EVIDENCE"' in proc.stdout
