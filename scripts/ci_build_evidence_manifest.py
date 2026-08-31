from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'CI_BUILD_EVIDENCE_MANIFEST.json'
INPUTS = (
    'uv.lock',
    'frontend/package-lock.json',
    'frontend/dist',
    'reports/local_acceptance',
    'reports/external_acceptance/sbom.cdx.json',
    'reports/external_acceptance/dependency_licenses.json',
    'reports/external_acceptance/supply_chain_artifact_verification.json',
    'reports/external_acceptance/scanner_image_digests.json',
    'reports/external_acceptance/provenance.json',
    'reports/CI_SCANNER_VERSIONS.txt',
    'reports/CI_TOOLCHAIN_RECEIPT.json',
    'reports/CI_CONTAINER_REPODIGEST.txt',
    'reports/ACCEPTANCE_REF_VALIDATION.json',
    'RELEASE_MANIFEST.json',
    'reports/PROJECT_STATUS.json',
    'reports/RELEASE_CONSISTENCY.json',
    'reports/PRODUCTION_READINESS_DOSSIER.json',
    'reports/EXTERNAL_EXECUTION_PLAN_VERIFICATION.json',
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _git_sha(root: Path) -> str:
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()


def _files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in INPUTS:
        target = root / rel
        if target.is_file():
            files.append(target)
        elif target.is_dir():
            files.extend(p for p in target.rglob('*') if p.is_file())
        else:
            raise FileNotFoundError(rel)
    return sorted(set(files), key=lambda p: p.relative_to(root).as_posix())


def create(root: Path = ROOT, output: Path | None = None) -> dict:
    out = output or (root / 'reports' / 'CI_BUILD_EVIDENCE_MANIFEST.json')
    entries = [
        {
            'path': p.relative_to(root).as_posix(),
            'sha256': sha256_file(p),
            'size': p.stat().st_size,
        }
        for p in _files(root)
        if p.resolve() != out.resolve()
    ]
    payload = {
        'schema_version': '1.1',
        'classification': 'CI_BUILD_EVIDENCE_TRANSFER_MANIFEST',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'git_commit_sha': _git_sha(root),
        'ci_context': {
            'repository': os.getenv('GITHUB_REPOSITORY') or None,
            'run_id': os.getenv('GITHUB_RUN_ID') or None,
            'run_attempt': os.getenv('GITHUB_RUN_ATTEMPT') or None,
            'workflow_ref': os.getenv('GITHUB_WORKFLOW_REF') or None,
        },
        'entries': entries,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return payload


def verify(path: Path = OUT, *, root: Path = ROOT, expected_git_sha: str | None = None, expected_repository: str | None = None, expected_run_id: str | None = None, expected_run_attempt: str | None = None, expected_workflow_ref: str | None = None) -> dict:
    problems: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return {'verified': False, 'problems': [f'CI_BUILD_EVIDENCE_MANIFEST_INVALID:{type(exc).__name__}']}
    if payload.get('schema_version') != '1.1':
        problems.append('CI_BUILD_EVIDENCE_SCHEMA_UNSUPPORTED')
    if payload.get('classification') != 'CI_BUILD_EVIDENCE_TRANSFER_MANIFEST':
        problems.append('CI_BUILD_EVIDENCE_CLASSIFICATION_INVALID')
    actual_git = _git_sha(root)
    declared_git = payload.get('git_commit_sha')
    if declared_git != actual_git:
        problems.append('CI_BUILD_EVIDENCE_GIT_MISMATCH')
    if expected_git_sha and declared_git != expected_git_sha:
        problems.append('CI_BUILD_EVIDENCE_EXPECTED_GIT_MISMATCH')
    context = payload.get('ci_context') if isinstance(payload.get('ci_context'), dict) else {}
    expected_context = {
        'repository': expected_repository,
        'run_id': expected_run_id,
        'run_attempt': expected_run_attempt,
        'workflow_ref': expected_workflow_ref,
    }
    for key, expected in expected_context.items():
        if expected is not None and context.get(key) != expected:
            problems.append(f'CI_BUILD_EVIDENCE_CONTEXT_MISMATCH:{key}')
    entries = payload.get('entries')
    if not isinstance(entries, list) or not entries:
        problems.append('CI_BUILD_EVIDENCE_ENTRIES_MISSING')
        entries = []
    seen: set[str] = set()
    root_resolved = root.resolve()
    manifest_rel = None
    try:
        manifest_rel = path.resolve().relative_to(root_resolved).as_posix()
    except ValueError:
        problems.append('CI_BUILD_EVIDENCE_MANIFEST_OUTSIDE_ROOT')
    expected_paths: set[str] = set()
    try:
        expected_paths = {
            p.relative_to(root).as_posix()
            for p in _files(root)
            if p.resolve() != path.resolve()
        }
    except Exception as exc:
        problems.append(f'CI_BUILD_EVIDENCE_EXPECTED_INPUTS_INVALID:{type(exc).__name__}')
    for row in entries:
        if not isinstance(row, dict):
            problems.append('CI_BUILD_EVIDENCE_ENTRY_INVALID')
            continue
        rel = row.get('path')
        if not isinstance(rel, str) or not rel or rel in seen:
            problems.append('CI_BUILD_EVIDENCE_PATH_INVALID_OR_DUPLICATE')
            continue
        seen.add(rel)
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            problems.append(f'CI_BUILD_EVIDENCE_PATH_ESCAPE:{rel}')
            continue
        if not candidate.is_file():
            problems.append(f'CI_BUILD_EVIDENCE_FILE_MISSING:{rel}')
            continue
        if sha256_file(candidate) != row.get('sha256'):
            problems.append(f'CI_BUILD_EVIDENCE_HASH_MISMATCH:{rel}')
        if candidate.stat().st_size != row.get('size'):
            problems.append(f'CI_BUILD_EVIDENCE_SIZE_MISMATCH:{rel}')
    declared_paths = seen
    for rel in sorted(expected_paths - declared_paths):
        problems.append(f'CI_BUILD_EVIDENCE_REQUIRED_ENTRY_MISSING:{rel}')
    for rel in sorted(declared_paths - expected_paths):
        problems.append(f'CI_BUILD_EVIDENCE_UNEXPECTED_ENTRY:{rel}')
    return {
        'verified': not problems,
        'problems': problems,
        'git_commit_sha': declared_git,
        'entry_count': len(entries),
        'manifest_sha256': sha256_file(path) if path.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('create', 'verify'))
    parser.add_argument('--expected-git-sha')
    parser.add_argument('--expected-repository')
    parser.add_argument('--expected-run-id')
    parser.add_argument('--expected-run-attempt')
    parser.add_argument('--expected-workflow-ref')
    args = parser.parse_args()
    try:
        result = create() if args.mode == 'create' else verify(expected_git_sha=args.expected_git_sha, expected_repository=args.expected_repository, expected_run_id=args.expected_run_id, expected_run_attempt=args.expected_run_attempt, expected_workflow_ref=args.expected_workflow_ref)
    except Exception as exc:
        print(json.dumps({'verified': False, 'problems': [f'{type(exc).__name__}:{exc}']}, sort_keys=True))
        return 2
    if args.mode == 'create':
        print(json.dumps({'created': True, 'entries': len(result['entries']), 'git_commit_sha': result['git_commit_sha']}, sort_keys=True))
        return 0
    print(json.dumps(result, sort_keys=True))
    return 0 if result['verified'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
