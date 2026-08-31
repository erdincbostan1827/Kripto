from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib,hmac,json

@dataclass(frozen=True)
class AuditCheckpoint:
    sequence:int
    root_hash:str
    previous_checkpoint_hash:str|None
    actor:str
    action:str
    object_ref:str
    correlation_id:str
    reason:str
    release_version:str
    created_at:str
    signature:str
    @property
    def checkpoint_hash(self):
        payload={k:v for k,v in self.__dict__.items() if k!='signature'}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def merkle_root(record_hashes:list[str])->str:
    if not record_hashes: return hashlib.sha256(b'').hexdigest()
    level=[bytes.fromhex(x) for x in record_hashes]
    while len(level)>1:
        if len(level)%2: level.append(level[-1])
        level=[hashlib.sha256(level[i]+level[i+1]).digest() for i in range(0,len(level),2)]
    return level[0].hex()

def create_checkpoint(record_hashes:list[str], *, sequence:int, secret:bytes, previous_checkpoint_hash:str|None=None, actor:str, action:str, object_ref:str, correlation_id:str, reason:str, release_version:str, created_at:str|None=None):
    if not secret: raise ValueError('checkpoint signing secret required')
    ts=created_at or datetime.now(timezone.utc).isoformat()
    unsigned=dict(sequence=sequence,root_hash=merkle_root(record_hashes),previous_checkpoint_hash=previous_checkpoint_hash,actor=actor,action=action,object_ref=object_ref,correlation_id=correlation_id,reason=reason,release_version=release_version,created_at=ts)
    sig=hmac.new(secret,json.dumps(unsigned,sort_keys=True,separators=(',',':')).encode(),hashlib.sha256).hexdigest()
    return AuditCheckpoint(**unsigned,signature=sig)

def verify_checkpoint(checkpoint:AuditCheckpoint, record_hashes:list[str], *, secret:bytes, expected_previous_hash:str|None=None)->bool:
    if checkpoint.root_hash != merkle_root(record_hashes): return False
    if checkpoint.previous_checkpoint_hash != expected_previous_hash: return False
    unsigned={k:v for k,v in checkpoint.__dict__.items() if k!='signature'}
    expected=hmac.new(secret,json.dumps(unsigned,sort_keys=True,separators=(',',':')).encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,checkpoint.signature)
