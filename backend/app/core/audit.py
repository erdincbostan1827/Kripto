from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
import hashlib,json
@dataclass(frozen=True)
class AuditEntry:
    previous_hash:str; current_hash:str; actor:str; action:str; object_ref:str; correlation_id:str; timestamp:str; reason:str; release_version:str

def _hash(payload:dict)->str: return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class AuditChain:
    def __init__(self): self.entries:list[AuditEntry]=[]
    def append(self,actor,action,object_ref,correlation_id,reason,release_version='0.3.0'):
        prev=self.entries[-1].current_hash if self.entries else 'GENESIS'
        ts=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        payload=dict(previous_hash=prev,actor=actor,action=action,object_ref=object_ref,correlation_id=correlation_id,timestamp=ts,reason=reason,release_version=release_version)
        entry=AuditEntry(current_hash=_hash(payload),**payload); self.entries.append(entry); return entry
    def verify(self)->bool:
        prev='GENESIS'
        for e in self.entries:
            if e.previous_hash!=prev: return False
            payload={k:getattr(e,k) for k in ('previous_hash','actor','action','object_ref','correlation_id','timestamp','reason','release_version')}
            if _hash(payload)!=e.current_hash: return False
            prev=e.current_hash
        return True
