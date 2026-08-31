from __future__ import annotations
from datetime import datetime,timedelta,timezone

import pytest

from app.research.bootstrap import bootstrap_paths,effective_sample_size
from app.research.cost_history import CostVintage,PointInTimeCostModel
from app.exchange.contract_compat import ApiSchema,changelog_requires_review,validate_payload
from app.data.websocket_lifecycle import handover,new_state
from app.exchange.transport import AUTH_TYPES,TRANSPORT_TYPES,TransportRequest,validate_request
from app.execution.smart_execution import ExecutionContext,ProtectiveOrderSpec,choose_policy
from app.core.live_config import LiveProfile,emergency_risk_change,validate_profile
from app.research.champion_challenger import ShadowObservation
from app.research.change_detection import cusum,detect_degradation,page_hinkley
from app.risk.attribution_extended import TradeAttribution,diagnose,group_performance
from app.research.benchmarks import benchmark_report,deflated_sharpe_proxy,probabilistic_sharpe_proxy,probability_backtest_overfit_proxy

UTC=timezone.utc

def test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics():
    returns=[.01,.012,-.008,.011,-.02,.015,-.005,.009,-.03,.02]*8
    assert effective_sample_size(returns)>0
    for method in ('reshuffle','block','stationary'):
        r=bootstrap_paths(returns,simulations=100,method=method,block_size=4,cost_shock=.0001,slippage_shock=.0002,latency_shock=.0001)
        assert 0<=r.ruin_probability<=1 and r.expected_max_drawdown>=0 and r.max_drawdown_p95>=r.expected_max_drawdown
        assert r.terminal_wealth_p05<=r.terminal_wealth_p50<=r.terminal_wealth_p95 and r.effective_sample_size<=len(returns)
    regimes=['TREND' if i%2 else 'RANGE' for i in range(len(returns))]
    assert bootstrap_paths(returns,simulations=50,method='regime',regimes=regimes).expected_losing_streak>=0


def test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity():
    a=datetime(2025,1,1,tzinfo=UTC); b=datetime(2026,1,1,tzinfo=UTC)
    old=CostVintage('BTCUSDT',a,b,1,2,.2,'VIP1',.5,.4,10,.1,'exchange-archive','historical actual',(-1,2))
    new=CostVintage('BTCUSDT',b,None,.5,1,.1,'VIP2',.2,.3,5,.01,'exchange-archive','historical actual',(-.5,1))
    model=PointInTimeCostModel([old,new])
    assert model.resolve('BTCUSDT',datetime(2025,6,1,tzinfo=UTC))==old
    assert model.resolve('BTCUSDT',datetime(2026,6,1,tzinfo=UTC))==new
    assert model.estimate_bps('BTCUSDT',datetime(2025,6,1,tzinfo=UTC),maker=False,include_borrow=True)==pytest.approx(2-.2+.5+.4)
    assert old.source and old.assumption and old.sensitivity_bps and old.min_notional==10 and old.tick_size==.1


def test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review():
    v1=ApiSchema('v1',frozenset({'symbol','price'}),frozenset({'qty'}))
    ok=validate_payload({'symbol':'BTC','price':1,'new_optional':'x'},v1,reject_unknown=False)
    assert ok.compatible and ok.unknown_fields==('new_optional',)
    bad=validate_payload({'symbol':'BTC'},v1)
    assert not bad.compatible and bad.missing_required==('price',)
    v2=ApiSchema('v2',frozenset({'symbol','price','timestamp'}),frozenset({'qty'}))
    assert changelog_requires_review(v1,v2)


def test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile():
    now=datetime(2026,8,29,12,tzinfo=UTC); old=new_state(now-timedelta(hours=23)); new=new_state(now)
    assert old.planned_rotation_at==old.connection_started_at+old.max_lifetime
    assert old.ping_pong_healthy and old.inbound_rate==0 and old.outbound_rate==0 and old.subscription_count==0 and old.reconnect_count==0
    ready_state,ready=handover(old,new,is_private=True); assert not ready and not ready_state.healthy
    from dataclasses import replace
    verified=replace(new,subscriptions_verified=True,continuity_verified=True,private_state_reconciled=True)
    ready_state,ready=handover(old,verified,is_private=True); assert ready and ready_state.healthy


def test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams():
    assert {'HMAC','ED25519'}<=AUTH_TYPES and {'REST_JSON','WS_REQUEST_RESPONSE','WS_STREAM'}<=TRANSPORT_TYPES
    for transport in TRANSPORT_TYPES:
        for auth in AUTH_TYPES:
            validate_request(TransportRequest(transport,auth,'query',{}))
    with pytest.raises(ValueError): validate_request(TransportRequest('FTP','HMAC','x',{}))


def test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing():
    aggressive=ExecutionContext(.95,1,5,.8,2,.2,1,.8,5,.1,.5,10_000)
    assert choose_policy(aggressive)=='AGGRESSIVE_LIMIT'
    passive=ExecutionContext(.2,100,2,.9,1,.1,2,.9,1,.05,.2,10_000)
    assert choose_policy(passive)=='PASSIVE_POST_ONLY'
    sliced=ExecutionContext(.2,100,2,.8,1,.5,0,.5,1,.05,.2,200_000)
    assert choose_policy(sliced)=='SLICED_LIMIT'
    bad=ExecutionContext(.2,100,2,.05,1,.1,0,.9,1,.7,.2,1000)
    assert choose_policy(bad)=='NO_TRADE'


def test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity():
    p=ProtectiveOrderSpec('MARK','BELOW',True,False,'MARK_PRICE',1.0,1.5)
    assert p.trigger_source=='MARK' and p.trigger_direction=='BELOW' and p.reduce_only and not p.close_position and p.working_type=='MARK_PRICE' and p.quantity<=p.protected_position_quantity
    with pytest.raises(ValueError): ProtectiveOrderSpec('LAST','BELOW',False,False,None,1,1)
    with pytest.raises(ValueError): ProtectiveOrderSpec('LAST','BELOW',True,False,None,2,1)


def test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash():
    p=LiveProfile('15m','SPOT','BTCUSDT','filters-v1',.02)
    assert validate_profile(p,allowed_timeframes={'15m'},allowed_market_types={'SPOT'},valid_symbols={'BTCUSDT'})
    n,a=emergency_risk_change(p,.01,actor='risk-officer',reason='incident',ts=datetime.now(UTC))
    assert p.max_risk_fraction==.02 and n.max_risk_fraction==.01 and a.old_value==.02 and a.new_value==.01 and a.actor and a.reason and a.config_hash==n.digest()
    with pytest.raises(ValueError): emergency_risk_change(p,.03,actor='x',reason='increase',ts=datetime.now(UTC))


def test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates():
    o=ShadowObservation('BUY','SELL','SELL_LIMIT',100,99,4,True)
    assert o.challenger_order_sent is False and o.divergence==-1 and o.estimated_cost_bps==4 and o.gates_passed
    with pytest.raises(ValueError): ShadowObservation('BUY','SELL','SELL_LIMIT',100,99,4,True,True)


def test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support():
    small=detect_degradation({'expectancy':[1]*10},min_samples=30)
    assert not small.degraded and small.false_alarm_guard
    drifting={'expectancy':[0.0,.1,-.1,.05,-.05]*6+[2.0]*30,'slippage':[1.0]*60,'fill_rate':[.9]*60,'feature':[0.0]*60,'regime':[.5]*60,'calibration':[.1]*60}
    d=detect_degradation(drifting,min_samples=30,z_threshold=2)
    assert d.degraded and any('EXPECTANCY' in x for x in d.reasons)
    assert cusum([0]*20+[2]*10,threshold=5) and page_hinkley([0]*20+[2]*10,threshold=5)


def test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context():
    t=TradeAttribution('trend','1.2','TREND','HIGH','15m','LONG','A','HIGH',14,5,False,'LIMIT','MAKER','DEEP','GOOD',.03,.02,-.001,-.002,-.003,-.004,-.005,-.006)
    assert t.strategy_contribution==pytest.approx(.05) and t.execution_drag>0
    assert diagnose(t) in {'STRATEGY','EXECUTION_OR_COST','DATA_LATENCY'}
    assert 'TREND' in group_performance([t],'regime') and 'trend' in group_performance([t],'strategy')
    for field in ('strategy_version','volatility_bucket','timeframe','direction','confidence_bucket','signal_score_bucket','hour','day_of_week','weekend','execution_type','maker_taker','liquidity_bucket','data_quality_bucket'):
        assert hasattr(t,field)


def test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported():
    s=[.002,-.001,.003,.001,-.002,.004,.001,-.001,.002,.001]*10
    a=[.001,-.002,.002,.001,-.003,.003,.001,-.001,.001,.0]*10
    r=benchmark_report(s,a)
    assert r.strategy_return!=0 and r.buy_hold_return!=0 and r.cash_return==0 and r.dca_return!=r.buy_hold_return and r.trend_return is not None
    assert r.excess_return==pytest.approx(r.strategy_return-r.buy_hold_return)
    assert r.minimum_track_record_length>=30 and r.effective_sample_size==len(s) and len(r.confidence_interval)==2
    assert deflated_sharpe_proxy(2,10)<2 and 0<=probabilistic_sharpe_proxy(1,.5,100)<=1
    assert 0<=probability_backtest_overfit_proxy([1,2,3],[3,2,1])<=1
