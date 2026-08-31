from pathlib import Path
from datetime import date,timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.monitoring.health import HealthService,ProbeResult
from app.auth.password_policy import PasswordHashPolicy
from app.core.security import hash_password,password_hash_needs_upgrade,verify_password
from app.data.providers import DataProviderRegistry,DataProviderPolicy
from app.api.versioning import ApiVersionPolicy,ApiVersionRegistry,DeprecationNotice
from app.release.provenance import ReleaseAttestation
from app.release.supply_chain import collect_supply_chain_evidence
from app.release.runtime_readiness import RuntimeReadinessEvidence


def test_phase22_health_and_ready_are_separate_and_readiness_fails_closed():
    h=HealthService({'database':lambda:ProbeResult('UP'),'redis':lambda:ProbeResult('DOWN')},fail_closed=True,required_components=('database','redis'))
    c=TestClient(create_app(health_service=h))
    health=c.get('/health'); ready=c.get('/ready')
    assert health.status_code==200 and health.json()['database']=='UP' and health.json()['redis']=='DOWN'
    assert ready.status_code==503 and ready.text=='not ready'


def test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract():
    assert PasswordHashPolicy().validate().upgrade_on_login
    with pytest.raises(ValueError): PasswordHashPolicy(memory_cost_kib=8192).validate()
    encoded=hash_password('correct-horse-battery')
    assert verify_password(encoded,'correct-horse-battery') and not password_hash_needs_upgrade(encoded)


def test_phase22_provider_registry_enforces_license_retention_provenance_contract():
    r=DataProviderRegistry(); p=DataProviderPolicy('binance-public-v1','market','https://binance.com','exchange terms',False,'required','raw 30d','weight based','commercial allowed','UTC milliseconds','exchange revision semantics','market-data','1.0')
    r.register(p); snap=r.snapshot()
    assert snap['providers'][0]['provider_id']=='binance-public-v1' and len(snap['sha256'])==64
    with pytest.raises(PermissionError): r.assert_usage_allowed('binance-public-v1',redistribute=True)


def test_phase22_api_deprecation_contract_has_warning_window_successor_and_breaking_criteria():
    pol=ApiVersionPolicy(compatibility_window_days=180,deprecation_warning_days=90)
    reg=ApiVersionRegistry(pol); today=date(2026,8,28)
    reg.deprecate(DeprecationNotice('v1',today,today+timedelta(days=100),'v2','auth contract change'))
    h=reg.headers('v1',today)
    assert h['Deprecation']=='true' and 'successor-version' in h['Link']
    assert reg.is_breaking_change(changes_auth=True)


def test_phase22_release_attestation_requires_all_production_provenance_fields_and_is_tamper_fingerprinted():
    a=ReleaseAttestation('r','abc','tree','ci-1','2026-08-28T00:00:00Z','lock','sbom','sha256:img','front','0003','arch','req','tests')
    a.assert_production_complete(); fp=a.fingerprint(); assert len(fp)==64
    bad=ReleaseAttestation('r','UNAVAILABLE','tree','LOCAL-NOT-CI','x',None,None,'NOT_BUILT',None,'0003','arch','req','tests')
    assert {'git_commit_sha','ci_run_id','dependency_lock_hash','sbom_hash','container_digest','frontend_artifact_hash'} <= set(bad.production_blockers())


def test_phase22_supply_chain_evidence_is_explicit_and_never_promotes_missing_tools_or_artifacts():
    root=Path(__file__).resolve().parents[2]
    e=collect_supply_chain_evidence(root)
    assert isinstance(e.tool_availability,dict) and len(e.fingerprint())==64
    assert 'PYTHON_LOCK_MISSING' in e.production_blockers()
    assert 'VULNERABILITY_SCAN_MISSING' in e.production_blockers()


def test_phase22_runtime_readiness_requires_health_db_redis_exchange_clock_reconciliation_and_outbox():
    ok=RuntimeReadinessEvidence(True,True,True,True,True,True,True,True); ok.assert_ready()
    bad=RuntimeReadinessEvidence(True,False,True,False,True,True,False,True)
    assert {'NOT_READY_FOR_NEW_RISK','REDIS_NOT_OK','RECONCILIATION_NOT_OK'} <= set(bad.blockers())
    with pytest.raises(RuntimeError): bad.assert_ready()

from app.exchange.base import ExchangeAdapter
from app.recovery.policy import BackupRecoveryPolicy,RestoreDrillEvidence
from app.backtest.execution_model import conservative_exit_long,conservative_limit_fill
from app.core.enums import TradingMode
from app.database.models import Base


def test_phase22_exchange_architecture_is_adapter_based_and_extensible_without_binance_coupling():
    abstract={name for name,val in ExchangeAdapter.__dict__.items() if getattr(val,'__isabstractmethod__',False)}
    assert {'get_ticker','get_order_book','get_balance','get_positions','get_open_orders','get_klines','submit_order','cancel_order','get_order','list_markets','get_symbol_filters','get_capabilities','get_server_time'} <= abstract


def test_phase22_modes_contract_keeps_paper_as_safe_default_and_explicit_modes():
    values={m.value for m in TradingMode}
    assert {'BACKTEST','PAPER','TESTNET','LIVE'} <= values


def test_phase22_backup_dr_policy_is_explicit_but_restore_drill_evidence_cannot_be_faked():
    p=BackupRecoveryPolicy(15,60,15,30); p.validate()
    incomplete=RestoreDrillEvidence(False,False,False,False,False,False,None)
    with pytest.raises(ValueError): incomplete.assert_complete()


def test_phase22_backtest_intrabar_model_is_conservative_on_ambiguous_stop_take_profit_and_limit_touch():
    d=conservative_exit_long(bar_open='100',bar_high='111',bar_low='89',stop='90',tp='110')
    assert d.reason=='STOP_CONSERVATIVE' and d.price is not None
    touch=conservative_limit_fill('BUY','100','101','102','100',require_penetration=True)
    assert not touch.filled and touch.reason=='TOUCH_NOT_GUARANTEED'


def test_phase22_database_schema_contract_has_financial_and_operational_tables_registered():
    tables=set(Base.metadata.tables)
    assert {'users','exchange_accounts','orders','fills','ledger_entries','system_events','health_checks','universe_snapshots','incidents'} <= tables
from app.backtest.execution_model import IntrabarEvidence,resolve_long_stop_take_profit

def test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative():
    kw=dict(bar_open='100',bar_high='111',bar_low='89',stop='90',tp='110')
    assert resolve_long_stop_take_profit(**kw,evidence=IntrabarEvidence(lower_timeframe_order='TP_FIRST',tick_trade_order='STOP_FIRST')).reason=='TAKE_PROFIT_LOWER_TIMEFRAME_EVIDENCE'
    assert resolve_long_stop_take_profit(**kw,evidence=IntrabarEvidence(tick_trade_order='TP_FIRST',orderbook_order='STOP_FIRST')).reason=='TAKE_PROFIT_TICK_TRADE_EVIDENCE'
    assert resolve_long_stop_take_profit(**kw,evidence=IntrabarEvidence(orderbook_order='TP_FIRST')).reason=='TAKE_PROFIT_ORDER_BOOK_EVIDENCE'
    assert resolve_long_stop_take_profit(**kw).reason=='STOP_CONSERVATIVE'
