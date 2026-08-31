from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha(path:Path)->str:
    if path.is_symlink() or not path.is_file(): raise RuntimeError(f'ATTESTATION_INPUT_UNSAFE:{path.name}')
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def canonical(x:dict)->str: return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def atomic(path:Path,payload:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(prefix=f'.{path.name}.',suffix='.tmp',dir=path.parent)
    try:
      with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(payload,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
      os.replace(tmp,path)
    except BaseException:
      try: os.unlink(tmp)
      except FileNotFoundError: pass
      raise

def create(*, acceptance:Path, package_provenance:Path, output:Path, migration:Path|None=None)->dict:
    a=json.loads(acceptance.read_text()); p=json.loads(package_provenance.read_text())
    if a.get('classification')!='VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT': raise RuntimeError('ATTESTATION_ACCEPTANCE_CLASSIFICATION_INVALID')
    if p.get('git_commit_sha') != a.get('post_update_git_commit_sha'): raise RuntimeError('ATTESTATION_GIT_IDENTITY_MISMATCH')
    subjects={"acceptance_receipt_sha256":sha(acceptance),"package_provenance_sha256":sha(package_provenance)}
    if migration is not None: subjects['migration_receipt_sha256']=sha(migration)
    body={"schema_version":"1.0","classification":"SIGNABLE_RELEASE_ACCEPTANCE_ATTESTATION","git_commit_sha":a.get('post_update_git_commit_sha'),"subjects":subjects,"created_at":datetime.now(timezone.utc).isoformat(),"signature_status":"UNSIGNED","signature":None,"signing_identity":None,"policy":"CANONICAL_DIGEST_READY_FOR_TRUSTED_CI_SIGNING; UNSIGNED_IS_NOT_TRUSTED_PROVENANCE"}
    body['canonical_payload_sha256']=canonical({k:v for k,v in body.items() if k!='canonical_payload_sha256'})
    atomic(output,body); return body

def verify(path:Path)->dict:
    raw=json.loads(path.read_text()); digest=raw.get('canonical_payload_sha256'); body=dict(raw); body.pop('canonical_payload_sha256',None)
    problems=[]
    if raw.get('classification')!='SIGNABLE_RELEASE_ACCEPTANCE_ATTESTATION': problems.append('CLASSIFICATION_INVALID')
    if digest!=canonical(body): problems.append('CANONICAL_DIGEST_MISMATCH')
    trusted = raw.get('signature_status')=='SIGNED' and isinstance(raw.get('signature'),str) and bool(raw.get('signing_identity'))
    if not trusted: problems.append('TRUSTED_SIGNATURE_NOT_PRESENT')
    return {"verified_structure":not any(x!='TRUSTED_SIGNATURE_NOT_PRESENT' for x in problems),"trusted_provenance":trusted and not problems,"problems":problems,"canonical_payload_sha256":digest}

def main()->int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); c=sub.add_parser('create'); c.add_argument('--acceptance',type=Path,required=True); c.add_argument('--package-provenance',type=Path,required=True); c.add_argument('--migration',type=Path); c.add_argument('--output',type=Path,required=True); v=sub.add_parser('verify'); v.add_argument('--input',type=Path,required=True); a=p.parse_args()
    result=create(acceptance=a.acceptance,package_provenance=a.package_provenance,migration=a.migration,output=a.output) if a.cmd=='create' else verify(a.input); print(json.dumps(result,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
