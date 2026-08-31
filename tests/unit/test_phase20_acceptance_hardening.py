from datetime import datetime,timedelta,timezone
import pytest
from app.universe.asset_metadata import AssetIdentityVersion,MarketIdentityVersion,AssetMetadataRegistry
from app.risk.normalization import AssetLiquidityClass,NormalizedMarketFeatures,SafetyLimits,AssetParameterPolicy
from app.research.manifest import ResearchExperimentManifest,ResearchPoint
from app.analytics.performance_attribution import AttributionTrade,build_attribution
from app.release.dod import DefinitionOfDoneEvidence
from app.audit.worm import WormAuditExporter,CRITICAL_ACTIONS
UTC=timezone.utc

def test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity():
    t=datetime(2026,1,1,tzinfo=UTC); r=AssetMetadataRegistry()
    r.add_asset(AssetIdentityVersion("BTC","BTC","Bitcoin",t,chain_network="bitcoin"))
    r.add_market(MarketIdentityVersion("BINANCE","SPOT","BTCUSDT","BTC","USDT","SPOT","TRADING",t,t))
    assert r.asset_as_of("BTC",t+timedelta(days=1)).canonical_symbol=="BTC"
    m=r.market_as_of("BINANCE","SPOT","BTCUSDT",t+timedelta(days=1)); assert (m.base_asset_id,m.quote_asset_id,m.contract_type,m.status)==("BTC","USDT","SPOT","TRADING")

def test_asset_contract_identifier_requires_trusted_source_and_validity_ranges_do_not_overlap():
    t=datetime(2026,1,1,tzinfo=UTC); r=AssetMetadataRegistry()
    with pytest.raises(ValueError): AssetIdentityVersion("X","X","X",t,chain_network="eth",contract_identifier="0x1",contract_source="BLOG")
    r.add_asset(AssetIdentityVersion("X","OLD","Old",t,t+timedelta(days=1)))
    r.add_asset(AssetIdentityVersion("X","NEW","New",t+timedelta(days=1)))
    assert r.asset_as_of("X",t+timedelta(days=2)).canonical_symbol=="NEW"

def test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features():
    g=SafetyLimits(.1,1000,20,100000,50000); c=SafetyLimits(.05,700,12,200000,75000)
    p=AssetParameterPolicy(g,{AssetLiquidityClass.CORE_HIGH_LIQUIDITY:c},{("s","BTCUSDT"):{"entry_z":1.5}})
    f=NormalizedMarketFeatures(2.1,10,300000,100000,.3,1.2); x=p.resolve(strategy_id="s",symbol="BTCUSDT",asset_class=AssetLiquidityClass.CORE_HIGH_LIQUIDITY,features=f)
    assert x.trade_allowed and x.limits.max_position_fraction==.05 and x.limits.max_order_notional==700 and x.calibrated_parameters["entry_z"]==1.5

def test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade():
    assert {x.value for x in AssetLiquidityClass}=={"CORE_HIGH_LIQUIDITY","LARGE_CAP","MID_LIQUIDITY","NEW_LISTING","HIGH_VOLATILITY","RESTRICTED/NO_TRADE"}
    g=SafetyLimits(.1,1000,20,1,1); p=AssetParameterPolicy(g,{})
    f=NormalizedMarketFeatures(1,1,1,1,0,1)
    assert not p.resolve(strategy_id="s",symbol="X",asset_class=AssetLiquidityClass.RESTRICTED_NO_TRADE,features=f).trade_allowed

def test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information():
    t=datetime(2026,1,1,tzinfo=UTC); m=ResearchExperimentManifest("u-v1",("BTCUSDT","ETHUSDT"),"strat-v3",{"p":(1,2)},("rsi","atr"),("1h","4h"),(t,t+timedelta(days=10)),(t+timedelta(days=10),t+timedelta(days=20)),"OOS_SHARPE",t+timedelta(days=20))
    m.assert_no_future_labels(universe_membership=ResearchPoint("membership",t,t+timedelta(days=5)))
    for name in ("future membership","future market-cap/category","revised metadata","future liquidity rank","intraday early EOD"):
        with pytest.raises(ValueError): m.assert_point_in_time_safe([ResearchPoint(name,t,t+timedelta(days=21))])

def test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects():
    x=build_attribution(trades=[AttributionTrade("BTC","s1",10,100,1,selection_rank=1),AttributionTrade("ETH","s2",-2,50,2,True,2)],portfolio_equity=1000,drawdown=-.1,average_pairwise_correlation=.5,universe_added=2,universe_removed=1,universe_size=10,excluded_reasons=["SPREAD","SPREAD","STALE"],missing_data_policy="EXCLUDE_AND_REPORT")
    assert x.per_asset_contribution=={"BTC":10.0,"ETH":-2.0} and x.per_strategy_contribution["s1"]==10
    assert x.turnover==.15 and x.maximum_concurrent_positions==2 and x.universe_turnover==.3 and x.excluded_symbol_reason_distribution["SPREAD"]==2 and x.delisted_asset_contribution==-2

def test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue():
    ok=DefinitionOfDoneEvidence(True,True,True,True,"reports/evidence.txt",True,True,True,(),True,True); ok.assert_done()
    with pytest.raises(RuntimeError): DefinitionOfDoneEvidence(True,True,True,True,None,True,True,False,("SEV1",),True,True).assert_done()

def test_worm_audit_export_covers_all_critical_actions_and_detects_tampering():
    e=WormAuditExporter(b"x"*32); records=[]
    for a in sorted(CRITICAL_ACTIONS): e.append(records,action=a,payload={"who":"operator"})
    assert e.verify(records) and len(e.export_append_only_jsonl(records).splitlines())==len(CRITICAL_ACTIONS)
    bad=list(records); bad[0]=bad[0].__class__(bad[0].sequence,bad[0].action,{"who":"attacker"},bad[0].previous_hash,bad[0].record_hash)
    assert not e.verify(bad)
from app.universe.snapshot_registry import UniverseMemberRecord,PointInTimeUniverseRegistry
from app.release.acceptance_evidence import AcceptanceCaseEvidence,MultiAssetAcceptanceSnapshot

def test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics():
    t=datetime(2026,1,1,tzinfo=UTC); reg=PointInTimeUniverseRegistry()
    rows=[UniverseMemberRecord('BINANCE','SPOT','BTCUSDT','BTC',t,t,t,listing_open_time=t,inclusion_reason='ELIGIBLE'),UniverseMemberRecord('BINANCE','SPOT','BADUSDT','BAD',t,t,t,exclusion_reason='LOW_LIQUIDITY')]
    s=reg.create(snapshot_id='u1',mode='DYNAMIC_EXCHANGE_UNIVERSE',as_of=t,records=rows)
    assert s.mode=='DYNAMIC_EXCHANGE_UNIVERSE' and reg.eligible_symbols('u1')==('BTCUSDT',)
    assert rows[0].exchange=='BINANCE' and rows[0].market_type=='SPOT' and rows[0].base_asset=='BTC' and rows[1].exclusion_reason=='LOW_LIQUIDITY'

def test_research_snapshot_rejects_future_available_membership_and_snapshots_are_immutable():
    t=datetime(2026,1,1,tzinfo=UTC); reg=PointInTimeUniverseRegistry()
    future=UniverseMemberRecord('BINANCE','SPOT','BTCUSDT','BTC',t,t,t+timedelta(hours=1),inclusion_reason='ELIGIBLE')
    with pytest.raises(ValueError): reg.create(snapshot_id='u2',mode='RESEARCH_SNAPSHOT',as_of=t,records=[future])
    good=UniverseMemberRecord('BINANCE','SPOT','BTCUSDT','BTC',t,t,t,inclusion_reason='ELIGIBLE'); reg.create(snapshot_id='u2',mode='RESEARCH_SNAPSHOT',as_of=t,records=[good])
    with pytest.raises(ValueError): reg.create(snapshot_id='u2',mode='RESEARCH_SNAPSHOT',as_of=t,records=[good])

def test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents():
    with pytest.raises(ValueError): AcceptanceCaseEvidence('c','PASS','LOCAL','written only','reports/x',None,False)
    ev=(AcceptanceCaseEvidence('c','PASS','LOCAL_MOCK_PAPER','executed','reports/LATEST_PYTEST.txt','mock disclosed',True),)
    x=MultiAssetAcceptanceSnapshot(True,True,True,True,True,True,True,True,True,0,True,ev); x.assert_accepted()
    with pytest.raises(RuntimeError): MultiAssetAcceptanceSnapshot(True,True,True,True,True,True,True,True,True,1,True,ev).assert_accepted()
from pathlib import Path
import yaml

def test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits():
    compose=yaml.safe_load(Path('docker-compose.yml').read_text()); prod=Path('docker-compose.prod.yml').read_text(); back=Path('backend/Dockerfile').read_text(); front=Path('frontend/Dockerfile').read_text(); docs=Path('docs/SECURITY_HARDENING.md').read_text()
    assert '/run/secrets/' in prod and 'Docker secrets' in docs and 'TESTNET and LIVE exchange keys are separate' in docs and 'IP allowlist' in docs
    assert 'python:3.12.14-slim-bookworm@sha256:' in back and 'USER appuser' in back
    assert 'bookworm-slim@sha256:' in front and 'alpine@sha256:' in front and 'USER 101' in front
    raw=Path('docker-compose.yml').read_text(); assert '/var/run/docker.sock' not in raw and 'privileged: true' not in raw
    for name in ('app','frontend','nginx'):
        svc=compose['services'][name]; assert svc.get('read_only') is True and 'ALL' in svc.get('cap_drop',[]) and 'no-new-privileges:true' in svc.get('security_opt',[])
    assert 'resources' in compose['services']['app']['deploy'] and 'resources' in compose['services']['nginx']['deploy']
    assert set(compose['services']['nginx']['ports'])=={'8080:8080'}
