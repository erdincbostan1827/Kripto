from __future__ import annotations

import re
import subprocess
from pathlib import Path

import scripts.lock_promotion_manifest as lock_manifest
import scripts.verify_acceptance_contract_parity as parity


def _repo(root: Path) -> str:
    subprocess.run(['git','init','-q'], cwd=root, check=True)
    subprocess.run(['git','config','user.email','t@example.invalid'], cwd=root, check=True)
    subprocess.run(['git','config','user.name','T'], cwd=root, check=True)
    (root/'seed').write_text('x')
    subprocess.run(['git','add','.'], cwd=root, check=True)
    subprocess.run(['git','commit','-q','-m','seed'], cwd=root, check=True)
    return subprocess.check_output(['git','rev-parse','HEAD'], cwd=root, text=True).strip()


def test_acceptance_contract_parity_current_repo_is_verified():
    result = parity.verify()
    assert result['verified'], result['problems']
    assert len(result['workflow_secrets']) == 14
    assert result['workflow_environment_vars'] == ['ACCEPTANCE_ENVIRONMENT_ID', 'ACCEPTANCE_TOPOLOGY_HASH']


def test_contract_parser_detects_missing_preflight_env():
    workflow = 'x: ${{ secrets.TEST_SECRET }}\ny: ${{ vars.TEST_VAR }}\n'
    secrets, variables = parity._workflow_contract(workflow)
    preflight = '_env("TEST_SECRET")\n'
    envs = set(re.findall(r'_env\("([A-Z0-9_]+)"\)', preflight))
    assert secrets == {'TEST_SECRET'}
    assert variables == {'TEST_VAR'}
    assert (secrets | variables) - envs == {'TEST_VAR'}


def test_lock_promotion_manifest_binds_source_and_lock_hashes(tmp_path: Path, monkeypatch):
    sha = _repo(tmp_path)
    (tmp_path/'frontend').mkdir()
    (tmp_path/'pyproject.toml').write_text('[project]\nname="x"\nversion="0"\n')
    (tmp_path/'frontend/package.json').write_text('{"name":"x","private":true}\n')
    (tmp_path/'uv.lock').write_text('backend-lock')
    (tmp_path/'frontend/package-lock.json').write_text('frontend-lock')
    monkeypatch.setattr(lock_manifest, 'cmd_version', lambda command, root: command[0] + '-version')
    out = tmp_path/'reports/lock-promotion/LOCK_PROMOTION_MANIFEST.json'
    lock_manifest.create(tmp_path, out)
    result = lock_manifest.verify(out, root=tmp_path, expected_source_sha=sha)
    assert result['verified'], result['problems']


def test_lock_promotion_manifest_rejects_tampered_lock(tmp_path: Path, monkeypatch):
    sha = _repo(tmp_path)
    (tmp_path/'frontend').mkdir()
    (tmp_path/'pyproject.toml').write_text('[project]\nname="x"\nversion="0"\n')
    (tmp_path/'frontend/package.json').write_text('{"name":"x","private":true}\n')
    (tmp_path/'uv.lock').write_text('backend-lock')
    (tmp_path/'frontend/package-lock.json').write_text('frontend-lock')
    monkeypatch.setattr(lock_manifest, 'cmd_version', lambda command, root: command[0] + '-version')
    out = tmp_path/'reports/lock-promotion/LOCK_PROMOTION_MANIFEST.json'
    lock_manifest.create(tmp_path, out)
    (tmp_path/'uv.lock').write_text('tampered')
    result = lock_manifest.verify(out, root=tmp_path, expected_source_sha=sha)
    assert not result['verified']
    assert 'LOCK_PROMOTION_LOCK_HASH_MISMATCH:uv.lock' in result['problems']


def test_lock_promotion_workflow_requires_manifest_verification():
    root = Path(__file__).resolve().parents[2]
    text = (root/'.github/workflows/lock-promotion.yml').read_text()
    assert 'python scripts/lock_promotion_manifest.py create' in text
    assert 'python scripts/lock_promotion_manifest.py verify --expected-source-sha' in text


def test_production_workflow_requires_contract_parity():
    root = Path(__file__).resolve().parents[2]
    text = (root/'.github/workflows/production-acceptance.yml').read_text()
    assert 'python scripts/verify_acceptance_contract_parity.py' in text
