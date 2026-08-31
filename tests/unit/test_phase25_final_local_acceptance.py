from __future__ import annotations

from pathlib import Path
import json

from backend.app.data.candles import CLOSED_CANDLE_ONLY, closed_only
from backend.app.release.acceptance_harness import run_command_attempt, write_attempt_manifest

ROOT = Path(__file__).resolve().parents[2]


def test_phase25_install_scripts_exist_for_windows_and_linux_and_linux_is_executable():
    windows = ROOT / 'INSTALL_WINDOWS.ps1'
    linux = ROOT / 'install.sh'
    assert windows.is_file() and windows.stat().st_size > 0
    assert linux.is_file() and linux.stat().st_size > 0
    assert linux.stat().st_mode & 0o111


def test_phase25_closed_candle_only_is_explicit_safe_default():
    assert CLOSED_CANDLE_ONLY is True
    rows = [
        {'close_time': __import__('datetime').datetime(2026,1,1,12,0,tzinfo=__import__('datetime').timezone.utc), 'closed': True},
        {'close_time': __import__('datetime').datetime(2026,1,1,12,5,tzinfo=__import__('datetime').timezone.utc), 'closed': False},
    ]
    out = closed_only(rows, __import__('datetime').datetime(2026,1,1,12,10,tzinfo=__import__('datetime').timezone.utc))
    assert out == [rows[0]]


def test_phase25_acceptance_harness_records_missing_external_tool_as_blocked(tmp_path: Path):
    # Intentionally impossible executable proves absence is evidence, not PASS.
    e = run_command_attempt(key='missing_tool', command=['definitely-not-a-real-tool-phase25'], root=tmp_path,
                            evidence_dir=tmp_path/'evidence', real_system=True)
    assert e.status == 'BLOCKED' and not e.tool_available and e.blocker.startswith('TOOL_UNAVAILABLE:')
    assert (tmp_path/e.evidence_path).is_file()


def test_phase25_acceptance_harness_never_promotes_local_simulation_to_external_pass(tmp_path: Path):
    e = run_command_attempt(key='sim', command=['python','-c','print("ok")'], root=tmp_path,
                            evidence_dir=tmp_path/'evidence', real_system=False)
    assert e.exit_code == 0 and e.status == 'BLOCKED' and e.blocker == 'SIMULATED_NOT_EXTERNAL_ACCEPTANCE'


def test_phase25_acceptance_attempt_manifest_is_machine_readable_and_fail_closed(tmp_path: Path):
    e = run_command_attempt(key='sim', command=['python','-c','print("ok")'], root=tmp_path,
                            evidence_dir=tmp_path/'evidence', real_system=False)
    payload = write_attempt_manifest([e], tmp_path/'attempts.json')
    loaded = json.loads((tmp_path/'attempts.json').read_text())
    assert payload['all_pass'] is False and loaded['attempts'][0]['status'] == 'BLOCKED'
