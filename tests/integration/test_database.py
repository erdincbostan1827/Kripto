import uuid
from sqlalchemy.pool import StaticPool
from app.database.session import make_engine,init_db,session_factory
from app.database.models import Base,ExchangeAccount,Order,OutboxEvent,DeadLetterRow
from app.database.outbox import OutboxDispatcher

def engine():
 e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e); return e
def test_schema_creates_expected_tables():
 e=engine(); names=set(Base.metadata.tables); assert {'users','exchange_accounts','api_credentials','orders','fills','positions','account_balances','domain_events','outbox_events','dead_letters','audit_log'}<=names; e.dispose()
def test_unique_order_intent():
 e=engine(); sf=session_factory(e)
 with sf() as s:
  a=ExchangeAccount(id='a',exchange='X',account_fingerprint='f',market_type='SPOT',capabilities={},permission_snapshot={},status='ACTIVE'); s.add(a); s.commit(); s.add(Order(id='1',intent_id='i',exchange_account_id='a',symbol='BTC',side='BUY',order_type='LIMIT',quantity=1,status='ACK',client_order_id='i')); s.commit(); s.add(Order(id='2',intent_id='i',exchange_account_id='a',symbol='ETH',side='BUY',order_type='LIMIT',quantity=1,status='ACK',client_order_id='i'))
  try: s.commit(); ok=False
  except Exception: s.rollback(); ok=True
  assert ok
 e.dispose()
def test_outbox_publish_success():
 e=engine(); sf=session_factory(e); seen=[]
 with sf() as s: s.add(OutboxEvent(id='o',event_id='e',topic='X',payload={'a':1},attempts=0)); s.commit()
 r=OutboxDispatcher(sf,lambda t,p:seen.append((t,p))).dispatch_once(); assert r['published']==1 and seen
 e.dispose()
def test_outbox_failure_to_dlq():
 e=engine(); sf=session_factory(e)
 with sf() as s: s.add(OutboxEvent(id='o',event_id='e',topic='X',payload={'a':1},attempts=0)); s.commit()
 d=OutboxDispatcher(sf,lambda t,p:(_ for _ in ()).throw(RuntimeError('boom')),max_attempts=1); d.dispatch_once()
 with sf() as s: assert s.query(DeadLetterRow).count()==1
 e.dispose()

def test_immutable_initial_migration_matches_runtime_table_set():
 import importlib.util
 from pathlib import Path
 path=Path(__file__).resolve().parents[2]/'alembic/versions/0001_core_schema.py'
 text=path.read_text()
 assert 'database/schema.sql' not in text and 'Path(' not in text
 spec=importlib.util.spec_from_file_location('migration_0001',path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 created={stmt.split()[2].strip('"') for stmt in module.STATEMENTS if stmt.startswith('CREATE TABLE ')}
 assert created==set(Base.metadata.tables)-{'password_reset_tokens'}
 assert module.revision=='0001_core_schema' and module.down_revision is None
 migration2=(Path(__file__).resolve().parents[2]/'alembic/versions/0002_identity_recovery.py').read_text()
 assert "revision='0002_identity_recovery'" in migration2 and "down_revision='0001_core_schema'" in migration2
 assert "'password_reset_tokens'" in migration2

def test_order_persistence_schema_contains_required_execution_fields():
    columns = set(Order.__table__.columns.keys())
    assert {
        'symbol', 'side', 'quantity', 'price', 'stop_price', 'created_at',
        'status', 'exchange_order_id', 'client_order_id', 'order_type'
    } <= columns
    # Fees are fill-level facts rather than guessed order-level values.
    from app.database.models import Fill
    assert {'fee_asset', 'fee_amount', 'quantity', 'price', 'trade_id'} <= set(Fill.__table__.columns.keys())
