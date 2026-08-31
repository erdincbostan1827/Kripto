from __future__ import annotations
from dataclasses import dataclass
import hashlib,hmac,json

CRITICAL_ACTIONS={"LIVE_MODE_CHANGE","RISK_LIMIT_CHANGE","API_CREDENTIAL_METADATA_CHANGE","ORDER_INTENT","ORDER_FILL_RECONCILIATION","MANUAL_EXTERNAL_ACTIVITY_ACCEPTANCE","PANIC_CLOSE","STRATEGY_PROMOTION","DEPLOYMENT_RELEASE"}
@dataclass(frozen=True)
class WormAuditRecord:
    sequence:int; action:str; payload:dict; previous_hash:str; record_hash:str

class WormAuditExporter:
    def __init__(self,key:bytes):
        if len(key)<32: raise ValueError(">=32-byte signing key required")
        self.key=key
    def append(self,records:list[WormAuditRecord],*,action:str,payload:dict)->WormAuditRecord:
        if action not in CRITICAL_ACTIONS: raise ValueError("unsupported critical audit action")
        prev=records[-1].record_hash if records else "GENESIS"
        seq=len(records)+1
        raw=json.dumps({"sequence":seq,"action":action,"payload":payload,"previous_hash":prev},sort_keys=True,separators=(",",":"),default=str).encode()
        digest=hmac.new(self.key,raw,hashlib.sha256).hexdigest()
        rec=WormAuditRecord(seq,action,dict(payload),prev,digest); records.append(rec); return rec
    def verify(self,records:list[WormAuditRecord])->bool:
        prev="GENESIS"
        for i,r in enumerate(records,1):
            if r.sequence!=i or r.previous_hash!=prev or r.action not in CRITICAL_ACTIONS: return False
            raw=json.dumps({"sequence":r.sequence,"action":r.action,"payload":r.payload,"previous_hash":r.previous_hash},sort_keys=True,separators=(",",":"),default=str).encode()
            if not hmac.compare_digest(r.record_hash,hmac.new(self.key,raw,hashlib.sha256).hexdigest()): return False
            prev=r.record_hash
        return True
    def export_append_only_jsonl(self,records:list[WormAuditRecord])->bytes:
        if not self.verify(records): raise ValueError("audit chain invalid")
        return ("\n".join(json.dumps(r.__dict__,sort_keys=True,separators=(",",":")) for r in records)+"\n").encode()
