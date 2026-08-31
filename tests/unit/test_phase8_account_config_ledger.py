from decimal import Decimal
import pytest
from app.execution.account_boundary import AccountIdentity,AccountBoundaryGuard,detect_external_activity
from app.execution.reconciliation import AccountSnapshot
from app.risk.config_safety import LiveConfigGuard
from app.risk.ledger_integrity import LedgerPosting,validate_double_entry

def test_account_boundary_rejects_other_subaccount():
    g=AccountBoundaryGuard(AccountIdentity('BINANCE','a','fp1','SPOT'))
    with pytest.raises(PermissionError): g.require(AccountIdentity('BINANCE','b','fp2','SPOT'))

def test_external_activity_detects_balance_position_and_order_drift():
    l=AccountSnapshot({'USDT':Decimal('100')},{'BTCUSDT':Decimal('1')},{'1'})
    r=AccountSnapshot({'USDT':Decimal('90')},{'BTCUSDT':Decimal('2')},{'2'})
    e=detect_external_activity(l,r)
    assert e.detected and e.balance_drift==('USDT',) and e.position_drift==('BTCUSDT',) and e.unknown_orders==('2',) and e.missing_orders==('1',)

def test_live_config_risk_increase_requires_restart_and_human_approval():
    g=LiveConfigGuard({'risk_per_trade':0.01,'max_open_positions':3})
    d=g.evaluate({'risk_per_trade':0.02,'max_open_positions':3})
    assert not d.allowed and d.requires_restart and d.requires_human_approval

def test_live_config_any_change_is_not_hot_applied():
    g=LiveConfigGuard({'risk_per_trade':0.01,'max_open_positions':3})
    assert not g.evaluate({'risk_per_trade':0.005,'max_open_positions':3}).allowed
    with pytest.raises(PermissionError): g.require_unchanged({'risk_per_trade':0.005,'max_open_positions':3})

def test_double_entry_integrity_balanced_per_asset():
    ps=[LedgerPosting('USDT',Decimal('-10'),'r1'),LedgerPosting('USDT',Decimal('10'),'r1'),LedgerPosting('BTC',Decimal('-1'),'r2'),LedgerPosting('BTC',Decimal('1'),'r2')]
    assert validate_double_entry(ps).balanced

def test_double_entry_integrity_rejects_imbalance():
    r=validate_double_entry([LedgerPosting('USDT',Decimal('-10'),'r1'),LedgerPosting('USDT',Decimal('9'),'r1')])
    assert not r.balanced and r.imbalances['USDT']==Decimal('-1')
from app.execution.reconciliation import plan_orphan_order_recovery
from app.execution.recovery import validate_private_stream_freshness

def test_unknown_exchange_order_is_never_silently_adopted():
    l=AccountSnapshot({}, {}, set()); r=AccountSnapshot({}, {}, {'x'})
    p=plan_orphan_order_recovery(l,r)
    assert p[0].action=='MANUAL_REVIEW'

def test_missing_exchange_order_queries_history_before_state_change():
    l=AccountSnapshot({}, {}, {'x'}); r=AccountSnapshot({}, {}, set())
    assert plan_orphan_order_recovery(l,r)[0].action=='QUERY_HISTORY_AND_RECONCILE'

def test_private_stream_stale_and_clock_regression_fail_closed():
    assert not validate_private_stream_freshness(now_monotonic=20,last_message_monotonic=10,max_age_seconds=5).healthy
    assert validate_private_stream_freshness(now_monotonic=12,last_message_monotonic=10,max_age_seconds=5).healthy
    assert validate_private_stream_freshness(now_monotonic=9,last_message_monotonic=10,max_age_seconds=5).reason=='MONOTONIC_CLOCK_REGRESSION'
from app.execution.account_boundary import ExchangeAccountBoundary
from app.risk.config_safety import validate_risk_config

def test_exchange_account_boundary_includes_margin_position_permission_identity():
    a=ExchangeAccountBoundary('a','BINANCE','fp','PERPETUAL','CROSS','ONE_WAY','cap1','perm1','key1')
    a.require_compatible(a)
    with pytest.raises(PermissionError):
        a.require_compatible(ExchangeAccountBoundary('a','BINANCE','fp','PERPETUAL','ISOLATED','ONE_WAY','cap1','perm1','key1'))

def test_risk_config_cross_field_validation_fail_closed():
    ok=validate_risk_config({'risk_per_trade':.01,'min_risk_reward':1.5,'max_daily_loss':.03,'max_drawdown':.1,'tp_allocations':[.5,.5]})
    assert ok.valid
    bad=validate_risk_config({'risk_per_trade':.2,'min_risk_reward':0,'max_daily_loss':.2,'max_drawdown':.1,'tp_allocations':[.8,.8]})
    assert not bad.valid and len(bad.errors)==4
