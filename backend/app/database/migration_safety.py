from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MigrationSafetyPlan:
    migration_id:str
    expand_contract:bool
    pre_migration_checkpoint:str
    estimated_lock_seconds:float
    max_lock_seconds:float
    online_index:bool
    backfill_batch_size:int
    backfill_pause_ms:int
    observability_metrics:tuple[str,...]
    rollback_documented:bool
    def validate(self):
        if not self.migration_id.strip(): raise ValueError('migration id required')
        if not self.expand_contract: raise ValueError('production migration must use expand/contract by default')
        if not self.pre_migration_checkpoint.strip(): raise ValueError('pre-migration backup/checkpoint required')
        if self.estimated_lock_seconds > self.max_lock_seconds: raise ValueError('estimated lock exceeds production lock budget')
        if self.backfill_batch_size < 1 or self.backfill_pause_ms < 0: raise ValueError('invalid backfill throttling')
        required={'migration_duration_seconds','migration_errors_total','backfill_rows_total','db_lock_wait_seconds'}
        if not required.issubset(self.observability_metrics): raise ValueError('migration observability incomplete')
        if not self.rollback_documented: raise ValueError('rollback plan required')
        return self
