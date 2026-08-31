from __future__ import annotations
import argparse, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path
AUDIT='.deployment-audit-chain.jsonl'

def _canonical(x:dict)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def verify(root:Path)->dict:
    path=root.resolve()/AUDIT
    if not path.exists(): return {'verified':True,'event_count':0,'head_sha256':None,'problems':[]}
    if path.is_symlink() or not path.is_file(): return {'verified':False,'event_count':0,'head_sha256':None,'problems':['AUDIT_PATH_UNSAFE']}
    prev=None; count=0; problems=[]
    for i,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: e=json.loads(line)
        except Exception: problems.append(f'LINE_{i}_INVALID_JSON'); continue
        digest=e.get('event_sha256'); body=dict(e); body.pop('event_sha256',None)
        if digest!=_canonical(body): problems.append(f'LINE_{i}_DIGEST_MISMATCH')
        if body.get('previous_event_sha256')!=prev: problems.append(f'LINE_{i}_PREVIOUS_HASH_MISMATCH')
        prev=digest; count+=1
    return {'verified':not problems,'event_count':count,'head_sha256':prev,'problems':problems}

def append_event(root:Path, *, event_type:str, subjects:dict)->dict:
    root=root.resolve(); path=root/AUDIT
    if path.is_symlink() or (path.exists() and not path.is_file()): raise RuntimeError('DEPLOYMENT_AUDIT_PATH_UNSAFE')
    current=verify(root)
    if not current['verified']: raise RuntimeError(f"DEPLOYMENT_AUDIT_CHAIN_TAMPERED:{current['problems']}")
    body={'schema_version':'1.1','classification':'TAMPER_EVIDENT_DEPLOYMENT_AUDIT_EVENT','event_type':event_type,'created_at':datetime.now(timezone.utc).isoformat(),'previous_event_sha256':current['head_sha256'],'subjects':subjects}
    body['event_sha256']=_canonical(body)
    flags=os.O_WRONLY|os.O_CREAT|os.O_APPEND
    if hasattr(os,'O_NOFOLLOW'): flags|=os.O_NOFOLLOW
    fd=os.open(path,flags,0o600)
    with os.fdopen(fd,'a',encoding='utf-8') as f:
        f.write(json.dumps(body,sort_keys=True)+'\n'); f.flush(); os.fsync(f.fileno())
    after=verify(root)
    if not after['verified'] or after['head_sha256']!=body['event_sha256']:
        raise RuntimeError(f"DEPLOYMENT_AUDIT_APPEND_VERIFY_FAILED:{after['problems']}")
    return body

def main()->int:
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('append'); a.add_argument('--root',type=Path,required=True); a.add_argument('--event-type',required=True); a.add_argument('--subjects-json',default='{}')
    v=sub.add_parser('verify'); v.add_argument('--root',type=Path,required=True)
    ns=ap.parse_args()
    if ns.cmd=='append':
        subjects=json.loads(ns.subjects_json)
        if not isinstance(subjects,dict): raise SystemExit('DEPLOYMENT_AUDIT_SUBJECTS_MUST_BE_OBJECT')
        result=append_event(ns.root,event_type=ns.event_type,subjects=subjects)
    else: result=verify(ns.root)
    print(json.dumps(result,sort_keys=True)); return 0 if (ns.cmd=='append' or result['verified']) else 2
if __name__=='__main__': raise SystemExit(main())
