from __future__ import annotations
from dataclasses import dataclass
import hashlib,hmac,json,time

class HeartbeatSigner:
    def __init__(self,key:bytes):
        if len(key)<16: raise ValueError('watchdog signing key too short')
        self.key=key
    def sign(self,payload:dict):
        body=json.dumps(payload,sort_keys=True,separators=(',',':')).encode(); return hmac.new(self.key,body,hashlib.sha256).hexdigest()
    def verify(self,payload:dict,signature:str): return hmac.compare_digest(self.sign(payload),signature)

def heartbeat_payload(risk_state,last_reconciliation,outbox_backlog,*,health='UP',ready=True,last_market_data_age=0.0,private_stream_age=0.0,process_id='trading-engine'):
    return {'timestamp':time.time(),'process_id':process_id,'health':health,'ready':bool(ready),'last_market_data_age':float(last_market_data_age),'private_stream_age':float(private_stream_age),'risk_state':str(risk_state),'last_reconciliation':last_reconciliation,'outbox_backlog':int(outbox_backlog)}

@dataclass(frozen=True)
class WatchdogAssessment:
    healthy: bool
    severity: str
    reasons: tuple[str,...]

class ExternalWatchdog:
    def __init__(self,signer:HeartbeatSigner,max_heartbeat_age=30,max_market_data_age=5,max_private_stream_age=30,max_outbox_backlog=100):
        self.signer=signer; self.max_heartbeat_age=max_heartbeat_age; self.max_market_data_age=max_market_data_age; self.max_private_stream_age=max_private_stream_age; self.max_outbox_backlog=max_outbox_backlog
    def assess(self,payload:dict,signature:str,*,now:float|None=None)->WatchdogAssessment:
        if not self.signer.verify(payload,signature): return WatchdogAssessment(False,'SEV1',('INVALID_HEARTBEAT_SIGNATURE',))
        now=time.time() if now is None else now; reasons=[]
        age=now-float(payload.get('timestamp',0))
        if age < 0: reasons.append('CLOCK_REGRESSION')
        elif age>self.max_heartbeat_age: reasons.append('PROCESS_HEARTBEAT_STALE')
        if payload.get('health')!='UP': reasons.append('HEALTH_DOWN')
        if not payload.get('ready'): reasons.append('NOT_READY')
        if float(payload.get('last_market_data_age',1e18))>self.max_market_data_age: reasons.append('MARKET_DATA_STALE')
        if float(payload.get('private_stream_age',1e18))>self.max_private_stream_age: reasons.append('PRIVATE_STREAM_STALE')
        if int(payload.get('outbox_backlog',10**9))>self.max_outbox_backlog: reasons.append('OUTBOX_BACKLOG_HIGH')
        if str(payload.get('risk_state')) not in {'ACTIVE','REDUCING_ONLY','HALTED'}: reasons.append('UNKNOWN_RISK_STATE')
        return WatchdogAssessment(not reasons,'OK' if not reasons else 'SEV1',tuple(reasons))
