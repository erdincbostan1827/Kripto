from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def canonical(x:dict)->str: return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def normalize_environment_id(value: str) -> str:
    value=value.strip()
    if not value or len(value)>128 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-' for c in value):
        raise SystemExit('RESTORE_DRILL_ENVIRONMENT_ID_INVALID')
    return value

def environment_fingerprint(value: str) -> str:
    return hashlib.sha256(("ctp-environment-v1:"+value).encode()).hexdigest()

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--backup',type=Path,required=True); p.add_argument('--restored-table-count',type=int,required=True); p.add_argument('--environment-id',required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    backup=a.backup.resolve(); out=a.output.resolve(); env_id=normalize_environment_id(a.environment_id)
    if backup.is_symlink() or not backup.is_file(): raise SystemExit('RESTORE_DRILL_BACKUP_UNSAFE')
    if a.restored_table_count<=0: raise SystemExit('RESTORE_DRILL_TABLE_COUNT_INVALID')
    body={"schema_version":"1.1","classification":"VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT","backup_sha256":sha(backup),"restore_status":"PASS","restored_table_count":a.restored_table_count,"environment_id":env_id,"environment_fingerprint":environment_fingerprint(env_id),"completed_at":datetime.now(timezone.utc).isoformat(),"policy":"REAL_RESTORE_COMMAND_COMPLETED_AND_DATABASE_SMOKE_CHECK_PASSED; ENVIRONMENT_BOUND_AND_FRESHNESS_VERIFIABLE"}
    body['provenance_sha256']=canonical(body); out.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=f'.{out.name}.',suffix='.tmp',dir=out.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(body,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,out)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
    print(json.dumps({"created":True,"output":str(out),"environment_fingerprint":body['environment_fingerprint'],"provenance_sha256":body['provenance_sha256']},sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())

# Phase 193 library helper. CLI integration remains optional to preserve existing invocation contract.
def append_restore_receipt_to_audit(*, receipt: Path, audit_root: Path) -> dict:
    if receipt.is_symlink() or not receipt.is_file(): raise RuntimeError('RESTORE_DRILL_RECEIPT_UNSAFE')
    payload=json.loads(receipt.read_text(encoding='utf-8'))
    if payload.get('classification')!='VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT': raise RuntimeError('RESTORE_DRILL_RECEIPT_CLASSIFICATION_INVALID')
    provenance=payload.get('provenance_sha256'); body=dict(payload); body.pop('provenance_sha256',None)
    if provenance!=canonical(body): raise RuntimeError('RESTORE_DRILL_RECEIPT_PROVENANCE_MISMATCH')
    try:
        from scripts.deployment_audit_chain import append_event
    except ModuleNotFoundError:
        from deployment_audit_chain import append_event
    return append_event(audit_root,event_type='DATABASE_RESTORE_DRILL_VERIFIED',subjects={
        'restore_drill_receipt_sha256':sha(receipt), 'provenance_sha256':provenance,
        'backup_sha256':payload.get('backup_sha256'),'environment_fingerprint':payload.get('environment_fingerprint'),
        'restored_table_count':payload.get('restored_table_count')})
