from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import pytest
import scripts.deployment_audit_chain as audit
import scripts.trusted_signing_adapter as signing
import scripts.release_provenance_graph as graph
import scripts.transactional_release_update as update
import scripts.database_migration_guard as guard


def _write(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True)); return path


def test_audit_chain_covers_install_update_migration_and_rollback_events(tmp_path: Path):
    events=[
        ('INSTALL_ACCEPTED',{'health':'PASS'}),
        ('DATABASE_MIGRATION_COMMITTED',{'to_head':'m2'}),
        ('RELEASE_UPDATE_ACCEPTED',{'tree':'a'*64}),
        ('RELEASE_ROLLBACK_ACCEPTED',{'tree':'b'*64}),
    ]
    previous=None
    for kind,subjects in events:
        event=audit.append_event(tmp_path,event_type=kind,subjects=subjects)
        assert event['previous_event_sha256']==previous
        previous=event['event_sha256']
    verified=audit.verify(tmp_path)
    assert verified=={'verified':True,'event_count':4,'head_sha256':previous,'problems':[]}


def test_audit_append_refuses_any_earlier_chain_tamper(tmp_path: Path):
    audit.append_event(tmp_path,event_type='A',subjects={'x':1})
    audit.append_event(tmp_path,event_type='B',subjects={'x':2})
    p=tmp_path/audit.AUDIT
    lines=p.read_text().splitlines(); first=json.loads(lines[0]); first['subjects']['x']=9; lines[0]=json.dumps(first); p.write_text('\n'.join(lines)+'\n')
    with pytest.raises(RuntimeError,match='CHAIN_TAMPERED'):
        audit.append_event(tmp_path,event_type='C',subjects={})


def _signed_envelope(tmp_path: Path):
    subject=_write(tmp_path/'subject.json',{'classification':'SIGNABLE_RELEASE_ACCEPTANCE_ATTESTATION','canonical_payload_sha256':'a'*64})
    req=tmp_path/'request.json'; signing.build_request(subject=subject,output=req)
    sig=tmp_path/'sig.bin'; sig.write_bytes(b's'*64)
    env=tmp_path/'envelope.json'; signing.attach_external_signature(request=req,signature_file=sig,signing_identity='ci-key://phase192',output=env)
    return subject,req,env


def _verifier_script(tmp_path: Path, *, verified=True, mutate: str|None=None, rc: int=0) -> Path:
    p=tmp_path/f'verifier-{mutate or "ok"}-{rc}.py'
    code="""import json,sys,hashlib\ne=json.load(open(sys.argv[1])); raw=open(sys.argv[1],'rb').read()\no={'verified':VERIFIED,'subject_sha256':e['subject_sha256'],'canonical_payload_sha256':e['canonical_payload_sha256'],'signing_identity':e['signing_identity'],'nonce':e['nonce'],'envelope_sha256':hashlib.sha256(raw).hexdigest(),'verifier_identity':'sigstore://trusted-ci','issued_at':e['issued_at'],'expires_at':e['expires_at']}\nMUTATE\nprint(json.dumps(o))\nraise SystemExit(RC)\n"""
    mutation=""
    if mutate: mutation=f"o[{mutate!r}]='wrong'"
    p.write_text(code.replace('VERIFIED',repr(verified)).replace('MUTATE',mutation).replace('RC',str(rc)))
    return p


def test_external_verifier_contract_produces_trusted_receipt(tmp_path: Path):
    subject,req,env=_signed_envelope(tmp_path)
    verifier=_verifier_script(tmp_path)
    out=tmp_path/'verified.json'
    body=signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(verifier)],verifier_identity='sigstore://trusted-ci',output=out)
    assert body['trusted'] is True
    assert body['signature_status']=='VERIFIED_EXTERNAL_TRUST_PROVIDER'
    assert body['envelope_sha256']==hashlib.sha256(env.read_bytes()).hexdigest()
    assert len(body['verification_receipt_sha256'])==64 and out.is_file()


@pytest.mark.parametrize('mutate', ['subject_sha256','canonical_payload_sha256','signing_identity'])
def test_external_verifier_rejects_binding_mismatch(tmp_path: Path, mutate: str):
    _,_,env=_signed_envelope(tmp_path); verifier=_verifier_script(tmp_path,mutate=mutate)
    with pytest.raises(RuntimeError,match='MISMATCH'):
        signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(verifier)],verifier_identity='sigstore://trusted-ci',output=tmp_path/'x.json')


def test_external_verifier_rejects_negative_verdict_and_nonzero_exit(tmp_path: Path):
    _,_,env=_signed_envelope(tmp_path)
    with pytest.raises(RuntimeError,match='NOT_VERIFIED'):
        signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(_verifier_script(tmp_path,verified=False))],verifier_identity='sigstore://trusted-ci',output=tmp_path/'x.json')
    with pytest.raises(RuntimeError,match='VERIFIER_FAILED'):
        signing.verify_external_signature(envelope=env,verifier_command=[sys.executable,str(_verifier_script(tmp_path,rc=7))],verifier_identity='sigstore://trusted-ci',output=tmp_path/'y.json')


def test_provenance_graph_includes_rollback_acceptance(tmp_path: Path):
    acceptance=_write(tmp_path/'acceptance.json',{'classification':'VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT','post_update_git_commit_sha':'a'*40})
    acceptance_sha=hashlib.sha256(acceptance.read_bytes()).hexdigest()
    rollback=_write(tmp_path/'rollback.json',{'classification':'VERIFIED_RELEASE_ROLLBACK_RECEIPT','acceptance_receipt_sha256':acceptance_sha})
    rollback_sha=hashlib.sha256(rollback.read_bytes()).hexdigest()
    ra=_write(tmp_path/'rollback-acceptance.json',{'classification':'VERIFIED_RELEASE_ROLLBACK_ACCEPTANCE_RECEIPT','source_update_acceptance_receipt_sha256':acceptance_sha,'source_rollback_receipt_sha256':rollback_sha,'provenance_sha256':'r'*64})
    out=tmp_path/'graph.json'
    result=graph.build_graph(acceptance=acceptance,rollback=rollback,rollback_acceptance=ra,output=out)
    payload=json.loads(out.read_text())
    assert result['node_count']==3 and result['edge_count']==3
    assert payload['nodes']['rollback_acceptance']['sha256']==hashlib.sha256(ra.read_bytes()).hexdigest()


def test_provenance_graph_rejects_tampered_rollback_acceptance_link(tmp_path: Path):
    acceptance=_write(tmp_path/'acceptance.json',{'classification':'VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT','post_update_git_commit_sha':'a'*40})
    ash=hashlib.sha256(acceptance.read_bytes()).hexdigest()
    rollback=_write(tmp_path/'rollback.json',{'classification':'VERIFIED_RELEASE_ROLLBACK_RECEIPT','acceptance_receipt_sha256':ash})
    ra=_write(tmp_path/'ra.json',{'classification':'VERIFIED_RELEASE_ROLLBACK_ACCEPTANCE_RECEIPT','source_update_acceptance_receipt_sha256':ash,'source_rollback_receipt_sha256':'0'*64})
    with pytest.raises(RuntimeError,match='ROLLBACK_ACCEPTANCE_RECEIPT_HASH_MISMATCH'):
        graph.build_graph(acceptance=acceptance,rollback=rollback,rollback_acceptance=ra,output=tmp_path/'g.json')


def test_successful_update_emits_audit_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    active=tmp_path/'active'; active.mkdir(); (active/'marker.txt').write_text('old')
    package=tmp_path/'source.zip'; package.write_bytes(b'x')
    def fake_extract(package: Path,destination: Path,**kwargs):
        project=destination/'project'; project.mkdir(); (project/'marker.txt').write_text('new')
        return {'classification':'SOURCE_PACKAGE_SAFE_EXTRACTION'}
    monkeypatch.setattr(update,'extract',fake_extract)
    monkeypatch.setattr(update,'verify_source_package_identity',lambda root:{'verified':True,'problems':[],'git_commit_sha':'f'*40})
    monkeypatch.setattr(update,'run_post_cutover_acceptance',lambda root,**kwargs:{'accepted':True,'problems':[],'binding':{'accepted':True,'migration_version':None,'architecture_profile_hash':'a'*64}})
    monkeypatch.setattr('scripts.database_migration_guard.compare_release_migrations',lambda a,b:{'required':False,'from_head':None,'to_head':None})
    result=update.apply_update(package=package,active=active)
    assert result['deployment_audit_event_sha256']==audit.verify(tmp_path)['head_sha256']
    assert audit.verify(tmp_path)['event_count']==1


def test_installers_append_install_acceptance_only_after_health():
    sh=Path('install.sh').read_text(); ps=Path('INSTALL_WINDOWS.ps1').read_text()
    assert sh.index('api/v1/health') < sh.index('INSTALL_ACCEPTED')
    assert ps.index('api/v1/health') < ps.index('INSTALL_ACCEPTED')
