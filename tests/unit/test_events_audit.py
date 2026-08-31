import pytest
from app.core.events import DomainEvent,EventReplayer,ReplayError
from app.core.audit import AuditChain

def test_event_hash_stable():
    e=DomainEvent('X','a',{'b':1}); assert len(e.payload_hash)==64; assert e.record()['payload_hash']==e.payload_hash
def test_replay_sequence():
    es=[DomainEvent('ADD','a',{'n':1},sequence=1),DomainEvent('ADD','a',{'n':2},sequence=2)]
    r=EventReplayer({'ADD':lambda s,e:(s or 0)+e.payload['n']}); assert r.replay(es,0)==3
def test_replay_sorts_input():
    es=[DomainEvent('ADD','a',{'n':2},sequence=2),DomainEvent('ADD','a',{'n':1},sequence=1)]; r=EventReplayer({'ADD':lambda s,e:(s or 0)+e.payload['n']}); assert r.replay(es,0)==3
def test_replay_gap_hard_fails():
    with pytest.raises(ReplayError): EventReplayer({'ADD':lambda s,e:s}).replay([DomainEvent('ADD','a',{},sequence=2)])
def test_unknown_event_hard_fails():
    with pytest.raises(ReplayError): EventReplayer({}).replay([DomainEvent('UNKNOWN','a',{},sequence=1)])
def test_audit_chain_verifies():
    a=AuditChain(); a.append('admin','LIVE_DISABLE','account:1','c1','safety'); a.append('system','ORDER_INTENT','order:1','c2','signal'); assert a.verify()
def test_audit_tamper_detected():
    a=AuditChain(); a.append('admin','A','o','c','r'); object.__setattr__(a.entries[0],'reason','tampered'); assert not a.verify()

def test_domain_event_record_contains_required_audit_and_replay_fields():
    e = DomainEvent('ORDER_UPDATED', 'order-1', {'status': 'ACK'}, sequence=7, causation_id='cause-1')
    record = e.record()
    required = {
        'event_id', 'event_type', 'schema_version', 'aggregate_id', 'correlation_id',
        'causation_id', 'sequence', 'event_time', 'received_at', 'producer_version',
        'payload_hash', 'payload'
    }
    assert required <= set(record)
    assert record['causation_id'] == 'cause-1'
    assert len(record['payload_hash']) == 64
