from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
import scripts.trusted_signing_adapter as signing
import scripts.write_restore_drill_receipt as restore_receipt
import scripts.deployment_audit_chain as audit
import scripts.deployment_recovery_coordinator as recovery
import scripts.transactional_release_update as update
import scripts.database_migration_guard as migration


def _signed(tmp_path:Path):
    subject=tmp_path/'subject.json'; subject.write_text(json.dumps({'classification':'SIGNABLE_RELEASE_ACCEPTANCE_ATTESTATION','canonical_payload_sha256':'a'*64}))
    req=tmp_path/'request.json'; signing.build_request(subject=subject,output=req)
    sig=tmp_path/'sig.bin'; sig.write_bytes(b'z'*64)
    env=tmp_path/'env.json'; signing.attach_external_signature(request=req,signature_file=sig,signing_identity='ci-key://phase193',output=env)
    return env


def _verifier(tmp_path:Path, *, mutate:str|None=None, expired:bool=False):
    p=tmp_path/f'verifier-{mutate}-{expired}.py'
    mutation=f"o[{mutate!r}]='wrong'" if mutate else ''
    expiry="(datetime.now(timezone.utc)-timedelta(seconds=60)).isoformat()" if expired else "e['expires_at']"
    p.write_text(f"""import json,sys,hashlib\nfrom datetime import datetime,timezone,timedelta\ne=json.load(open(sys.argv[1])); raw=open(sys.argv[1],'rb').read()\no={{'verified':True,'subject_sha256':e['subject_sha256'],'canonical_payload_sha256':e['canonical_payload_sha256'],'signing_identity':e['signing_identity'],'nonce':e['nonce'],'envelope_sha256':hashlib.sha256(raw).hexdigest(),'verifier_identity':'trusted://phase193','issued_at':e['issued_at'],'expires_at':{expiry}}}\n{mutation}\nprint(json.dumps(o))\n""")
    return p


def test_trusted_verifier_nonce_expiry_and_replay_are_fail_closed(tmp_path:Path):
    env=_signed(tmp_path); verifier=_verifier(tmp_path); ledger=tmp_path/'ledger.jsonl'
    out=tmp_path/'receipt.json'
    result=signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(verifier)],verifier_identity='trusted://phase193',output=out,replay_ledger=ledger)
    assert result['trusted'] is True and result['nonce']==json.loads(env.read_text())['nonce']
    with pytest.raises(RuntimeError,match='REPLAY_DETECTED'):
        signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(verifier)],verifier_identity='trusted://phase193',output=tmp_path/'replay.json',replay_ledger=ledger)


def test_trusted_verifier_rejects_wrong_nonce_and_expired_verdict(tmp_path:Path):
    env=_signed(tmp_path)
    with pytest.raises(RuntimeError,match='NONCE_MISMATCH'):
        signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(_verifier(tmp_path,mutate='nonce'))],verifier_identity='trusted://phase193',output=tmp_path/'x.json')
    with pytest.raises(RuntimeError,match='EXPIRED_OR_NOT_YET_VALID|VALIDITY_WINDOW_INVALID'):
        signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(_verifier(tmp_path,expired=True))],verifier_identity='trusted://phase193',output=tmp_path/'y.json')


def _restore(path:Path, backup:Path):
    env='phase193-test'; now=datetime.now(timezone.utc).isoformat()
    body={'schema_version':'1.1','classification':'VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT','backup_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),'restore_status':'PASS','restored_table_count':7,'environment_id':env,'environment_fingerprint':restore_receipt.environment_fingerprint(env),'completed_at':now,'policy':'REAL_RESTORE_COMMAND_COMPLETED_AND_DATABASE_SMOKE_CHECK_PASSED; ENVIRONMENT_BOUND_AND_FRESHNESS_VERIFIABLE'}
    body['provenance_sha256']=restore_receipt.canonical(body); path.write_text(json.dumps(body,sort_keys=True)); return path


def test_restore_receipt_is_bound_into_deployment_audit_chain(tmp_path:Path):
    backup=tmp_path/'db.dump'; backup.write_bytes(b'database'); receipt=_restore(tmp_path/'restore.json',backup)
    event=restore_receipt.append_restore_receipt_to_audit(receipt=receipt,audit_root=tmp_path)
    assert event['event_type']=='DATABASE_RESTORE_DRILL_VERIFIED'
    assert event['subjects']['restore_drill_receipt_sha256']==hashlib.sha256(receipt.read_bytes()).hexdigest()
    assert audit.verify(tmp_path)['head_sha256']==event['event_sha256']


def test_restore_audit_append_refuses_tampered_existing_chain(tmp_path:Path):
    backup=tmp_path/'db.dump'; backup.write_bytes(b'database'); receipt=_restore(tmp_path/'restore.json',backup)
    audit.append_event(tmp_path,event_type='EARLIER',subjects={'ok':True})
    ap=tmp_path/audit.AUDIT; row=json.loads(ap.read_text()); row['subjects']['ok']=False; ap.write_text(json.dumps(row)+'\n')
    with pytest.raises(RuntimeError,match='CHAIN_TAMPERED'):
        restore_receipt.append_restore_receipt_to_audit(receipt=receipt,audit_root=tmp_path)


def _write_update_journal(root:Path, active:Path, backup:Path, candidate:Path):
    body={'schema_version':'1.0','classification':'RELEASE_UPDATE_TRANSACTION','transaction_id':'u1','status':'CUTOVER_COMPLETE','active_name':active.name,'backup':backup.name,'candidate':candidate.name}
    (root/update.JOURNAL).write_text(json.dumps(body))


def _write_migration_journal(root:Path):
    body={'schema_version':'1.0','classification':'DATABASE_MIGRATION_TRANSACTION','transaction_id':'m1','status':'PREPARED','from_head':'old','to_head':'new','active_tree_sha256':'a'*64,'candidate_tree_sha256':'b'*64,'compatibility_contract_sha256':'c'*64,'database_backup_receipt_sha256':'d'*64,'pending_revisions':['new']}
    (root/migration.JOURNAL).write_text(json.dumps(body))


def test_cross_transaction_recovery_recovers_only_when_database_not_advanced(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    active=tmp_path/'active'; active.mkdir(); (active/'marker').write_text('new')
    backup=tmp_path/(update.BACKUP_PREFIX+'u1'); backup.mkdir(); (backup/'marker').write_text('old')
    candidate=tmp_path/(update.CANDIDATE_PREFIX+'u1'); candidate.mkdir()
    _write_update_journal(tmp_path,active,backup,candidate); _write_migration_journal(tmp_path)
    monkeypatch.setattr(migration,'probe_database_head',lambda *a,**k:'old')
    result=recovery.recover_cross_transaction(active=active,state_dir=tmp_path,probe_command=['probe'],cwd=tmp_path)
    assert result['status']=='RECOVERED_PRE_MIGRATION_UPDATE' and result['safe_to_continue'] is True
    assert (active/'marker').read_text()=='old'


def test_cross_transaction_recovery_blocks_if_database_already_advanced(tmp_path:Path,monkeypatch:pytest.MonkeyPatch):
    active=tmp_path/'active'; active.mkdir(); (active/'marker').write_text('new')
    backup=tmp_path/(update.BACKUP_PREFIX+'u1'); backup.mkdir(); candidate=tmp_path/(update.CANDIDATE_PREFIX+'u1'); candidate.mkdir()
    _write_update_journal(tmp_path,active,backup,candidate); _write_migration_journal(tmp_path)
    monkeypatch.setattr(migration,'probe_database_head',lambda *a,**k:'new')
    result=recovery.recover_cross_transaction(active=active,state_dir=tmp_path,probe_command=['probe'],cwd=tmp_path)
    assert result['status']=='BLOCKED_DATABASE_ADVANCED_APPLICATION_UNCOMMITTED' and result['safe_to_continue'] is False
    assert (tmp_path/update.JOURNAL).exists() and (tmp_path/migration.JOURNAL).exists()
