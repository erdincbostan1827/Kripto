from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeReadinessEvidence:
    health_ok:bool
    ready_for_new_risk:bool
    database_ok:bool
    redis_ok:bool
    exchange_ok:bool
    clock_ok:bool
    reconciliation_ok:bool
    outbox_ok:bool

    def blockers(self)->tuple[str,...]:
        checks={
            'HEALTH_NOT_OK':self.health_ok,
            'NOT_READY_FOR_NEW_RISK':self.ready_for_new_risk,
            'DATABASE_NOT_OK':self.database_ok,
            'REDIS_NOT_OK':self.redis_ok,
            'EXCHANGE_NOT_OK':self.exchange_ok,
            'CLOCK_NOT_OK':self.clock_ok,
            'RECONCILIATION_NOT_OK':self.reconciliation_ok,
            'OUTBOX_NOT_OK':self.outbox_ok,
        }
        return tuple(k for k,v in checks.items() if not v)

    def assert_ready(self)->None:
        b=self.blockers()
        if b: raise RuntimeError('runtime readiness blocked: '+','.join(b))
