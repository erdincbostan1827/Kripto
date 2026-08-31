from decimal import Decimal
import pytest
from app.exchange.mock import MockExchange
from app.exchange.models import OrderIntent,OrderRecord
from app.core.enums import OrderState,TradingMode
from app.execution.pretrade import normalize_and_validate
from app.execution.state import transition
from app.execution.service import ExecutionService
from app.execution.reconciliation import *
from app.execution.protection import ensure_protected,protection_coverage
from app.execution.ownership import OwnershipBook
from app.execution.leader import LeaderRegistry
from app.execution.reservation import CapitalReservations
from app.risk.state import RiskMachine

def intent(id='i1',price='60000',qty='0.01',typ='LIMIT'): return OrderIntent(id,'a1','BTCUSDT','BUY',typ,Decimal(qty),Decimal(price) if price else None)
def test_pretrade_normalizes():
 e=MockExchange(); x=normalize_and_validate(intent(price='60000.009',qty='0.010009'),e.get_symbol_filters('BTCUSDT'),e.get_capabilities('BTCUSDT'),Decimal('60000')); assert x.price==Decimal('60000.00') and x.quantity==Decimal('0.01000')
def test_min_notional_rejected():
 e=MockExchange()
 with pytest.raises(ValueError): normalize_and_validate(intent(qty='0.00001'),e.get_symbol_filters('BTCUSDT'),e.get_capabilities('BTCUSDT'),Decimal('60000'))
def test_fat_finger_rejected():
 e=MockExchange()
 with pytest.raises(ValueError): normalize_and_validate(intent(price='70000'),e.get_symbol_filters('BTCUSDT'),e.get_capabilities('BTCUSDT'),Decimal('60000'),Decimal('100'))
def test_order_transition_direct_fill(): assert transition(OrderState.SUBMITTED,OrderState.FILLED)==OrderState.FILLED
def test_illegal_transition():
 with pytest.raises(ValueError): transition(OrderState.CREATED,OrderState.FILLED)
def test_idempotent_submit():
 e=MockExchange(); s=ExecutionService(e,RiskMachine()); a=s.submit(intent(),Decimal('60000'),Decimal('100')); b=s.submit(intent(),Decimal('60000'),Decimal('100')); assert a.exchange_order_id==b.exchange_order_id and len(e.orders)==1
def test_ambiguous_becomes_unknown():
 e=MockExchange(); e.fail_mode='ambiguous'; r=RiskMachine(); x=ExecutionService(e,r).submit(intent(),Decimal('60000'),Decimal('100')); assert x.state==OrderState.UNKNOWN and r.state.value=='MANUAL_REVIEW_REQUIRED'
def test_reconciliation_clean():
 s=AccountSnapshot({'USDT':Decimal('10')},{},set()); assert reconcile(s,s).risk_state.value=='NORMAL'
def test_reconciliation_external_order():
 l=AccountSnapshot({}, {}, {'known'}); x=AccountSnapshot({}, {}, {'known','manual'}); r=reconcile(l,x); assert 'UNKNOWN_ORDER:manual' in r.drift
def test_reconciliation_balance_drift():
 l=AccountSnapshot({'USDT':Decimal('10')},{},set()); x=AccountSnapshot({'USDT':Decimal('11')},{},set()); assert reconcile(l,x).risk_state.value=='MANUAL_REVIEW_REQUIRED'
def test_protective_stop_coverage():
 o=OrderRecord('i','a','BTCUSDT','SELL','STOP_LOSS_LIMIT',Decimal('1'),OrderState.ACKNOWLEDGED,stop_price=Decimal('90')); assert ensure_protected(Decimal('1'),'LONG',[o])
def test_nonstop_not_protective():
 o=OrderRecord('i','a','BTCUSDT','SELL','LIMIT',Decimal('1'),OrderState.ACKNOWLEDGED,price=Decimal('90'))
 with pytest.raises(RuntimeError): ensure_protected(Decimal('1'),'LONG',[o])
def test_partial_protection_insufficient():
 o=OrderRecord('i','a','BTCUSDT','SELL','STOP_LOSS_LIMIT',Decimal('.5'),OrderState.ACKNOWLEDGED,stop_price=Decimal('90'))
 with pytest.raises(RuntimeError): ensure_protected(Decimal('1'),'LONG',[o])
def test_strategy_ownership_prevents_cross_exit():
 b=OwnershipBook(); b.allocate('s1','BTC',Decimal('1'),Decimal('100'))
 with pytest.raises(ValueError): b.exit('s1','BTC',Decimal('2'),Decimal('110'))
def test_strategy_pnl_attribution():
 b=OwnershipBook(); b.allocate('s1','BTC',Decimal('1'),Decimal('100')); assert b.exit('s1','BTC',Decimal('.5'),Decimal('110'))==Decimal('5')
def test_leader_fencing():
 l=LeaderRegistry(); a=l.acquire('a','one',ttl=1,now=100); assert l.validate('a','one',a.fencing_token,100.5); b=l.acquire('a','two',ttl=1,now=102); assert b.fencing_token>a.fencing_token and not l.validate('a','one',a.fencing_token,102)
def test_active_leader_blocks_other():
 l=LeaderRegistry(); l.acquire('a','one',ttl=10,now=100)
 with pytest.raises(PermissionError): l.acquire('a','two',ttl=10,now=101)
def test_capital_reservation():
 c=CapitalReservations(); c.reserve('i1','60','100',now=1)
 with pytest.raises(ValueError): c.reserve('i2','50','100',now=1)
def test_reservation_idempotent():
 c=CapitalReservations(); a=c.reserve('i1','60','100',now=1); b=c.reserve('i1','60','100',now=1); assert a==b
def test_live_execution_requires_fencing_and_reservation():
 e=MockExchange(); l=LeaderRegistry(); c=CapitalReservations(); r=RiskMachine(); s=ExecutionService(e,r,l,c); lease=l.acquire('a1','node',ttl=100); c.reserve('i1','1000','10000',ttl=100)
 x=s.submit(intent(),Decimal('60000'),Decimal('100'),TradingMode.LIVE,'node',lease.fencing_token); assert x.state==OrderState.ACKNOWLEDGED
def test_live_execution_missing_reservation():
 e=MockExchange(); l=LeaderRegistry(); c=CapitalReservations(); lease=l.acquire('a1','node',now=10,ttl=100)
 with pytest.raises(PermissionError): ExecutionService(e,RiskMachine(),l,c).submit(intent(),Decimal('60000'),Decimal('100'),TradingMode.LIVE,'node',lease.fencing_token)

def test_reduce_only_model_cannot_increase_absolute_exposure():
 from app.exchange.models import OrderIntent
 e=MockExchange(); r=RiskMachine(); r.reducing_only('risk')
 service=ExecutionService(e,r)
 sell=OrderIntent('reduce-long','a1','BTCUSDT','SELL','LIMIT',Decimal('0.01'),Decimal('60000'),reduce_only=True)
 result=service.submit(sell,Decimal('60000'),Decimal('100'),current_position_qty=Decimal('0.02'))
 assert result.state==OrderState.ACKNOWLEDGED
 wrong_side=OrderIntent('wrong-side','a1','BTCUSDT','BUY','LIMIT',Decimal('0.01'),Decimal('60000'),reduce_only=True)
 with pytest.raises(PermissionError,match='increase long'):
  service.submit(wrong_side,Decimal('60000'),Decimal('100'),current_position_qty=Decimal('0.02'))
 oversize=OrderIntent('oversize','a1','BTCUSDT','SELL','LIMIT',Decimal('0.03'),Decimal('60000'),reduce_only=True)
 with pytest.raises(PermissionError,match='cross through zero'):
  service.submit(oversize,Decimal('60000'),Decimal('100'),current_position_qty=Decimal('0.02'))
 flat=OrderIntent('flat','a1','BTCUSDT','SELL','LIMIT',Decimal('0.01'),Decimal('60000'),reduce_only=True)
 with pytest.raises(PermissionError,match='flat'):
  service.submit(flat,Decimal('60000'),Decimal('100'),current_position_qty=Decimal('0'))


def test_cancel_pending_can_receive_late_fill_without_illegal_state():
 assert transition(OrderState.CANCEL_PENDING,OrderState.PARTIALLY_FILLED)==OrderState.PARTIALLY_FILLED
 assert transition(OrderState.CANCEL_PENDING,OrderState.FILLED)==OrderState.FILLED


def test_terminal_order_state_cannot_be_reopened_by_late_ack():
 with pytest.raises(ValueError): transition(OrderState.FILLED,OrderState.ACKNOWLEDGED)
 with pytest.raises(ValueError): transition(OrderState.CANCELLED,OrderState.ACKNOWLEDGED)
