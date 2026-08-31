from decimal import Decimal
import pytest
from app.execution.race_recovery import ReplaceRaceEvidence,resolve_replace_race,UnknownOutcomeEvidence,resolve_unknown_outcome
from app.auth.recovery_policy import RecoveryGrantStore,RecoveryPolicy
from app.core.environment_isolation import EnvironmentBoundary,validate_environment_isolation


def test_replace_race_detects_old_fill_and_overlapping_orders():
    d=resolve_replace_race(ReplaceRaceEvidence('old','new','PARTIALLY_FILLED','NEW',Decimal('1'),Decimal('0.5')))
    assert not d.safe and d.halt_new_risk
    assert 'OLD_ORDER_FILLED_DURING_REPLACE' in d.reasons
    assert 'OVERLAPPING_LIVE_ORDERS' in d.reasons


def test_replace_race_ack_loss_is_unknown_until_reconciled():
    d=resolve_replace_race(ReplaceRaceEvidence('old',None,None,None,ack_lost=True))
    assert d.action=='RECONCILE_OPEN_ORDERS_AND_FILLS' and 'ACK_LOST_DURING_DISCONNECT' in d.reasons


def test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews():
    assert resolve_unknown_outcome(UnknownOutcomeEvidence('c',None,None,Decimal('2'),Decimal('2'))).resolved_status=='FILLED'
    p=resolve_unknown_outcome(UnknownOutcomeEvidence('c',None,None,Decimal('1'),Decimal('2')))
    assert p.resolved_status=='PARTIALLY_FILLED' and not p.manual_review
    u=resolve_unknown_outcome(UnknownOutcomeEvidence('c',None,None,Decimal('0'),Decimal('2')))
    assert u.manual_review and u.resolved_status=='UNKNOWN'


def test_privileged_recovery_requires_mfa_and_admin_approval_and_is_one_time():
    now=[1000.0]
    s=RecoveryGrantStore(RecoveryPolicy(token_ttl_seconds=60),clock=lambda:now[0])
    with pytest.raises(PermissionError): s.issue('u','trader')
    with pytest.raises(PermissionError): s.issue('a','admin',mfa_verified=True)
    raw=s.issue('a','admin',mfa_verified=True,approved_by='second-admin')
    grant=s.consume(raw,'a'); assert grant.used and grant.approved_by=='second-admin'
    with pytest.raises(PermissionError): s.consume(raw,'a')


def test_recovery_token_expires_and_wrong_principal_fails_closed():
    now=[1000.0]; s=RecoveryGrantStore(RecoveryPolicy(token_ttl_seconds=10),clock=lambda:now[0])
    raw=s.issue('viewer-1','viewer')
    with pytest.raises(PermissionError): s.consume(raw,'viewer-2')
    now[0]=1011
    with pytest.raises(PermissionError): s.consume(raw,'viewer-1')


def test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital():
    dev=EnvironmentBoundary('DEV','db-dev','redis-dev','key-dev','hook-dev','enc-dev')
    stg=EnvironmentBoundary('STAGING','db-stg','redis-stg','key-stg','hook-stg','enc-stg')
    prod=EnvironmentBoundary('PROD','db-prod','redis-prod','key-prod','hook-prod','enc-prod',True)
    assert validate_environment_isolation(dev,stg,prod)==()
    bad=EnvironmentBoundary('STAGING','db-prod','redis-stg','key-prod','hook-stg','enc-stg',True)
    issues=validate_environment_isolation(dev,bad,prod)
    assert any('SHARED_DATABASE_NAMESPACE' in x for x in issues)
    assert any('SHARED_EXCHANGE_KEY_IDENTITY' in x for x in issues)
    assert 'NON_PROD_REAL_CAPITAL_FORBIDDEN:STAGING' in issues

from app.exchange.private_stream import parse_user_event,PrivateStreamProjector,FuturesPositionUpdate
from app.risk.ledger_policy import AccountingEvidence,LedgerLifecyclePolicy,validate_accounting_evidence,validate_ledger_lifecycle

def test_private_stream_account_update_carries_position_and_balance_truth():
    e=parse_user_event({'e':'ACCOUNT_UPDATE','E':123,'a':{'B':[{'a':'USDT','wb':'100.5'}],'P':[{'s':'BTCUSDT','pa':'0.25'}]}})
    assert isinstance(e,FuturesPositionUpdate) and e.positions['BTCUSDT']==Decimal('0.25')
    p=PrivateStreamProjector(); r=p.project(e)
    assert r.classification=='KNOWN_POSITION_SNAPSHOT' and p.positions['BTCUSDT']==Decimal('0.25')


def test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy():
    good=AccountingEvidence('o1','f1','sig-abc',fee=Decimal('1'),funding=Decimal('2'),realized_pnl=Decimal('3'),unrealized_pnl=Decimal('4'))
    assert validate_accounting_evidence(good).ok
    bad=AccountingEvidence('o1',None,None,funding=Decimal('2'),transfer_amount=Decimal('10'))
    v=validate_accounting_evidence(bad)
    assert not v.ok and 'FILL_REFERENCE_REQUIRED_FOR_REALIZED_ACTIVITY' in v.reasons and 'MANUAL_TRANSFER_RECONCILIATION_REQUIRED' in v.reasons
    assert validate_ledger_lifecycle(LedgerLifecyclePolicy()).ok
    assert not validate_ledger_lifecycle(LedgerLifecyclePolicy(timescaledb_required=True)).ok

from app.universe.risk_context import classify_asset_risk,market_breadth
from app.monitoring.multiasset_metrics import BoundedMetricRegistry

def test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls():
    n=classify_asset_risk(listing_age_days=5,volatility_ratio=Decimal('1'),liquidity_score=Decimal('1'))
    assert n.risk_class=='NEW_LISTING' and n.paper_only and n.manual_confirmation and n.max_position_multiplier<1 and n.min_edge_multiplier>1
    v=classify_asset_risk(listing_age_days=100,volatility_ratio=Decimal('1'),liquidity_score=Decimal('1'),venue_healthy=False)
    assert v.risk_class=='VENUE_RISK' and v.no_trade
    r=classify_asset_risk(listing_age_days=100,volatility_ratio=Decimal('1'),liquidity_score=Decimal('1'),restricted=True)
    assert r.no_trade and r.risk_class=='RESTRICTED'


def test_market_breadth_uses_point_in_time_universe_and_cross_asset_context():
    rows=[
      {'symbol':'BTCUSDT','return':'0.02','realized_volatility':'0.03','above_ma':True,'momentum':'0.04'},
      {'symbol':'ETHUSDT','return':'-0.01','realized_volatility':'0.05','above_ma':False,'momentum':'-0.02'},
      {'symbol':'SOLUSDT','return':'0.03','realized_volatility':'0.08','above_ma':True,'momentum':'0.06'},
    ]
    b=market_breadth(rows,universe_version='u-2026-08-28T00:00Z')
    assert b.advancers_ratio==Decimal(2)/Decimal(3) and b.btc_leadership==Decimal('0.02') and b.altcoin_breadth==1
    assert b.dispersion>=0 and b.cross_sectional_momentum_dispersion>=0
    with pytest.raises(ValueError): market_breadth(rows,universe_version='')


def test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields():
    m=BoundedMetricRegistry(max_points=3,max_symbol_labels=2)
    m.observe('websocket_shards',2,exchange='binance')
    m.observe('symbol_data_latency',10,symbol='BTCUSDT')
    m.observe('portfolio_concentration','0.4')
    m.observe('symbol_slippage','2.5',symbol='ETHUSDT')
    assert len(m.points)==3
    with pytest.raises(OverflowError): m.observe('symbol_order_reject_rate','0.1',symbol='SOLUSDT')

from datetime import datetime,timezone
from app.universe.lifecycle import AssetLifecycleManager,AssetLifecycleEvent

def test_asset_lifecycle_manager_versions_warns_revalidates_and_never_auto_transfers():
    m=AssetLifecycleManager(); now=datetime.now(timezone.utc)
    listing=m.record(AssetLifecycleEvent('btc','BTCUSDT','SCHEDULED_LISTING',now,'exchangeInfo'))
    assert listing.warn_user and listing.verify_venue_rules and not listing.allow_new_risk and not listing.automatic_transfer_withdrawal
    renamed=m.record(AssetLifecycleEvent('btc','XBTUSDT','TOKEN_RENAME',now,'exchangeNotice',{'old':'BTCUSDT'}))
    assert renamed.mapping_version==2 and 'VERSIONED_MAPPING_CHANGE' in renamed.reasons
    delisted=m.record(AssetLifecycleEvent('btc','XBTUSDT','DELISTING',now,'exchangeNotice'))
    assert delisted.reducing_only and not delisted.allow_new_risk and delisted.mode=='EXIT_OR_REDUCING_ONLY'
    assert len(m.history('btc'))==3


def test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes():
    m=AssetLifecycleManager(); now=datetime.now(timezone.utc)
    for typ in ('TRADING_ENABLED','TRADING_DISABLED','SUSPENSION','QUOTE_PAIR_REMOVAL','REDENOMINATION','CONTRACT_MIGRATION','CHAIN_MIGRATION','HARD_FORK','TICKER_CHANGE','MERGE_SPLIT_REBASE'):
        d=m.record(AssetLifecycleEvent('a','AAAUSDT',typ,now,'venue'))
        assert d.warn_user and d.verify_venue_rules and not d.automatic_transfer_withdrawal

from app.universe.ranking import CrossSectionalRankInput,rank_cross_sectional

def test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality():
    a=CrossSectionalRankInput('AAA',0.08,0.9,0.9,0.9,2,2.5,0.8,0.9,0.8,0.95,100)
    b=CrossSectionalRankInput('BBB',0.02,0.5,0.5,0.4,15,1.2,0.5,0.5,0.2,0.5,50)
    c=CrossSectionalRankInput('CCC',0.2,0.99,1,1,0,5,1,1,1,1,200,eligible=False,blocking_reasons=('RISK_BLOCKED',))
    out=rank_cross_sectional([b,c,a])
    assert out[0].symbol=='AAA' and out[0].rank==1 and out[0].rank_score>out[1].rank_score
    blocked=next(x for x in out if x.symbol=='CCC')
    assert not blocked.eligible and blocked.blocking_reasons==('RISK_BLOCKED',)
    assert out[0].data_quality_score==0.95 and out[0].correlation_penalty>=0 and out[0].liquidity_penalty>=0
