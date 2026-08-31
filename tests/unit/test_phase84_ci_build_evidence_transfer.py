from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.ci_build_evidence_manifest as mod


def _repo(root: Path) -> str:
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    subprocess.run(['git', 'config', 'user.email', 't@example.invalid'], cwd=root, check=True)
    subprocess.run(['git', 'config', 'user.name', 'T'], cwd=root, check=True)
    (root / 'seed').write_text('x')
    subprocess.run(['git', 'add', 'seed'], cwd=root, check=True)
    subprocess.run(['git', 'commit', '-q', '-m', 'seed'], cwd=root, check=True)
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()


def _inputs(root: Path) -> None:
    for rel in mod.INPUTS:
        p = root / rel
        if rel in {'frontend/dist', 'reports/local_acceptance'}:
            p.mkdir(parents=True, exist_ok=True)
            (p / 'x.txt').write_text(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(rel)


def test_transfer_manifest_binds_every_file_and_git_sha(tmp_path: Path):
    sha = _repo(tmp_path)
    _inputs(tmp_path)
    out = tmp_path / 'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    payload = mod.create(tmp_path, out)
    assert payload['git_commit_sha'] == sha
    result = mod.verify(out, root=tmp_path, expected_git_sha=sha)
    assert result['verified'] and result['entry_count'] >= len(mod.INPUTS)


def test_transfer_manifest_fails_on_tampered_file(tmp_path: Path):
    sha = _repo(tmp_path)
    _inputs(tmp_path)
    out = tmp_path / 'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    mod.create(tmp_path, out)
    (tmp_path / 'reports/PROJECT_STATUS.json').write_text('tampered')
    result = mod.verify(out, root=tmp_path, expected_git_sha=sha)
    assert not result['verified']
    assert 'CI_BUILD_EVIDENCE_HASH_MISMATCH:reports/PROJECT_STATUS.json' in result['problems']


def test_transfer_manifest_fails_on_wrong_expected_git(tmp_path: Path):
    _repo(tmp_path)
    _inputs(tmp_path)
    out = tmp_path / 'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    mod.create(tmp_path, out)
    result = mod.verify(out, root=tmp_path, expected_git_sha='0' * 40)
    assert not result['verified']
    assert 'CI_BUILD_EVIDENCE_EXPECTED_GIT_MISMATCH' in result['problems']


def test_transfer_manifest_rejects_path_escape(tmp_path: Path):
    sha = _repo(tmp_path)
    _inputs(tmp_path)
    out = tmp_path / 'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    mod.create(tmp_path, out)
    payload = json.loads(out.read_text())
    payload['entries'].append({'path': '../outside', 'sha256': 'a' * 64, 'size': 1})
    out.write_text(json.dumps(payload))
    result = mod.verify(out, root=tmp_path, expected_git_sha=sha)
    assert not result['verified']
    assert 'CI_BUILD_EVIDENCE_PATH_ESCAPE:../outside' in result['problems']
