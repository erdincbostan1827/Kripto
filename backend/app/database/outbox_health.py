from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OutboxHealth:
    committed_unpublished: int
    replayable_committed: int
    critical_alert_delivery_failures: int
    dead_letter_open: int
    @property
    def degraded(self)->bool:
        return self.critical_alert_delivery_failures>0 or self.dead_letter_open>0
    def assert_no_event_loss(self)->None:
        if self.committed_unpublished<0 or self.replayable_committed<0: raise ValueError('invalid counters')
        if self.replayable_committed < self.committed_unpublished:
            raise RuntimeError('committed event not replayable')
