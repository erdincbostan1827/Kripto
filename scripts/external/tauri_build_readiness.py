from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / 'frontend'
TAURI = FRONTEND / 'src-tauri'
OUT = ROOT / 'reports' / 'external_acceptance' / 'tauri_build_readiness.json'


def digest(p: Path) -> str | None:
    return sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def git_sha() -> str | None:
    try:
        p = subprocess.run(['git','rev-parse','HEAD'], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10, check=False)
        value = (p.stdout or '').strip().lower()
        return value if p.returncode == 0 and len(value) == 40 else None
    except Exception:
        return None


def run_cmd(cmd: list[str], cwd: Path, timeout: int) -> dict:
    if not shutil.which(cmd[0]):
        return {'command': cmd, 'status': 'BLOCKED', 'exit_code': None, 'blocker': f'TOOL_UNAVAILABLE:{cmd[0]}'}
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return {'command': cmd, 'status': 'PASS' if p.returncode == 0 else 'BLOCKED', 'exit_code': p.returncode, 'blocker': None if p.returncode == 0 else f'EXIT_CODE:{p.returncode}', 'output': (p.stdout or '')[-12000:]}
    except subprocess.TimeoutExpired as e:
        return {'command': cmd, 'status': 'BLOCKED', 'exit_code': None, 'blocker': 'TIMEOUT', 'output': str(e)}


def evaluate(*, confirm_real: bool, timeout: int = 600) -> dict:
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_dir = OUT.parent / 'tauri_build_runs' / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    frontend_lock = FRONTEND / 'package-lock.json'
    cargo_lock = TAURI / 'Cargo.lock'
    blockers = []
    if not confirm_real: blockers.append('REAL_TARGET_NOT_EXPLICITLY_CONFIRMED')
    if not frontend_lock.is_file(): blockers.append('FRONTEND_LOCK_MISSING')
    if not cargo_lock.is_file(): blockers.append('TAURI_CARGO_LOCK_MISSING')
    cargo = shutil.which('cargo'); rustc = shutil.which('rustc')
    if not cargo: blockers.append('CARGO_UNAVAILABLE')
    if not rustc: blockers.append('RUSTC_UNAVAILABLE')
    evidence: dict[str, object] = {}
    if cargo: evidence['cargo_version'] = run_cmd(['cargo','--version'], ROOT, 30)
    if rustc: evidence['rustc_version'] = run_cmd(['rustc','--version'], ROOT, 30)

    if not blockers:
        evidence['npm_ci'] = run_cmd(['npm','ci','--ignore-scripts'], FRONTEND, timeout)
        if evidence['npm_ci']['status'] != 'PASS': blockers.append('NPM_CI_FAILED')
    if not blockers:
        evidence['frontend_build'] = run_cmd(['npm','run','build'], FRONTEND, timeout)
        if evidence['frontend_build']['status'] != 'PASS': blockers.append('FRONTEND_BUILD_FAILED')
    if not blockers:
        evidence['cargo_build_locked'] = run_cmd(['cargo','build','--locked','--manifest-path',str(TAURI/'Cargo.toml')], ROOT, timeout)
        if evidence['cargo_build_locked']['status'] != 'PASS': blockers.append('TAURI_LOCKED_BUILD_FAILED')

    payload = {
        'schema_version': '1.1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'classification': 'REAL_TAURI_BUILD_READINESS_NOT_SIGNING_EVIDENCE',
        'truth_policy': 'PASS requires explicit real-target confirmation, current Git identity, frontend package-lock, Tauri Cargo.lock, Rust/Cargo, lock-bound frontend install/build, and cargo build --locked. It never claims installer signing or CI provenance.',
        'run_id': run_id,
        'run_directory': str(run_dir.relative_to(ROOT)),
        'git_commit_sha': git_sha(),
        'verified': not blockers,
        'blockers': sorted(set(blockers)),
        'frontend_lock_sha256': digest(frontend_lock),
        'cargo_lock_sha256': digest(cargo_lock),
        'cargo_path': cargo,
        'rustc_path': rustc,
        'evidence': evidence,
    }
    if payload['git_commit_sha'] is None:
        payload['blockers'] = sorted(set([*payload['blockers'], 'GIT_IDENTITY_UNAVAILABLE']))
        payload['verified'] = False
    immutable = run_dir / 'manifest.json'
    immutable.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    payload['manifest_sha256'] = digest(immutable)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--confirm-real-target', action='store_true')
    ap.add_argument('--timeout', type=int, default=600)
    args = ap.parse_args()
    result = evaluate(confirm_real=args.confirm_real_target, timeout=max(args.timeout, 1))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['verified'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
