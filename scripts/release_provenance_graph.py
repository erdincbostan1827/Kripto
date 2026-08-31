from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path


def _sha(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"PROVENANCE_GRAPH_INPUT_UNSAFE:{path.name}")
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _load(path: Path) -> dict:
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: raise RuntimeError(f"PROVENANCE_GRAPH_JSON_INVALID:{path.name}:{type(exc).__name__}") from exc


def _canonical(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=f'.{path.name}.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(payload,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise


def build_graph(*, acceptance: Path, rollback: Path, output: Path, migration: Path|None=None, backup: Path|None=None, restore: Path|None=None, package_provenance: Path|None=None, rollback_acceptance: Path|None=None, signing_verification: Path|None=None) -> dict:
    a=_load(acceptance); r=_load(rollback)
    if a.get('classification')!='VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT': raise RuntimeError('PROVENANCE_GRAPH_ACCEPTANCE_CLASSIFICATION_INVALID')
    if r.get('classification')!='VERIFIED_RELEASE_ROLLBACK_RECEIPT': raise RuntimeError('PROVENANCE_GRAPH_ROLLBACK_CLASSIFICATION_INVALID')
    if r.get('acceptance_receipt_sha256') != _sha(acceptance): raise RuntimeError('PROVENANCE_GRAPH_ROLLBACK_ACCEPTANCE_HASH_MISMATCH')
    nodes={
      'release_acceptance': {'sha256':_sha(acceptance),'classification':a.get('classification')},
      'rollback': {'sha256':_sha(rollback),'classification':r.get('classification')},
    }
    edges=[{'from':'rollback','to':'release_acceptance','relation':'hash_binds'}]
    migration_sha=a.get('migration_receipt_sha256')
    if migration_sha:
        if migration is None: raise RuntimeError('PROVENANCE_GRAPH_MIGRATION_RECEIPT_REQUIRED')
        m=_load(migration)
        if m.get('classification')!='VERIFIED_DATABASE_MIGRATION_RECEIPT': raise RuntimeError('PROVENANCE_GRAPH_MIGRATION_CLASSIFICATION_INVALID')
        if _sha(migration)!=migration_sha: raise RuntimeError('PROVENANCE_GRAPH_ACCEPTANCE_MIGRATION_HASH_MISMATCH')
        nodes['database_migration']={'sha256':_sha(migration),'classification':m.get('classification'),'provenance_sha256':m.get('provenance_sha256')}
        edges.append({'from':'release_acceptance','to':'database_migration','relation':'hash_binds'})
        if backup is None or restore is None: raise RuntimeError('PROVENANCE_GRAPH_DATABASE_BACKUP_AND_RESTORE_REQUIRED')
        b=_load(backup); d=_load(restore)
        if b.get('classification')!='VERIFIED_DATABASE_BACKUP_RECEIPT': raise RuntimeError('PROVENANCE_GRAPH_BACKUP_CLASSIFICATION_INVALID')
        if d.get('classification')!='VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT': raise RuntimeError('PROVENANCE_GRAPH_RESTORE_CLASSIFICATION_INVALID')
        if m.get('database_backup_receipt_sha256') != _sha(backup): raise RuntimeError('PROVENANCE_GRAPH_MIGRATION_BACKUP_HASH_MISMATCH')
        if m.get('database_restore_drill_receipt_sha256') != _sha(restore): raise RuntimeError('PROVENANCE_GRAPH_MIGRATION_RESTORE_HASH_MISMATCH')
        if b.get('restore_drill_receipt_sha256') != _sha(restore): raise RuntimeError('PROVENANCE_GRAPH_BACKUP_RESTORE_HASH_MISMATCH')
        if m.get('database_restore_drill_provenance_sha256') != d.get('provenance_sha256'): raise RuntimeError('PROVENANCE_GRAPH_RESTORE_PROVENANCE_MISMATCH')
        if b.get('restore_drill_provenance_sha256') != d.get('provenance_sha256'): raise RuntimeError('PROVENANCE_GRAPH_BACKUP_RESTORE_PROVENANCE_MISMATCH')
        if m.get('database_environment_fingerprint') and b.get('environment_fingerprint') != m.get('database_environment_fingerprint'): raise RuntimeError('PROVENANCE_GRAPH_ENVIRONMENT_MISMATCH')
        nodes['database_backup']={'sha256':_sha(backup),'classification':b.get('classification'),'backup_sha256':b.get('backup_sha256'),'environment_fingerprint':b.get('environment_fingerprint')}
        nodes['database_restore_drill']={'sha256':_sha(restore),'classification':d.get('classification'),'provenance_sha256':d.get('provenance_sha256'),'environment_fingerprint':d.get('environment_fingerprint')}
        edges += [
          {'from':'database_migration','to':'database_backup','relation':'hash_binds'},
          {'from':'database_migration','to':'database_restore_drill','relation':'hash_binds'},
          {'from':'database_backup','to':'database_restore_drill','relation':'hash_binds'},
        ]
    elif any(x is not None for x in (migration,backup,restore)):
        raise RuntimeError('PROVENANCE_GRAPH_DATABASE_EVIDENCE_UNEXPECTED')
    if package_provenance is not None:
        p=_load(package_provenance)
        if p.get('git_commit_sha') != a.get('post_update_git_commit_sha'): raise RuntimeError('PROVENANCE_GRAPH_PACKAGE_GIT_IDENTITY_MISMATCH')
        nodes['package_provenance']={'sha256':_sha(package_provenance),'classification':p.get('classification'),'git_commit_sha':p.get('git_commit_sha')}
        edges.append({'from':'release_acceptance','to':'package_provenance','relation':'git_identity_and_artifact_context'})
    if rollback_acceptance is not None:
        ra=_load(rollback_acceptance)
        if ra.get('classification')!='VERIFIED_RELEASE_ROLLBACK_ACCEPTANCE_RECEIPT': raise RuntimeError('PROVENANCE_GRAPH_ROLLBACK_ACCEPTANCE_CLASSIFICATION_INVALID')
        if ra.get('source_rollback_receipt_sha256') != _sha(rollback): raise RuntimeError('PROVENANCE_GRAPH_ROLLBACK_ACCEPTANCE_RECEIPT_HASH_MISMATCH')
        if ra.get('source_update_acceptance_receipt_sha256') != _sha(acceptance): raise RuntimeError('PROVENANCE_GRAPH_ROLLBACK_ACCEPTANCE_UPDATE_HASH_MISMATCH')
        nodes['rollback_acceptance']={'sha256':_sha(rollback_acceptance),'classification':ra.get('classification'),'provenance_sha256':ra.get('provenance_sha256')}
        edges += [
          {'from':'rollback_acceptance','to':'rollback','relation':'hash_binds'},
          {'from':'rollback_acceptance','to':'release_acceptance','relation':'hash_binds'},
        ]
    if signing_verification is not None:
        sv=_load(signing_verification)
        if sv.get('classification')!='TRUSTED_SIGNING_VERIFICATION_RECEIPT' or sv.get('trusted') is not True: raise RuntimeError('PROVENANCE_GRAPH_SIGNING_VERIFICATION_INVALID')
        subject_hashes={node.get('sha256') for node in nodes.values()}
        if sv.get('subject_sha256') not in subject_hashes: raise RuntimeError('PROVENANCE_GRAPH_SIGNING_SUBJECT_NOT_IN_GRAPH')
        nodes['trusted_signing_verification']={'sha256':_sha(signing_verification),'classification':sv.get('classification'),'signing_identity':sv.get('signing_identity'),'verifier_identity':sv.get('verifier_identity')}
        edges.append({'from':'trusted_signing_verification','to':'release_acceptance','relation':'external_trust_verification_context'})
    body={
      'schema_version':'1.0','classification':'VERIFIED_RELEASE_PROVENANCE_GRAPH',
      'git_commit_sha':a.get('post_update_git_commit_sha'),'nodes':nodes,'edges':edges,
      'created_at':datetime.now(timezone.utc).isoformat(),'signature_status':'UNSIGNED',
      'policy':'HASH_CLOSED_RESTORE_TO_MIGRATION_TO_RELEASE_TO_ROLLBACK_ACCEPTANCE_GRAPH; TRUST_REQUIRES_EXTERNAL_VERIFICATION_RECEIPT',
    }
    trusted='trusted_signing_verification' in nodes
    body['signature_status']='VERIFIED_EXTERNAL_TRUST_PROVIDER' if trusted else 'UNSIGNED'
    body['graph_sha256']=_canonical(body)
    _atomic(output,body)
    return {'verified':True,'output':str(output),'graph_sha256':body['graph_sha256'],'node_count':len(nodes),'edge_count':len(edges),'trusted_provenance':trusted}


def verify_graph(path: Path) -> dict:
    p=_load(path); digest=p.get('graph_sha256'); body=dict(p); body.pop('graph_sha256',None)
    problems=[]
    if p.get('classification')!='VERIFIED_RELEASE_PROVENANCE_GRAPH': problems.append('CLASSIFICATION_INVALID')
    if digest != _canonical(body): problems.append('GRAPH_DIGEST_MISMATCH')
    trusted=p.get('signature_status')=='VERIFIED_EXTERNAL_TRUST_PROVIDER'
    if not trusted: problems.append('TRUSTED_SIGNATURE_NOT_PRESENT')
    return {'verified_structure':not any(x!='TRUSTED_SIGNATURE_NOT_PRESENT' for x in problems),'trusted_provenance':trusted and not problems,'problems':problems,'graph_sha256':digest}


def main()->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build'); b.add_argument('--acceptance',type=Path,required=True); b.add_argument('--rollback',type=Path,required=True); b.add_argument('--migration',type=Path); b.add_argument('--backup',type=Path); b.add_argument('--restore',type=Path); b.add_argument('--package-provenance',type=Path); b.add_argument('--rollback-acceptance',type=Path); b.add_argument('--signing-verification',type=Path); b.add_argument('--output',type=Path,required=True)
    v=sub.add_parser('verify'); v.add_argument('--input',type=Path,required=True); a=p.parse_args()
    result=build_graph(acceptance=a.acceptance,rollback=a.rollback,migration=a.migration,backup=a.backup,restore=a.restore,package_provenance=a.package_provenance,rollback_acceptance=a.rollback_acceptance,signing_verification=a.signing_verification,output=a.output) if a.cmd=='build' else verify_graph(a.input)
    print(json.dumps(result,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
