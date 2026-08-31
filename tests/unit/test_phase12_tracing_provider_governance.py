import random,pytest
from app.monitoring.tracing import BoundedLatencyTracer,LATENCY_STAGES
from app.data.providers import DataProviderRegistry,DataProviderPolicy

def test_latency_tracer_decomposes_required_stages_and_is_bounded():
    t=BoundedLatencyTracer(sample_rate=1,max_records=2,rng=random.Random(1))
    r=t.start('x')
    for i,s in enumerate(LATENCY_STAGES): t.observe(r,s,10+i,10+i+.001)
    d=t.decomposition(r); assert not d['missing_stages'] and len(d['latencies_ms'])==len(LATENCY_STAGES) and d['total_observed_ms']>0
    t.start('y'); t.start('z'); assert len(t.records)==2 and [x.trace_id for x in t.records]==['y','z']

def test_latency_tracer_sampling_can_disable_high_cardinality_storage_and_clock_regression_fails():
    t=BoundedLatencyTracer(sample_rate=0,max_records=1,rng=random.Random(1)); r=t.start('secret-symbol-order-id'); assert not r.sampled and not t.records
    t2=BoundedLatencyTracer(sample_rate=1,max_records=1,rng=random.Random(1)); r2=t2.start('t')
    with pytest.raises(RuntimeError): t2.observe(r2,'exchange_ack',2,1)

def policy():
    return DataProviderPolicy('binance_spot_public','market_data','https://api.binance.com','Binance Terms',False,'source attribution','retain per policy','documented exchange limits','commercial use subject to TOS','UTC exchange timestamps','exchange data may be corrected by source','market-data','v1')

def test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash():
    r=DataProviderRegistry(); r.register(policy()); a=r.snapshot(); b=r.snapshot(); assert a['sha256']==b['sha256'] and a['providers'][0]['provider_id']=='binance_spot_public'

def test_provider_registry_enforces_redistribution_and_policy_changes_fail_closed():
    r=DataProviderRegistry(); r.register(policy())
    with pytest.raises(PermissionError): r.assert_usage_allowed('binance_spot_public',redistribute=True)
    changed=DataProviderPolicy(**{**policy().__dict__,'adapter_version':'v2'})
    with pytest.raises(ValueError): r.register(changed)
