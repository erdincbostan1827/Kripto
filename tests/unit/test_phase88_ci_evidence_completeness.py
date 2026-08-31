from __future__ import annotations

import json
from pathlib import Path

import scripts.ci_build_evidence_manifest as mod
from tests.unit.test_phase84_ci_build_evidence_transfer import _inputs, _repo


def test_transfer_manifest_rejects_omitted_required_file(tmp_path: Path):
    sha = _repo(tmp_path)
    _inputs(tmp_path)
    out = tmp_path / 'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    mod.create(tmp_path, out)
    payload = json.loads(out.read_text())
    removed = payload['entries'].pop(0)['path']
    out.write_text(json.dumps(payload))
    result = mod.verify(out, root=tmp_path, expected_git_sha=sha)
    assert not result['verified']
    assert f'CI_BUILD_EVIDENCE_REQUIRED_ENTRY_MISSING:{removed}' in result['problems']


def test_transfer_manifest_rejects_unexpected_in_root_entry(tmp_path: Path):
    sha = _repo(tmp_path)
    _inputs(tmp_path)
    out = tmp_path / 'reports/CI_BUILD_EVIDENCE_MANIFEST.json'
    mod.create(tmp_path, out)
    extra = tmp_path / 'unexpected.txt'
    extra.write_text('unexpected')
    payload = json.loads(out.read_text())
    payload['entries'].append({
        'path': 'unexpected.txt',
        'sha256': mod.sha256_file(extra),
        'size': extra.stat().st_size,
    })
    out.write_text(json.dumps(payload))
    result = mod.verify(out, root=tmp_path, expected_git_sha=sha)
    assert not result['verified']
    assert 'CI_BUILD_EVIDENCE_UNEXPECTED_ENTRY:unexpected.txt' in result['problems']
