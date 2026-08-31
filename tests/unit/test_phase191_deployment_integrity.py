from __future__ import annotations
import json, sys, time
from pathlib import Path
import pytest
import scripts.operation_lock as oplock
import scripts.transactional_release_update as update
import scripts.deployment_transaction_state as dstate
import scripts.deployment_audit_chain as audit
import scripts.trusted_signing_adapter as signing


def _tree(root:Path, marker:str)->Path:
    root.mkdir(parents=True); (root/'marker.txt').write_text(marker); return root

def _fixture(tmp_path:Path):
    rollback=_tree(tmp_path/(update.BACKUP_PREFIX+'x'),'old'); active=_tree(tmp_path/'active','new')
    pre=update._tree_sha256(rollback)
    acceptance=update._write_acceptance_receipt(parent=tmp_path,token='x',pre_tree_sha256=pre,post_tree_sha256=update._tree_sha256(active),post_identity={'git_commit_sha':'f'*40},binding={'migration_version':'m1','architecture_profile_hash':'a'*64},migration_receipt_verification=None)
    receipt=update._write_rollback_receipt(backup=rollback,pre_hash=pre,post_identity={'git_commit_sha':'f'*40},binding={'migration_version':'m1'},acceptance_receipt=acceptance)
    return active,rollback,acceptance,receipt

def test_lock_assert_healthy_detects_token_tamper(tmp_path:Path):
    with pytest.raises(RuntimeError,match='OWNERSHIP_LOST|HEARTBEAT_FAILED'):
        with oplock.operation_lock(tmp_path,operation='tamper',heartbeat_interval_seconds=.05) as held:
            path=tmp_path/oplock.LOCK_NAME; body=json.loads(path.read_text()); body['token']='attacker'; path.write_text(json.dumps(body))
            time.sleep(.08); held['assert_healthy']()

def test_rollback_emits_acceptance_receipt_and_audit_chain(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    active,rollback,acceptance,receipt=_fixture(tmp_path)
    monkeypatch.setattr(update,'run_post_cutover_acceptance',lambda *a,**k:{'accepted':True,'problems':[],'runtime_command':{'returncode':0}})
    result=update.rollback_last_update(active=active,rollback_dir=rollback,rollback_acceptance_command=[sys.executable,'-c','raise SystemExit(0)'])
    rr=Path(result['rollback_acceptance_receipt']); assert rr.is_file()
    body=json.loads(rr.read_text()); assert body['classification']=='VERIFIED_RELEASE_ROLLBACK_ACCEPTANCE_RECEIPT'
    assert body['active_tree_sha256']==update._tree_sha256(active)
    verified=audit.verify(tmp_path); assert verified['verified'] and verified['event_count']==1 and verified['head_sha256']==result['deployment_audit_event_sha256']

def test_audit_chain_detects_tamper(tmp_path:Path):
    audit.append_event(tmp_path,event_type='A',subjects={'x':1}); audit.append_event(tmp_path,event_type='B',subjects={'x':2})
    path=tmp_path/audit.AUDIT; lines=path.read_text().splitlines(); first=json.loads(lines[0]); first['subjects']['x']=9; lines[0]=json.dumps(first); path.write_text('\n'.join(lines)+'\n')
    assert audit.verify(tmp_path)['verified'] is False

def test_deployment_state_rejects_multiple_mutation_journals(tmp_path:Path):
    (tmp_path/'.release-update.transaction.json').write_text(json.dumps({'classification':'RELEASE_UPDATE_TRANSACTION','status':'PREPARED'}))
    (tmp_path/'.database-migration.transaction.json').write_text(json.dumps({'classification':'DATABASE_MIGRATION_TRANSACTION','status':'PREPARED'}))
    result=dstate.inspect(tmp_path); assert not result['safe_to_start_new_mutation']; assert any('MULTIPLE_MUTATION_JOURNALS' in x for x in result['problems'])

def test_deployment_state_clean_root_is_safe(tmp_path:Path):
    result=dstate.inspect(tmp_path); assert result['safe_to_start_new_mutation'] and not result['active'] and not result['problems']

def test_signing_adapter_only_prepares_external_trust_request(tmp_path:Path):
    subject=tmp_path/'attestation.json'; subject.write_text(json.dumps({'classification':'SIGNABLE_RELEASE_ACCEPTANCE_ATTESTATION','canonical_payload_sha256':'a'*64}))
    req=tmp_path/'request.json'; body=signing.build_request(subject=subject,output=req)
    assert body['signature_status']=='UNSIGNED' and body['algorithm']=='EXTERNAL_TRUST_PROVIDER_REQUIRED'
    sig=tmp_path/'sig.bin'; sig.write_bytes(b'x'*64); env=tmp_path/'envelope.json'; attached=signing.attach_external_signature(request=req,signature_file=sig,signing_identity='ci-key://example',output=env)
    assert attached['signature_status']=='SIGNED_EXTERNAL_UNVERIFIED'
    assert attached['classification']=='TRUSTED_SIGNING_ENVELOPE'
