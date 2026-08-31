from __future__ import annotations
import hashlib, json
from pathlib import Path
import scripts.verify_local_acceptance as verifier
from scripts.release_gate import evaluate_release_gate


def _sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def _valid_tree(root:Path, monkeypatch):
    (root/'reports/local_acceptance').mkdir(parents=True)
    log=root/'reports/local_acceptance/shard.log'; log.write_text('ok\n')
    shard=root/'reports/local_acceptance/shard.json'
    shard.write_text(json.dumps({'git_commit_sha':'abc','status':'PASS','exit_code':0,'log':'reports/local_acceptance/shard.log','log_sha256':_sha(log),'selected_files':['tests/a.py']}))
    full=root/'reports/local_acceptance/full_regression_manifest.json'
    full.write_text(json.dumps({'classification':'LOCAL_FULL_REGRESSION_EVIDENCE','git_commit_sha':'abc','status':'PASS','problems':[],'test_file_count':1,'shard_count':1,'shards':[{'manifest':'reports/local_acceptance/shard.json','manifest_sha256':_sha(shard)}]}))
    monkeypatch.setattr(verifier,'_git_sha',lambda _root:'abc')
    return full,log,shard


def test_local_test_evidence_requires_git_bound_shard_and_log_hashes(tmp_path:Path,monkeypatch):
    full,log,shard=_valid_tree(tmp_path,monkeypatch)
    r=verifier.verify_local_acceptance(full,root=tmp_path)
    assert r['verified'] is True and r['status']=='PASS'
    log.write_text('tampered\n')
    r=verifier.verify_local_acceptance(full,root=tmp_path)
    assert r['verified'] is False and any('SHARD_LOG_HASH_INVALID' in p for p in r['problems'])


def test_local_test_evidence_rejects_stale_git(tmp_path:Path,monkeypatch):
    full,_,_=_valid_tree(tmp_path,monkeypatch)
    monkeypatch.setattr(verifier,'_git_sha',lambda _root:'different')
    r=verifier.verify_local_acceptance(full,root=tmp_path)
    assert r['verified'] is False and 'GIT_COMMIT_MISMATCH' in r['problems']


def test_release_gate_blocks_when_local_full_regression_not_verified(tmp_path:Path):
    import yaml
    (tmp_path/'requirements_acceptance_matrix.yaml').write_text(yaml.safe_dump({'requirements':[{'id':'x','priority':'P0','status':'PASS'}]}))
    (tmp_path/'RELEASE_MANIFEST.json').write_text(json.dumps({'test_evidence':{'status':'BLOCKED','verified':False},'acceptance':{},'prod_live_status':'BLOCKED','live_enabled':False,'default_mode':'PAPER'}))
    blockers=evaluate_release_gate(tmp_path)
    assert any('local full regression evidence not PASS/verified' in b for b in blockers)
