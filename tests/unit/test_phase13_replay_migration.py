import pytest
from app.core.events import DomainEvent,EventReplayer,create_replay_checkpoint,verify_replay_checkpoint,ReplayError
from app.database.migration_safety import MigrationSafetyPlan


def test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift():
    events=[DomainEvent('inc','acct',{'n':1},sequence=1),DomainEvent('inc','acct',{'n':2},sequence=2)]
    r=EventReplayer({'inc':lambda state,e:(state or 0)+e.payload['n']})
    state=r.replay(events,0)
    cp=create_replay_checkpoint(state,events)
    assert verify_replay_checkpoint(cp,state,events)
    assert not verify_replay_checkpoint(cp,state+1,events)
    tampered=[events[0],DomainEvent('inc','acct',{'n':999},sequence=2)]
    assert not verify_replay_checkpoint(cp,state,tampered)

def test_replay_checkpoint_rejects_sequence_gap():
    with pytest.raises(ReplayError): create_replay_checkpoint({},[DomainEvent('x','a',{},sequence=2)])

def test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback():
    p=MigrationSafetyPlan('0004_large_table',True,'backup://checkpoint-123',1.2,2.0,True,1000,25,
      ('migration_duration_seconds','migration_errors_total','backfill_rows_total','db_lock_wait_seconds'),True)
    assert p.validate() is p
    with pytest.raises(ValueError): MigrationSafetyPlan('0004',True,'',1,2,True,100,0,('migration_duration_seconds',),True).validate()
    with pytest.raises(ValueError): MigrationSafetyPlan('0004',True,'cp',5,2,True,100,0,('migration_duration_seconds','migration_errors_total','backfill_rows_total','db_lock_wait_seconds'),True).validate()
