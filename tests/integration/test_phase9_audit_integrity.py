from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.pool import StaticPool
from sqlalchemy import update

from app.database.session import make_engine, init_db, session_factory
from app.database.models import ExchangeAccount, Order, Fill, LedgerEntry, AuditLog
from app.database.audit_store import DatabaseAuditStore
from app.execution.reconciliation import AccountSnapshot
from app.execution.phase9 import reconcile_with_audit
from app.risk.referential_integrity import validate_execution_references


def setup():
    e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e); sf=session_factory(e)
    with sf() as s:
        s.add(ExchangeAccount(id='a',exchange='BINANCE',account_fingerprint='fp',market_type='SPOT',capabilities={},permission_snapshot={},status='ACTIVE')); s.commit()
    return e,sf


def test_reconciliation_result_is_bound_to_immutable_audit_chain():
    e,sf=setup(); store=DatabaseAuditStore(sf)
    local=AccountSnapshot({'USDT':Decimal('100')},{'BTCUSDT':Decimal('1')},{'o1'})
    remote=AccountSnapshot({'USDT':Decimal('90')},{'BTCUSDT':Decimal('1')},{'o2'})
    result,evidence=reconcile_with_audit(local=local,exchange=remote,audit_store=store,correlation_id='corr-1')
    assert result.drift and evidence.drift==tuple(sorted(result.drift)) and store.verify()
    with sf() as s:
        row=s.query(AuditLog).one(); assert row.action=='ACCOUNT_RECONCILIATION' and row.correlation_id=='corr-1'
        s.execute(update(AuditLog).values(reason='tampered')); s.commit()
    assert not store.verify(); e.dispose()


def test_execution_referential_integrity_accepts_valid_order_fill_ledger():
    e,sf=setup(); now=datetime.now(timezone.utc)
    with sf() as s:
        s.add(Order(id='o1',intent_id='i1',exchange_account_id='a',symbol='BTCUSDT',side='BUY',order_type='MARKET',quantity=1,status='FILLED',exchange_order_id='ex1',client_order_id='ctp-i1'))
        s.add(Fill(id='f1',exchange_account_id='a',order_id='o1',trade_id='t1',quantity=1,price=100,fee_asset='USDT',fee_amount=1))
        s.add(LedgerEntry(id='l1',exchange_account_id='a',event_type='FILL',asset='USDT',amount=-100,reference_type='ORDER',reference_id='o1',event_time=now,metadata_json={}))
        s.add(LedgerEntry(id='l2',exchange_account_id='a',event_type='FEE',asset='USDT',amount=-1,reference_type='FILL',reference_id='t1',event_time=now,metadata_json={}))
        s.commit(); assert validate_execution_references(s,exchange_account_id='a').valid
    e.dispose()


def test_execution_referential_integrity_detects_missing_ledger_reference():
    e,sf=setup(); now=datetime.now(timezone.utc)
    with sf() as s:
        s.add(LedgerEntry(id='l1',exchange_account_id='a',event_type='FILL',asset='USDT',amount=-100,reference_type='ORDER',reference_id='missing',event_time=now,metadata_json={})); s.commit()
        r=validate_execution_references(s,exchange_account_id='a'); assert not r.valid and r.errors==('LEDGER_ORDER_MISSING:l1:missing',)
    e.dispose()
