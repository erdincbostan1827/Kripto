from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import pytest
from app.core.enums import MarketType, OrderState
from app.exchange.models import OrderIntent, OrderRecord
from app.execution.pretrade_guard import PreTradeLimits,PreTradeContext,evaluate_pretrade,require_pretrade
from app.execution.quality import ExecutionObservation,summarize_execution_quality
from app.execution.protective_state import assess_protection,ProtectionState


def intent(**kw):
    base=dict(intent_id='i1',account_id='a1',symbol='BTCUSDT',side='BUY',order_type='LIMIT',quantity=D('1'),price=D('100'),market_type=MarketType.SPOT)
    base.update(kw); return OrderIntent(**base)

def limits():
    return PreTradeLimits(D('200'),D('2'),D('250'),D('100'),D('50'),D('30'),3000)

def ctx(**kw):
    base=dict(reference_price=D('100'),reference_time=datetime.now(timezone.utc),bid=D('99.9'),ask=D('100.1'),expected_slippage_bps=D('10'),current_position_qty=D('0'),available_balance=D('500'),symbol_trading=True,trading_state_allows_new_risk=True,min_price=D('50'),max_price=D('150'))
    base.update(kw); return PreTradeContext(**base)

def test_pretrade_happy_path_and_metrics():
    d=evaluate_pretrade(intent(),limits(),ctx())
    assert d.allowed and d.order_notional==D('100') and d.resulting_position_notional==D('100')
    assert d.spread_bps==D('20.000')

def test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state():
    c=ctx(reference_time=datetime.now(timezone.utc)-timedelta(seconds=4),bid=D('99'),ask=D('101'),expected_slippage_bps=D('31'),symbol_trading=False)
    d=evaluate_pretrade(intent(price=D('102')),limits(),c)
    assert {'STALE_REFERENCE_PRICE','SPREAD_LIMIT','SLIPPAGE_LIMIT','SYMBOL_NOT_TRADING','PRICE_COLLAR'} <= set(d.reasons)
    with pytest.raises(PermissionError): require_pretrade(intent(price=D('102')),limits(),c)

def test_pretrade_rejects_notional_quantity_position_balance_and_exchange_price():
    d=evaluate_pretrade(intent(quantity=D('3'),price=D('160')),limits(),ctx(available_balance=D('50')))
    assert {'MAX_QUANTITY','MAX_ORDER_NOTIONAL','MAX_POSITION_NOTIONAL','PRICE_COLLAR','EXCHANGE_MAX_PRICE','INSUFFICIENT_AVAILABLE_BALANCE'} <= set(d.reasons)

def test_reduce_only_sanity_is_inside_final_pretrade_gate():
    d=evaluate_pretrade(intent(side='BUY',quantity=D('2'),reduce_only=True),limits(),ctx(current_position_qty=D('1')))
    assert not d.allowed and 'REDUCE_ONLY_SIDE' in d.reasons

def test_execution_quality_reports_cost_fill_latency_and_adverse_selection():
    rows=[
      ExecutionObservation('BUY',D('100'),D('99.9'),D('100.1'),D('100.05'),D('100.10'),D('1'),D('1'),12,40,maker=False,post_fill_mark=D('99.95')),
      ExecutionObservation('SELL',D('200'),D('199.8'),D('200.2'),D('199.9'),D('199.8'),D('0.5'),D('1'),20,80,cancelled=True,maker=True,post_fill_mark=D('200.0')),
      ExecutionObservation('BUY',D('50'),D('49.95'),D('50.05'),D('50.02'),None,D('0'),D('1'),30,None,rejected=True),
    ]
    q=summarize_execution_quality(rows)
    assert q.quoted_spread_bps>0 and q.effective_spread_bps>0 and q.realized_slippage_bps>0
    assert 0<q.fill_ratio<1 and q.partial_fill_ratio>0 and q.cancel_ratio>0 and q.reject_ratio>0
    assert q.avg_ack_ms>0 and q.avg_fill_ms>0 and q.maker_ratio>0 and q.adverse_selection_bps>0

def protective(qty='1',state=OrderState.ACKNOWLEDGED):
    return OrderRecord('p','a1','BTCUSDT','SELL','STOP_LOSS_LIMIT',D(qty),state,stop_price=D('90'))

def test_protective_state_requires_exchange_ack_before_claiming_protected():
    pending=assess_protection(D('1'),'LONG',[],protective_submit_pending=True,local_synthetic_stop=True)
    assert pending.state==ProtectionState.PENDING_ACK and not pending.allow_new_risk and pending.local_synthetic_only
    protected=assess_protection(D('1'),'LONG',[protective()])
    assert protected.state==ProtectionState.PROTECTED and protected.allow_new_risk

def test_unprotected_position_blocks_new_risk_and_selects_safe_action():
    x=assess_protection(D('2'),'LONG',[protective('1')])
    assert x.state==ProtectionState.UNPROTECTED_POSITION and not x.allow_new_risk
    assert x.required_action=='REDUCING_ONLY_AND_RETRY_PROTECTION'
    y=assess_protection(D('2'),'LONG',[],panic_close=True)
    assert y.required_action=='PANIC_CLOSE'

def test_execution_quality_includes_market_impact():
    q=summarize_execution_quality([ExecutionObservation('BUY',D('100'),D('99.9'),D('100.1'),D('100.05'),D('100.10'),D('1'),D('1'),10,20)])
    assert q.market_impact_bps>0

def test_protective_supervisor_restricts_retries_and_alerts_when_unprotected():
    from app.execution.protective_state import ProtectiveOrderSupervisor
    class Risk:
        def __init__(self): self.reason=None
        def restrict(self,r): self.reason=r
    risk=Risk(); calls=[]; alerts=[]
    sup=ProtectiveOrderSupervisor(risk,lambda:calls.append('retry'),alerts.append)
    a=sup.enforce(D('1'),'LONG',[],local_synthetic_stop=True)
    assert a.state==ProtectionState.UNPROTECTED_POSITION and risk.reason=='UNPROTECTED_POSITION'
    assert calls==['retry'] and alerts[0]['severity']=='CRITICAL' and alerts[0]['synthetic_only'] is True

def test_pretrade_rejects_invalid_side_and_trading_state():
    d=evaluate_pretrade(intent(side='HOLD'),limits(),ctx(trading_state_allows_new_risk=False))
    assert 'SIDE_SANITY' in d.reasons and 'TRADING_STATE_BLOCKS_NEW_RISK' in d.reasons
