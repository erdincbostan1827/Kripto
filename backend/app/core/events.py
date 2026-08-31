from __future__ import annotations
from dataclasses import dataclass,field,asdict
from datetime import datetime,timezone
import hashlib,json,uuid

def utcnow(): return datetime.now(timezone.utc)
@dataclass(frozen=True)
class DomainEvent:
    event_type:str; aggregate_id:str; payload:dict
    schema_version:int=1; sequence:int=1; event_id:str=field(default_factory=lambda:uuid.uuid4().hex)
    correlation_id:str=field(default_factory=lambda:uuid.uuid4().hex)
    causation_id:str|None=None; event_time:datetime=field(default_factory=utcnow); received_at:datetime=field(default_factory=utcnow); producer_version:str='0.3.0'
    @property
    def payload_hash(self)->str: return hashlib.sha256(json.dumps(self.payload,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
    def record(self)->dict: return {**asdict(self),'payload_hash':self.payload_hash}

class ReplayError(RuntimeError):
    """Raised when deterministic event replay cannot continue safely."""
class EventReplayer:
    def __init__(self,handlers:dict[str,callable],upcasters:dict[tuple[str,int],callable]|None=None): self.handlers=handlers; self.upcasters=upcasters or {}
    def replay(self,events:list[DomainEvent],initial=None):
        state=initial
        ordered=sorted(events,key=lambda e:e.sequence)
        for i,e in enumerate(ordered,1):
            if e.sequence!=i: raise ReplayError('sequence gap or duplicate')
            while (e.event_type,e.schema_version) in self.upcasters: e=self.upcasters[(e.event_type,e.schema_version)](e)
            if e.event_type not in self.handlers: raise ReplayError('unknown event type')
            state=self.handlers[e.event_type](state,e)
        return state

@dataclass
class DeadLetter:
    original_event_id:str; event_type:str; schema_version:int; payload_hash:str; failure_reason:str; correlation_id:str; attempts:int; consumer_version:str; resolution_state:str='OPEN'; first_failed_at:datetime=field(default_factory=utcnow); last_failed_at:datetime=field(default_factory=utcnow)

@dataclass(frozen=True)
class ReplayCheckpoint:
    last_sequence:int
    state_hash:str
    event_chain_hash:str
    producer_version:str

def _stable_hash(value)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()

def event_chain_hash(events:list[DomainEvent])->str:
    h='0'*64
    for e in sorted(events,key=lambda x:x.sequence):
        h=hashlib.sha256((h+e.payload_hash+str(e.sequence)+e.event_type).encode()).hexdigest()
    return h

def create_replay_checkpoint(state,events:list[DomainEvent],producer_version='0.3.0')->ReplayCheckpoint:
    ordered=sorted(events,key=lambda e:e.sequence)
    if ordered and [e.sequence for e in ordered] != list(range(1,len(ordered)+1)): raise ReplayError('sequence gap or duplicate')
    return ReplayCheckpoint(len(ordered),_stable_hash(state),event_chain_hash(ordered),producer_version)

def verify_replay_checkpoint(checkpoint:ReplayCheckpoint,state,events:list[DomainEvent])->bool:
    ordered=sorted(events,key=lambda e:e.sequence)
    if len(ordered)!=checkpoint.last_sequence: return False
    return checkpoint.state_hash==_stable_hash(state) and checkpoint.event_chain_hash==event_chain_hash(ordered)
