from __future__ import annotations
import argparse, base64, hashlib, json, os, secrets, subprocess, tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

DEFAULT_TTL_SECONDS=300
MAX_TTL_SECONDS=900
CLOCK_SKEW_SECONDS=30

def _sha(path:Path)->str:
    if path.is_symlink() or not path.is_file(): raise RuntimeError('SIGNING_INPUT_UNSAFE')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _canonical(payload:dict)->str:
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _atomic(path:Path,payload:dict):
    path.parent.mkdir(parents=True,exist_ok=True); fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(payload,f,indent=2,sort_keys=True); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

def _dt(value:str, code:str)->datetime:
    if not isinstance(value,str) or not value: raise RuntimeError(code+'_MISSING')
    try: d=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc: raise RuntimeError(code+'_INVALID') from exc
    if d.tzinfo is None: raise RuntimeError(code+'_TIMEZONE_MISSING')
    return d.astimezone(timezone.utc)

def build_request(*, subject:Path, output:Path, ttl_seconds:int=DEFAULT_TTL_SECONDS)->dict:
    if not 1 <= ttl_seconds <= MAX_TTL_SECONDS: raise RuntimeError('SIGNING_REQUEST_TTL_INVALID')
    raw=json.loads(subject.read_text()); digest=raw.get('canonical_payload_sha256') or raw.get('graph_sha256')
    if not isinstance(digest,str) or len(digest)!=64: raise RuntimeError('SIGNING_SUBJECT_CANONICAL_DIGEST_MISSING')
    now=datetime.now(timezone.utc); expires=now+timedelta(seconds=ttl_seconds)
    body={'schema_version':'1.1','classification':'TRUSTED_SIGNING_REQUEST','subject_sha256':_sha(subject),'canonical_payload_sha256':digest,'subject_classification':raw.get('classification'),'algorithm':'EXTERNAL_TRUST_PROVIDER_REQUIRED','signature_status':'UNSIGNED','nonce':secrets.token_hex(32),'issued_at':now.isoformat(),'expires_at':expires.isoformat(),'policy':'LOCAL_CODE_MAY_PREPARE_BUT_MUST_NOT_FORGE_TRUSTED_SIGNATURES; NONCE_AND_EXPIRY_BOUND'}
    _atomic(output,body); return body

def attach_external_signature(*, request:Path, signature_file:Path, signing_identity:str, output:Path)->dict:
    req=json.loads(request.read_text()); sig=signature_file.read_bytes()
    if req.get('classification')!='TRUSTED_SIGNING_REQUEST': raise RuntimeError('SIGNING_REQUEST_INVALID')
    if not signing_identity.strip() or len(sig)<16: raise RuntimeError('EXTERNAL_SIGNATURE_INVALID')
    body=dict(req); body.update({'classification':'TRUSTED_SIGNING_ENVELOPE','signature_status':'SIGNED_EXTERNAL_UNVERIFIED','signing_identity':signing_identity.strip(),'signature_base64':base64.b64encode(sig).decode(),'signature_file_sha256':hashlib.sha256(sig).hexdigest(),'request_sha256':_sha(request)})
    _atomic(output,body); return body

def _consume_nonce(ledger:Path, *, nonce:str, envelope_sha256:str, verifier_identity:str)->None:
    if ledger.is_symlink() or (ledger.exists() and not ledger.is_file()): raise RuntimeError('TRUSTED_VERIFIER_REPLAY_LEDGER_UNSAFE')
    entries=[]
    if ledger.exists():
        for line in ledger.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            try: entry=json.loads(line)
            except Exception as exc: raise RuntimeError('TRUSTED_VERIFIER_REPLAY_LEDGER_INVALID') from exc
            if entry.get('nonce')==nonce: raise RuntimeError('TRUSTED_SIGNATURE_REPLAY_DETECTED')
            entries.append(entry)
    entry={'nonce':nonce,'envelope_sha256':envelope_sha256,'verifier_identity':verifier_identity,'consumed_at':datetime.now(timezone.utc).isoformat()}
    ledger.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+ledger.name+'.',suffix='.tmp',dir=ledger.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            for x in [*entries,entry]: f.write(json.dumps(x,sort_keys=True)+'\n')
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,ledger)
    except BaseException:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise

def verify_external_signature(*, envelope:Path, verifier_command:list[str], verifier_identity:str, output:Path, timeout_seconds:int=60, replay_ledger:Path|None=None)->dict:
    if not verifier_command or not all(isinstance(x,str) and x for x in verifier_command): raise RuntimeError('TRUSTED_VERIFIER_COMMAND_INVALID')
    env=json.loads(envelope.read_text()); env_sha=_sha(envelope)
    if env.get('classification')!='TRUSTED_SIGNING_ENVELOPE' or env.get('signature_status')!='SIGNED_EXTERNAL_UNVERIFIED': raise RuntimeError('TRUSTED_SIGNING_ENVELOPE_INVALID')
    if not verifier_identity.strip(): raise RuntimeError('TRUSTED_VERIFIER_IDENTITY_REQUIRED')
    nonce=env.get('nonce')
    if not isinstance(nonce,str) or len(nonce)<32: raise RuntimeError('TRUSTED_SIGNING_NONCE_INVALID')
    issued=_dt(env.get('issued_at'),'TRUSTED_SIGNING_ISSUED_AT'); expires=_dt(env.get('expires_at'),'TRUSTED_SIGNING_EXPIRES_AT'); now=datetime.now(timezone.utc)
    if expires <= issued or (expires-issued).total_seconds()>MAX_TTL_SECONDS: raise RuntimeError('TRUSTED_SIGNING_VALIDITY_WINDOW_INVALID')
    if now < issued-timedelta(seconds=CLOCK_SKEW_SECONDS): raise RuntimeError('TRUSTED_SIGNING_NOT_YET_VALID')
    if now > expires+timedelta(seconds=CLOCK_SKEW_SECONDS): raise RuntimeError('TRUSTED_SIGNING_EXPIRED')
    try: proc=subprocess.run([*verifier_command,str(envelope.resolve())],text=True,capture_output=True,timeout=timeout_seconds,check=False,shell=False)
    except subprocess.TimeoutExpired as exc: raise RuntimeError('TRUSTED_SIGNATURE_VERIFIER_TIMEOUT') from exc
    if proc.returncode!=0: raise RuntimeError(f'TRUSTED_SIGNATURE_VERIFIER_FAILED:{proc.returncode}')
    lines=[x for x in proc.stdout.splitlines() if x.strip()]
    if not lines: raise RuntimeError('TRUSTED_SIGNATURE_VERIFIER_OUTPUT_MISSING')
    try: verdict=json.loads(lines[-1])
    except Exception as exc: raise RuntimeError('TRUSTED_SIGNATURE_VERIFIER_OUTPUT_INVALID') from exc
    expected={'subject_sha256':env.get('subject_sha256'),'canonical_payload_sha256':env.get('canonical_payload_sha256'),'signing_identity':env.get('signing_identity'),'nonce':nonce,'envelope_sha256':env_sha,'verifier_identity':verifier_identity.strip()}
    if verdict.get('verified') is not True: raise RuntimeError('TRUSTED_SIGNATURE_NOT_VERIFIED')
    for k,v in expected.items():
        if verdict.get(k)!=v: raise RuntimeError(f'TRUSTED_SIGNATURE_VERIFIER_{k.upper()}_MISMATCH')
    verdict_issued=_dt(verdict.get('issued_at'),'TRUSTED_VERDICT_ISSUED_AT'); verdict_expires=_dt(verdict.get('expires_at'),'TRUSTED_VERDICT_EXPIRES_AT')
    if verdict_expires<=verdict_issued or verdict_expires>expires+timedelta(seconds=CLOCK_SKEW_SECONDS): raise RuntimeError('TRUSTED_VERDICT_VALIDITY_WINDOW_INVALID')
    if now < verdict_issued-timedelta(seconds=CLOCK_SKEW_SECONDS) or now > verdict_expires+timedelta(seconds=CLOCK_SKEW_SECONDS): raise RuntimeError('TRUSTED_VERDICT_EXPIRED_OR_NOT_YET_VALID')
    ledger=(replay_ledger or output.parent/'.trusted-signing-replay-ledger.jsonl').resolve()
    _consume_nonce(ledger,nonce=nonce,envelope_sha256=env_sha,verifier_identity=verifier_identity.strip())
    body={'schema_version':'1.1','classification':'TRUSTED_SIGNING_VERIFICATION_RECEIPT','signature_status':'VERIFIED_EXTERNAL_TRUST_PROVIDER','trusted':True,'envelope_sha256':env_sha,'subject_sha256':env['subject_sha256'],'canonical_payload_sha256':env['canonical_payload_sha256'],'signing_identity':env['signing_identity'],'nonce':nonce,'verifier_identity':verifier_identity.strip(),'verifier_evidence':verdict,'verified_at':datetime.now(timezone.utc).isoformat(),'replay_ledger_sha256':_sha(ledger),'policy':'TRUSTED_ONLY_AFTER_EXTERNAL_VERIFIER_RETURNS_HASH_IDENTITY_NONCE_AND_FRESHNESS_BOUND_VERDICT; REPLAY_FAIL_CLOSED'}
    body['verification_receipt_sha256']=_canonical(body); _atomic(output,body); return body

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('request'); a.add_argument('--subject',type=Path,required=True); a.add_argument('--output',type=Path,required=True); a.add_argument('--ttl-seconds',type=int,default=DEFAULT_TTL_SECONDS)
    b=sub.add_parser('attach'); b.add_argument('--request',type=Path,required=True); b.add_argument('--signature-file',type=Path,required=True); b.add_argument('--signing-identity',required=True); b.add_argument('--output',type=Path,required=True)
    c=sub.add_parser('verify'); c.add_argument('--envelope',type=Path,required=True); c.add_argument('--verifier-command-json',required=True); c.add_argument('--verifier-identity',required=True); c.add_argument('--timeout-seconds',type=int,default=60); c.add_argument('--replay-ledger',type=Path); c.add_argument('--output',type=Path,required=True)
    x=p.parse_args()
    if x.cmd=='request': r=build_request(subject=x.subject,output=x.output,ttl_seconds=x.ttl_seconds)
    elif x.cmd=='attach': r=attach_external_signature(request=x.request,signature_file=x.signature_file,signing_identity=x.signing_identity,output=x.output)
    else: r=verify_external_signature(envelope=x.envelope,verifier_command=json.loads(x.verifier_command_json),verifier_identity=x.verifier_identity,output=x.output,timeout_seconds=x.timeout_seconds,replay_ledger=x.replay_ledger)
    print(json.dumps(r,sort_keys=True))
if __name__=='__main__': main()
