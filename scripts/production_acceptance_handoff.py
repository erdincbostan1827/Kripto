from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.verify_source_locks import verify_source_locks
    from scripts.verify_source_package_identity import verify_source_package_identity
    from scripts.bounded_subprocess import run_captured_split
except ModuleNotFoundError:  # direct `python scripts/production_acceptance_handoff.py`
    from verify_source_locks import verify_source_locks
    from verify_source_package_identity import verify_source_package_identity
    from bounded_subprocess import run_captured_split

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'PRODUCTION_ACCEPTANCE_HANDOFF.json'
WORKFLOW = '.github/workflows/production-acceptance.yml'
REQUIRED_ENVIRONMENT_VARS = ['ACCEPTANCE_ENVIRONMENT_ID', 'ACCEPTANCE_TOPOLOGY_HASH']
GIT_PROBE_TIMEOUT_SECONDS = 10
REQUIRED_SECRETS = [
    'BINANCE_TESTNET_API_KEY', 'BINANCE_TESTNET_API_SECRET',
    'PITR_DRILL_COMMAND', 'PITR_EVIDENCE_JSON',
    'HA_DRILL_COMMAND', 'HA_EVIDENCE_JSON',
    'WORM_ACCEPTANCE_COMMAND', 'WORM_EVIDENCE_JSON',
    'RESTART_DRILL_COMMAND', 'RESTART_EVIDENCE_JSON',
    'PROVENANCE_SIGN_VERIFY_COMMAND',
    'ACCEPTANCE_CHALLENGE_VERIFY_COMMAND', 'LEDGER_CHECKPOINT_SIGN_COMMAND', 'ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND',
]


def git(*args: str, root: Path = ROOT) -> str:
    proc = run_captured_split(['git', *args], cwd=root, timeout=GIT_PROBE_TIMEOUT_SECONDS)
    value = (proc.stdout or '').strip()
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, ['git', *args], output=proc.stdout, stderr=proc.stderr)
    return value


def _candidate_identity(root: Path) -> tuple[str | None, list[str], str, bool]:
    try:
        sha = git('rev-parse', 'HEAD', root=root)
        tags = [x for x in git('tag', '--points-at', 'HEAD', root=root).splitlines() if x]
        if len(sha) == 40:
            return sha, tags, 'GIT_HEAD', True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    package = verify_source_package_identity(root, verify_all_files=True, verify_inventory=True)
    if package.get('verified') and package.get('git_commit_sha'):
        return package['git_commit_sha'], [], 'PACKAGE_MANIFEST', True
    return None, [], 'UNAVAILABLE', False


def build_handoff(root: Path = ROOT) -> dict:
    sha, tags, identity_mode, identity_verified = _candidate_identity(root)
    immutable = [x for x in tags if x.startswith('v') and '-phase' in x]
    release = {}
    p = root / 'RELEASE_MANIFEST.json'
    if p.is_file():
        try:
            release = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            release = {}
    source_locks = verify_source_locks(root)
    return {
        'schema_version': '1.2',
        'classification': 'ACCEPTANCE_HANDOFF_NOT_ACCEPTANCE_EVIDENCE',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'candidate_git_sha': sha,
        'candidate_identity_mode': identity_mode,
        'candidate_source_identity_verified': identity_verified,
        'candidate_tags': tags,
        'immutable_candidate_tag_present': bool(immutable),
        'workflow': WORKFLOW,
        'trigger': 'workflow_dispatch',
        'required_runner_labels': ['self-hosted', 'production-acceptance'],
        'protected_environment': 'production-acceptance',
        'required_secrets': REQUIRED_SECRETS,
        'required_environment_vars': REQUIRED_ENVIRONMENT_VARS,
        'required_source_files': ['uv.lock', 'frontend/package-lock.json'],
        'source_file_presence': {
            'uv.lock': (root / 'uv.lock').is_file(),
            'frontend/package-lock.json': (root / 'frontend/package-lock.json').is_file(),
        },
        'source_lock_compliance': {
            'verified': source_locks['verified'],
            'problems': source_locks['problems'],
            'locks': source_locks['locks'],
        },
        'release_status': {
            'prod_live_status': release.get('prod_live_status', 'BLOCKED'),
            'default_mode': release.get('default_mode', 'PAPER'),
            'live_enabled': release.get('live_enabled', False),
        },
        'operator_rules': [
            'Use an immutable tag or exact SHA; packaged-source identity may prove the SHA but not tag presence.',
            'Review and commit resolved dependency locks before production acceptance.',
            'Use protected secrets only on the self-hosted production-acceptance runner.',
            'Do not treat this handoff document as acceptance evidence.',
            'Return evidence through the staged promotion transaction; crash recovery and the import replay ledger must be healthy before another promotion.',
            'Do not enable LIVE unless the canonical release gate independently becomes eligible and human approval is recorded.',
        ],
    }


def main() -> int:
    payload = build_handoff()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
