from __future__ import annotations
import json
from pathlib import Path
import scripts.release_acceptance_attestation as att


def test_attestation_is_signable_but_not_falsely_trusted(tmp_path: Path):
    acceptance=tmp_path/'acceptance.json'; provenance=tmp_path/'provenance.json'; out=tmp_path/'attestation.json'
    acceptance.write_text(json.dumps({"classification":"VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT","post_update_git_commit_sha":"a"*40}))
    provenance.write_text(json.dumps({"git_commit_sha":"a"*40,"classification":"PACKAGE_PROVENANCE"}))
    created=att.create(acceptance=acceptance,package_provenance=provenance,output=out)
    assert created['signature_status']=='UNSIGNED'
    verified=att.verify(out)
    assert verified['verified_structure'] is True
    assert verified['trusted_provenance'] is False
    assert 'TRUSTED_SIGNATURE_NOT_PRESENT' in verified['problems']


def test_attestation_rejects_cross_release_provenance(tmp_path: Path):
    acceptance=tmp_path/'acceptance.json'; provenance=tmp_path/'provenance.json'; out=tmp_path/'attestation.json'
    acceptance.write_text(json.dumps({"classification":"VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT","post_update_git_commit_sha":"a"*40}))
    provenance.write_text(json.dumps({"git_commit_sha":"b"*40}))
    try:
        att.create(acceptance=acceptance,package_provenance=provenance,output=out)
    except RuntimeError as exc:
        assert 'GIT_IDENTITY_MISMATCH' in str(exc)
    else:
        raise AssertionError('expected mismatch')


def test_attestation_tamper_breaks_canonical_digest(tmp_path: Path):
    acceptance=tmp_path/'acceptance.json'; provenance=tmp_path/'provenance.json'; out=tmp_path/'attestation.json'
    acceptance.write_text(json.dumps({"classification":"VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT","post_update_git_commit_sha":"a"*40}))
    provenance.write_text(json.dumps({"git_commit_sha":"a"*40}))
    att.create(acceptance=acceptance,package_provenance=provenance,output=out)
    payload=json.loads(out.read_text()); payload['git_commit_sha']='evil'; out.write_text(json.dumps(payload))
    verified=att.verify(out)
    assert verified['verified_structure'] is False
    assert 'CANONICAL_DIGEST_MISMATCH' in verified['problems']
