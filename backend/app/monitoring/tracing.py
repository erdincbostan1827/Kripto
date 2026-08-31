from __future__ import annotations
from dataclasses import dataclass,field
import random,time

LATENCY_STAGES=('market_data_receive','feature_signal_compute','risk_decision','submit_network','exchange_ack','fill','private_stream_propagation','db_persistence')

@dataclass
class TraceRecord:
    trace_id:str
    sampled:bool
    latencies_ms:dict[str,float]=field(default_factory=dict)

class BoundedLatencyTracer:
    """Lightweight bounded tracing: no unbounded high-cardinality label storage."""
    def __init__(self,sample_rate:float=0.1,max_records:int=1000,rng:random.Random|None=None):
        if not 0<=sample_rate<=1 or max_records<1: raise ValueError('invalid tracing policy')
        self.sample_rate=sample_rate; self.max_records=max_records; self.rng=rng or random.Random(); self.records:list[TraceRecord]=[]
    def start(self,trace_id:str)->TraceRecord:
        rec=TraceRecord(trace_id,self.rng.random()<self.sample_rate)
        if rec.sampled:
            self.records.append(rec)
            if len(self.records)>self.max_records: del self.records[:-self.max_records]
        return rec
    def observe(self,rec:TraceRecord,stage:str,started_monotonic:float,ended_monotonic:float|None=None)->None:
        if stage not in LATENCY_STAGES: raise ValueError('unknown latency stage')
        if not rec.sampled: return
        end=time.perf_counter() if ended_monotonic is None else ended_monotonic
        if end<started_monotonic: raise RuntimeError('monotonic clock regression')
        rec.latencies_ms[stage]=(end-started_monotonic)*1000
    def decomposition(self,rec:TraceRecord)->dict:
        missing=[x for x in LATENCY_STAGES if x not in rec.latencies_ms]
        return {'trace_id':rec.trace_id,'sampled':rec.sampled,'latencies_ms':dict(rec.latencies_ms),'missing_stages':missing,'total_observed_ms':sum(rec.latencies_ms.values())}
