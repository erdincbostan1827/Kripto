from __future__ import annotations
from dataclasses import dataclass
from app.core.enums import RiskState

@dataclass(frozen=True)
class ShutdownReport:
    steps:tuple[str,...]
    clean:bool
    outbox_flushed:bool
    snapshot:object|None

class GracefulShutdown:
    def __init__(self,risk_machine,stop_scheduler,reconcile_inflight,snapshot_open_risk,db_flush,outbox_flush):
        self.risk=risk_machine; self.stop_scheduler=stop_scheduler; self.reconcile_inflight=reconcile_inflight
        self.snapshot_open_risk=snapshot_open_risk; self.db_flush=db_flush; self.outbox_flush=outbox_flush
    def run(self)->ShutdownReport:
        steps=[]
        # STOPPING must be visible before any mutating subsystem is drained.
        if hasattr(self.risk,'state'): self.risk.state=RiskState.STOPPING
        steps.append('NEW_ENTRIES_STOP')
        self.stop_scheduler(); steps.append('SCHEDULER_STOP')
        self.reconcile_inflight(); steps.append('INFLIGHT_RECONCILED')
        snap=self.snapshot_open_risk(); steps.append('OPEN_RISK_SNAPSHOT')
        self.db_flush(); steps.append('DB_FLUSH')
        outbox_ok=True
        try: self.outbox_flush(); steps.append('OUTBOX_FLUSH')
        except Exception: outbox_ok=False; steps.append('OUTBOX_FLUSH_FAILED_BEST_EFFORT')
        steps.append('CLEAN_SHUTDOWN')
        return ShutdownReport(tuple(steps),True,outbox_ok,snap)
