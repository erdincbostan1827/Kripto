from __future__ import annotations

import json
from pathlib import Path

import scripts.external_acceptance_runner as runner
import scripts.verify_external_acceptance as verifier


def test_real_runner_requires_external_challenge_trust(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'REPORTS', tmp_path / 'reports' / 'external_acceptance')
    seen = {}
    def fake_verify(path, *, root, max_age_hours=24, require_trust=None):
        seen['require_trust'] = require_trust
        return {'verified': False, 'problems': ['CHALLENGE_TRUST_VERIFIER_MISSING']}
    monkeypatch.setattr(runner, 'verify_challenge', fake_verify)
    result = runner.execute('runtime', confirm_real=True, timeout=1)
    assert seen['require_trust'] is True
    assert result['selected_all_pass'] is False
    assert result['blocker'] == 'RELEASE_CHALLENGE_NOT_VERIFIED'


def test_simulation_does_not_claim_external_trust(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, 'REPORTS', tmp_path / 'reports' / 'external_acceptance')
    seen = {}
    def fake_verify(path, *, root, max_age_hours=24, require_trust=None):
        seen['require_trust'] = require_trust
        return {'verified': False, 'problems': ['NOT_REQUIRED_FOR_SIMULATION']}
    monkeypatch.setattr(runner, 'verify_challenge', fake_verify)
    runner.execute('runtime', confirm_real=False, timeout=1)
    assert seen['require_trust'] is False


def test_pass_manifest_reverification_forces_trust(monkeypatch, tmp_path: Path) -> None:
    reports = tmp_path / 'reports' / 'external_acceptance'
    reports.mkdir(parents=True)
    manifest = reports / 'manifest_runtime.json'
    artifact = reports / 'runtime.log'
    artifact.write_text('ok\n')
    import hashlib
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    payload = {
        'schema_version':'3.2','classification':'EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE',
        'real_target_explicitly_confirmed':True,'profile':'runtime',
        'command_contract_sha256': verifier.command_contract_sha256('runtime'),
        'challenge':{'challenge_id':'x','sha256':'y'},
        'environment':{'git_commit_sha':None,'acceptance_environment_id_hash':'a'*64,'topology_hash':'b'*64},
        'generated_at':'2026-08-30T10:00:00+00:00',
        'groups':{'runtime':'PASS'},'selected_all_pass':True,
        'evidence':[]
    }
    manifest.write_text(json.dumps(payload))
    seen={}
    def fake_verify(path, *, root, max_age_hours=24, require_trust=None):
        seen['require_trust']=require_trust
        return {'verified':False,'problems':['CHALLENGE_TRUST_VERIFIER_MISSING'],'challenge_id':'x','sha256':'y'}
    monkeypatch.setattr(verifier, 'verify_challenge', fake_verify)
    result=verifier.verify_manifest(manifest, root=tmp_path)
    assert seen['require_trust'] is True
    assert 'CURRENT_RELEASE_CHALLENGE_NOT_VERIFIED' in result['problems']
