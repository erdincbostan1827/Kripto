from __future__ import annotations
import argparse, json
from pathlib import Path
JOURNALS={
 'release_update':'.release-update.transaction.json',
 'database_migration':'.database-migration.transaction.json',
 'dependency_locks':'.dependency-lock-bootstrap.transaction.json',
}
def inspect(root:Path)->dict:
    root=root.resolve(); active=[]; problems=[]
    for kind,name in JOURNALS.items():
        p=root/name
        if p.is_symlink(): problems.append(f'{kind}:JOURNAL_SYMLINK'); continue
        if p.exists():
            if not p.is_file(): problems.append(f'{kind}:JOURNAL_UNSAFE'); continue
            try: body=json.loads(p.read_text())
            except Exception as e: problems.append(f'{kind}:JOURNAL_INVALID:{type(e).__name__}'); continue
            active.append({'kind':kind,'path':name,'classification':body.get('classification'),'status':body.get('status'),'transaction_id':body.get('transaction_id')})
    lock=root/'.platform-operation.lock.json'
    if lock.is_symlink(): problems.append('operation_lock:SYMLINK')
    elif lock.exists() and lock.is_file():
        try: lb=json.loads(lock.read_text()); active.append({'kind':'operation_lock','path':lock.name,'operation':lb.get('operation'),'token':lb.get('token')})
        except Exception as e: problems.append(f'operation_lock:INVALID:{type(e).__name__}')
    conflicting=[x['kind'] for x in active if x['kind']!='operation_lock']
    if len(conflicting)>1: problems.append('MULTIPLE_MUTATION_JOURNALS_PRESENT:'+','.join(sorted(conflicting)))
    return {'schema_version':'1.0','classification':'DEPLOYMENT_TRANSACTION_STATE','active':active,'problems':problems,'safe_to_start_new_mutation':not active and not problems}
def assert_no_conflicting_journals(root:Path, *, allowed:set[str]|None=None)->dict:
    allowed=allowed or set(); result=inspect(root)
    conflicts=[x['kind'] for x in result['active'] if x['kind'] not in allowed and x['kind']!='operation_lock']
    if conflicts:
        raise RuntimeError('DEPLOYMENT_TRANSACTION_CONFLICT:'+','.join(sorted(conflicts)))
    journal_problems=[x for x in result['problems'] if not x.startswith('MULTIPLE_MUTATION_JOURNALS_PRESENT:')]
    if journal_problems:
        raise RuntimeError('DEPLOYMENT_TRANSACTION_STATE_INVALID:'+','.join(journal_problems))
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True); a=p.parse_args(); r=inspect(a.root); print(json.dumps(r,sort_keys=True)); raise SystemExit(0 if not r['problems'] else 2)
if __name__=='__main__': main()
