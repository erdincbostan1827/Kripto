from datetime import datetime,timezone
import random
import pytest
from app.core.event_schema import EventSchema,EventSchemaRegistry,EventSchemaError,EventMigrationRequired
from app.core.retry import RetryPolicy
from app.monitoring.watchdog import HeartbeatSigner,heartbeat_payload,ExternalWatchdog
from app.core.incident import IncidentManager

def test_event_schema_registry_tolerates_additive_unknown_fields_but_requires_semantics():
    r=EventSchemaRegistry(); r.register(EventSchema('fill',1,frozenset({'order_id','qty'}),frozenset({'fee'})))
    assert r.validate('fill',1,{'order_id':'o1','qty':'1','future_field':'ok'})['future_field']=='ok'
    with pytest.raises(EventSchemaError): r.validate('fill',1,{'qty':'1'})
    with pytest.raises(EventMigrationRequired): r.validate('fill',2,{'order_id':'o1','qty':'1'})

def test_event_schema_upcaster_requires_registered_latest_schema():
    r=EventSchemaRegistry(); r.register(EventSchema('order',2,frozenset({'id','client_order_id'})))
    r.register_upcaster('order',1,lambda p:{**p,'client_order_id':'legacy-'+p['id']})
    v,p=r.migrate_to_latest('order',1,{'id':'1'}); assert v==2 and p['client_order_id']=='legacy-1'

def test_retry_policy_is_bounded_classified_and_jittered():
    p=RetryPolicy(max_attempts=3,base_seconds=1,max_seconds=4,jitter_fraction=.5); now=datetime(2026,1,1,tzinfo=timezone.utc)
    d=p.decide(TimeoutError('temporary'),1,now,random.Random(1)); assert d.retryable and d.next_attempt_at>now
    assert not p.decide(ValueError('schema invalid'),1,now).retryable
    assert p.decide(ConnectionError('down'),3,now).reason=='RETRY_BUDGET_EXHAUSTED'

def test_external_watchdog_validates_signature_freshness_data_stream_and_backlog():
    s=HeartbeatSigner(b'0123456789abcdef0123456789abcdef'); now=1000.0
    p=heartbeat_payload('ACTIVE','2026-01-01T00:00:00Z',2,last_market_data_age=.2,private_stream_age=.3); p['timestamp']=now
    w=ExternalWatchdog(s); assert w.assess(p,s.sign(p),now=now).healthy
    bad=dict(p,last_market_data_age=99,private_stream_age=99,outbox_backlog=999)
    a=w.assess(bad,s.sign(bad),now=now); assert not a.healthy and {'MARKET_DATA_STALE','PRIVATE_STREAM_STALE','OUTBOX_BACKLOG_HIGH'}<=set(a.reasons)
    assert 'INVALID_HEARTBEAT_SIGNATURE' in w.assess(p,'0'*64,now=now).reasons

def test_typed_sev1_incident_requires_complete_recovery_evidence():
    m=IncidentManager(); x=m.open('SEV1','account:a/symbol:BTCUSDT','HALT_NEW_RISK','HALTED',['audit:1'],incident_type='ORPHAN_ORDER',correlation_ids=['c1'])
    assert x.detected_at and x.correlation_ids==['c1']
    with pytest.raises(PermissionError): m.resolve(x.incident_id,'checked',{'reconciliation_pass':True})
    y=m.resolve(x.incident_id,'checked',{'reconciliation_pass':True,'risk_state_verified':True,'evidence_preserved':True}); assert y.resolved_at

def test_secondary_alert_channels_are_transport_injected_and_fail_closed():
    from app.monitoring.channels import WebhookAlertChannel,EmailAlertChannel
    class R:
        def raise_for_status(self): pass
    class C:
        def post(self,url,json,timeout): assert url=='https://alerts.example/hook' and 'message' in json; return R()
    assert WebhookAlertChannel('https://alerts.example/hook',client=C()).send('sev1').delivered
    with pytest.raises(ValueError): WebhookAlertChannel('http://alerts.example/hook')
    sent=[]; assert EmailAlertChannel(lambda to,sub,body:sent.append((to,sub,body)),'ops@example.com').send('sev1').delivered and sent

def test_dead_letter_schema_contains_forensic_retry_fields():
    from app.database.models import DeadLetterRow
    cols=set(DeadLetterRow.__table__.columns.keys())
    assert {'original_event_id','event_type','schema_version','payload_hash','failure_reason','correlation_id','attempts','consumer_version','first_failed_at','last_failed_at','resolution_state'}<=cols
