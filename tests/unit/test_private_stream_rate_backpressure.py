from app.exchange.private_stream import *
from app.data.rate_limit import RateLimitBudget
from app.core.backpressure import PriorityEventBuffer,QueuedEvent

def execution(cid='ctp-1',trade='10'):
 return {'subscriptionId':0,'event':{'e':'executionReport','E':1,'s':'BTCUSDT','c':cid,'S':'BUY','o':'LIMIT','x':'TRADE','X':'PARTIALLY_FILLED','i':7,'l':'0.1','z':'0.1','L':'60000','n':'0.1','N':'BNB','t':trade}}
def test_parse_execution_report(): assert parse_user_event(execution()).symbol=='BTCUSDT'
def test_unknown_manual_order_detected(): assert PrivateStreamProjector().project(parse_user_event(execution('manual-1'))).classification=='UNKNOWN_ORDER'
def test_known_order_applies(): assert PrivateStreamProjector().project(parse_user_event(execution())).classification=='KNOWN_PLATFORM_ACTIVITY'
def test_duplicate_fill_idempotent():
 p=PrivateStreamProjector(); e=parse_user_event(execution()); p.project(e); assert p.project(e).classification=='DUPLICATE_FILL'
def test_balance_snapshot():
 e=parse_user_event({'e':'outboundAccountPosition','E':1,'B':[{'a':'USDT','f':'10','l':'2'}]}); p=PrivateStreamProjector(); assert p.project(e).classification=='KNOWN_ACCOUNT_SNAPSHOT' and p.balances['USDT'][0].as_tuple()
def test_balance_update_requires_review(): assert PrivateStreamProjector().project(parse_user_event({'e':'balanceUpdate','E':1,'a':'USDT','d':'5','T':1})).action=='MANUAL_REVIEW_REQUIRED'
def test_stream_termination_halts():
 p=PrivateStreamProjector(); assert p.project(parse_user_event({'e':'eventStreamTerminated','E':1})).action=='HALT_NEW_RISK' and p.terminated
def test_signature_subscription_request():
 x=signature_subscription_request('KEY','SECRET',123456); assert x['method']=='userDataStream.subscribe.signature' and x['params']['signature'] and 'SECRET' not in str(x)
def test_rate_budget_reset_and_reserve():
 r=RateLimitBudget(); r.configure('weight',100,60,now=0); assert r.allow('weight',80,now=1); assert not r.allow('weight',10,priority='low',now=2); assert r.allow('weight',10,priority='low',now=61)
def test_backpressure_prioritizes_private_event():
 q=PriorityEventBuffer(2); q.put(QueuedEvent('scanner_low',1)); q.put(QueuedEvent('candidate_market',2)); assert q.put(QueuedEvent('private_order_fill',3)); assert len(q)==2 and q.get().payload==3 and q.dropped==1
def test_backpressure_drops_low_when_full():
 q=PriorityEventBuffer(1); q.put(QueuedEvent('private_order_fill',1)); assert not q.put(QueuedEvent('scanner_low',2)); assert q.dropped==1


def _execution(status, cumulative, event_time, trade_id=None):
    from app.exchange.private_stream import ExecutionReport
    from decimal import Decimal
    return ExecutionReport('BTCUSDT','ctp-order-1','BUY','LIMIT','TRADE',status,'99',Decimal('0.1'),Decimal(str(cumulative)),Decimal('60000'),Decimal('0'),None,trade_id,event_time)


def test_private_stream_stale_order_event_cannot_regress_projection():
    from app.exchange.private_stream import PrivateStreamProjector
    p=PrivateStreamProjector()
    assert p.project(_execution('PARTIALLY_FILLED','0.5',2000,'t1')).action=='APPLY_ORDER_EVENT'
    stale=p.project(_execution('NEW','0',1000,None))
    assert stale.classification=='STALE_ORDER_EVENT'
    assert p.order_states['ctp-order-1']=='PARTIALLY_FILLED'


def test_private_stream_terminal_order_cannot_reopen():
    from app.exchange.private_stream import PrivateStreamProjector
    p=PrivateStreamProjector()
    assert p.project(_execution('FILLED','1',2000,'t2')).action=='APPLY_ORDER_EVENT'
    bad=p.project(_execution('PARTIALLY_FILLED','1',3000,None))
    assert bad.classification=='TERMINAL_ORDER_REGRESSION'
    assert bad.action=='MANUAL_REVIEW_REQUIRED'
    assert p.order_states['ctp-order-1']=='FILLED'


def test_private_stream_duplicate_order_event_is_idempotent():
    from app.exchange.private_stream import PrivateStreamProjector
    p=PrivateStreamProjector()
    e=_execution('NEW','0',1000,None)
    assert p.project(e).action=='APPLY_ORDER_EVENT'
    duplicate=p.project(e)
    assert duplicate.classification=='DUPLICATE_ORDER_EVENT'
    assert duplicate.action=='IGNORE_IDEMPOTENT'

import pytest as _pytest

@_pytest.mark.parametrize('status,cumulative,trade_id',[('NEW','0',None),('PARTIALLY_FILLED','0.4','tp'),('FILLED','1','tf'),('CANCELED','0',None),('REJECTED','0',None)])
def test_private_stream_projects_order_lifecycle_statuses(status,cumulative,trade_id):
    p=PrivateStreamProjector()
    result=p.project(_execution(status,cumulative,1000,trade_id))
    assert result.action=='APPLY_ORDER_EVENT'
    assert p.order_states['ctp-order-1']==status


def test_private_stream_termination_is_explicit_unknown_risk_boundary():
    p=PrivateStreamProjector()
    result=p.project(StreamTerminated(1000))
    assert result.classification=='PRIVATE_STREAM_TERMINATED'
    assert result.action=='HALT_NEW_RISK'
    assert p.terminated
