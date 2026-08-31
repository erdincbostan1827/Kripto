from __future__ import annotations
from pathlib import Path
try:
    from scripts import database_migration_guard as migration
    from scripts import transactional_release_update as update
    from scripts.deployment_transaction_state import inspect
except ModuleNotFoundError:
    import database_migration_guard as migration
    import transactional_release_update as update
    from deployment_transaction_state import inspect

def recover_cross_transaction(*, active:Path, state_dir:Path, probe_command:list[str], cwd:Path, timeout_seconds:int=60)->dict:
    root=state_dir.resolve(); state=inspect(root)
    kinds={x['kind'] for x in state['active']}
    if not {'release_update','database_migration'}.issubset(kinds):
        return {'classification':'CROSS_TRANSACTION_RECOVERY','status':'NOT_REQUIRED','state':state}
    journal=migration._read_journal(root)
    observed=migration.probe_database_head(probe_command,cwd=cwd,timeout_seconds=timeout_seconds)
    if observed==journal['to_head']:
        return {'classification':'CROSS_TRANSACTION_RECOVERY','status':'BLOCKED_DATABASE_ADVANCED_APPLICATION_UNCOMMITTED','observed_head':observed,'safe_to_continue':False}
    if observed!=journal['from_head']:
        raise RuntimeError(f'CROSS_TRANSACTION_DATABASE_STATE_AMBIGUOUS:{observed}')
    migration._journal_path(root).unlink()
    recovered=update.recover_incomplete_update(active=active)
    after=inspect(root)
    if not after['safe_to_start_new_mutation']:
        raise RuntimeError(f'CROSS_TRANSACTION_RECOVERY_INCOMPLETE:{after}')
    return {'classification':'CROSS_TRANSACTION_RECOVERY','status':'RECOVERED_PRE_MIGRATION_UPDATE','observed_head':observed,'release_recovery':recovered,'safe_to_continue':True}
