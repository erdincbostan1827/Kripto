from decimal import Decimal
import pytest
from app.exchange.mock import MockExchange
from app.exchange.models import OrderIntent
from app.execution.service import ExecutionService
from app.risk.state import RiskMachine
from app.risk.circuit import CircuitBreaker
from app.execution.reconciliation import AccountSnapshot,reconcile
from app.core.enums import RiskState

def test_exchange_timeout_halts_new_risk_via_unknown():
 e=MockExchange(); e.fail_mode='ambiguous'; r=RiskMachine(); s=ExecutionService(e,r); x=s.submit(OrderIntent('x','a','BTCUSDT','BUY','LIMIT',Decimal('.01'),Decimal('60000')),Decimal('60000'),Decimal('100')); assert x.state.value=='UNKNOWN' and not r.allow_new_risk()
@pytest.mark.parametrize('check',[{'database_ok':False},{'redis_ok':False},{'exchange_ok':False},{'clock_ok':False},{'private_stream_ok':False},{'data_fresh':False},{'balance_consistent':False},{'protective_orders_ok':False},{'duplicate_order_ok':False},{'spread_ok':False},{'volatility_ok':False},{'daily_loss_ok':False},{'drawdown_ok':False},{'order_rejection_ok':False}])
def test_fatal_circuit_conditions(check): assert CircuitBreaker().evaluate(**check)==RiskState.HALTED
def test_external_balance_change_requires_review():
 l=AccountSnapshot({'USDT':Decimal('1')},{},set()); x=AccountSnapshot({'USDT':Decimal('2')},{},set()); assert reconcile(l,x).risk_state==RiskState.MANUAL_REVIEW_REQUIRED
