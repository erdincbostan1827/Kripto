from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from app.exchange.capability_policy import from_binance_exchange_info
from app.execution.account_boundary import AccountLifecycleRecord
from app.monitoring.scanner_view import ScannerViewPreferences, apply_scanner_view, DEFAULT_COLUMNS, ADVANCED_COLUMNS
from app.release.final_evidence import FinalEvidenceBundle


def _symbol():
    return {'symbol':'BTCUSDT','orderTypes':['LIMIT','MARKET'],'ocoAllowed':True,'cancelReplaceAllowed':True,'maxNumOrders':17,'filters':[
        {'filterType':'PRICE_FILTER','tickSize':'0.01','minPrice':'0.01','maxPrice':'1000000'},
        {'filterType':'LOT_SIZE','stepSize':'0.00001','minQty':'0.00001','maxQty':'100'},
        {'filterType':'NOTIONAL','minNotional':'5','maxNotional':'1000000'},
    ]}

def test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits():
    p=from_binance_exchange_info(_symbol(),[{'rateLimitType':'REQUEST_WEIGHT','limit':6000}])
    assert p.oco_or_order_list and p.order_book_depth_supported and p.cancel_replace_supported
    assert p.precision_mode=='TICK_STEP_FILTERS'
    assert p.min_price==Decimal('0.01') and p.max_price==Decimal('1000000')
    assert p.max_open_orders==17 and p.exchange_rate_limits[0]['limit']==6000


def test_phase21_capability_profile_fails_closed_on_missing_or_invalid_filters():
    bad=_symbol(); bad['filters']=bad['filters'][1:]
    with pytest.raises(RuntimeError): from_binance_exchange_info(bad,[])
    bad=_symbol(); bad['filters'][0]['tickSize']='0'
    with pytest.raises(RuntimeError): from_binance_exchange_info(bad,[])


def test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace():
    created=datetime(2026,1,1,tzinfo=timezone.utc)
    a=AccountLifecycleRecord('acct',created,None,'RECONCILIATION_REQUIRED','bot-prod-acct','fp')
    assert a.client_order_id('intent# 42')=='bot-prod-acct-intent42'
    b=a.mark_reconciled(created+timedelta(seconds=1))
    assert b.status=='ACTIVE' and b.last_reconciled_at>created


def test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile():
    assert not set(ADVANCED_COLUMNS)&set(DEFAULT_COLUMNS)
    items=[{'symbol':'ETHUSDT','rank':2,'price':2,'signal':'BUY','score':1,'confidence':.7,'net_edge':.1,'block_reason':None,'data_age_seconds':1,'spread_bps':2},
           {'symbol':'BTCUSDT','rank':1,'price':1,'signal':'BUY','score':2,'confidence':.8,'net_edge':.2,'block_reason':None,'data_age_seconds':1,'spread_bps':1}]
    p=ScannerViewPreferences(visible_columns=('symbol','rank','spread_bps'),search='usdt',sort_by='rank',page_size=1,mobile=True,saved_view_name='risk-desk')
    r=apply_scanner_view(items,p)
    assert r.total==2 and r.rows[0]=={'symbol':'BTCUSDT','rank':1,'spread_bps':1}
    assert r.mobile_cards and r.page_size==1
    assert apply_scanner_view(list(reversed(items)),p).rows==r.rows


def test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet():
    e=FinalEvidenceBundle({'return':.1},{'fee_bps':20},{'delta':.02},None,('real PITR not run',),'abc','0.3.0-local-acceptance')
    assert e.blockers()==()
    assert 'TESTNET_VS_PAPER_NOT_TESTED' in e.production_blockers()
    assert 'UNRESOLVED_KNOWN_ISSUES' in e.production_blockers()


def test_phase21_final_evidence_rejects_nonexecuted_testnet_claim():
    e=FinalEvidenceBundle({'return':.1},{'x':1},{'x':1},{'executed':False},(), 'abc','r')
    assert 'TESTNET_EVIDENCE_INVALID' in e.blockers()

from app.universe.routing_policy import RouteCandidate,choose_route
from app.release.precedence import RequirementConflict,resolve_conflict
from app.database.outbox_health import OutboxHealth
from app.universe.risk_context import market_breadth


def test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability():
    good=RouteCandidate('binance','BTCUSDT','USDT','SPOT',True,Decimal('0.001'),Decimal('1'),Decimal('1'),Decimal('1'),Decimal('0'),True,Decimal('10'))
    bad_depeg=RouteCandidate('venue2','BTCUSDC','USDC','SPOT',True,Decimal('0.2'),Decimal('0'),Decimal('0'),Decimal('0'),Decimal('0'),True,Decimal('100'))
    bad_account=RouteCandidate('venue3','BTCUSDT','USDT','SPOT',True,Decimal('0'),Decimal('0'),Decimal('0'),Decimal('0'),Decimal('0'),False,Decimal('100'))
    d=choose_route([bad_depeg,bad_account,good])
    assert d.selected==good and d.total_cost_bps==Decimal('3')
    assert 'ACCOUNT_CAPABILITY_OK' in d.reasons and 'MARKET_TYPE_ALLOWED' in d.reasons


def test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux():
    c=RequirementConflict('halt trading','keep dashboard green','CAPITAL_AND_OPEN_POSITION_SAFETY','AVAILABILITY_PERFORMANCE_UX')
    assert resolve_conflict(c)=='halt trading'
    c=RequirementConflict('exchange truth','local cached state','EXCHANGE_ACCOUNT_REALITY_EXECUTION_CORRECTNESS','DATA_INTEGRITY_POINT_IN_TIME_CORRECTNESS')
    assert resolve_conflict(c)=='exchange truth'
    with pytest.raises(RuntimeError): resolve_conflict(RequirementConflict('a','b','IDENTITY_SECRET_ACCESS_SECURITY','IDENTITY_SECRET_ACCESS_SECURITY'))


def test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure():
    ok=OutboxHealth(3,3,0,0); ok.assert_no_event_loss(); assert not ok.degraded
    bad=OutboxHealth(2,1,0,0)
    with pytest.raises(RuntimeError): bad.assert_no_event_loss()
    assert OutboxHealth(0,0,1,0).degraded


def test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers():
    rows=[{'symbol':'BTCUSDT','return':'0.02','realized_volatility':'0.03','above_ma':True,'momentum':'0.04'}, {'symbol':'ETHUSDT','return':'-0.01','realized_volatility':'0.04','above_ma':False,'momentum':'-0.02'}, {'symbol':'SOLUSDT','return':'0.03','realized_volatility':'0.07','above_ma':True,'momentum':'0.06'}]
    b=market_breadth(rows,universe_version='u1')
    assert b.btc_leadership is not None and b.eth_leadership is not None and b.altcoin_breadth>=0
    assert b.dispersion>=0 and b.cross_sectional_momentum_dispersion>=0

from app.execution.order_conflicts import ProtectiveOrderEvidence,evaluate_protective_conflicts
from app.auth.db_service import LoginThrottle


def test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only():
    d=evaluate_protective_conflicts(ProtectiveOrderEvidence(Decimal('1'),Decimal('1'),Decimal('1'),1,2,False,'PERPETUAL',True))
    assert not d.safe and d.halt_new_risk
    assert {'STALE_REPLACE_ORDER','OVERLAPPING_STOP_TP_EXCEEDS_POSITION','CANCEL_REPLACE_RACE_REQUIRES_RECONCILIATION','REDUCE_ONLY_REQUIRED_FOR_PROTECTIVE_EXIT'} <= set(d.reasons)
    safe=evaluate_protective_conflicts(ProtectiveOrderEvidence(Decimal('1'),Decimal('1'),Decimal('0'),2,2,True,'PERPETUAL'))
    assert safe.safe


def test_phase21_login_throttle_is_bounded_and_clears_after_success():
    t=LoginThrottle(max_attempts=2,window_seconds=60)
    t.fail('u',now=100); t.fail('u',now=101)
    with pytest.raises(PermissionError): t.check('u',now=102)
    t.success('u'); t.check('u',now=102)
