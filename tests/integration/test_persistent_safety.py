from datetime import datetime,timezone,timedelta
from decimal import Decimal
from sqlalchemy import update
from sqlalchemy.pool import StaticPool
import pytest
from app.database.session import make_engine,init_db,session_factory
from app.database.models import ExchangeAccount,AccountBalance,Position,Order,AuditLog
from app.database.audit_store import DatabaseAuditStore
from app.database.credentials import CredentialVault
from app.core.security import SecretBox
from app.execution.persistent import DatabaseLeaderRegistry,DatabaseCapitalReservations
from app.execution.local_snapshot import DatabaseAccountSnapshotProvider

def setup():
 e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e); sf=session_factory(e)
 with sf() as s: s.add(ExchangeAccount(id='a',exchange='X',account_fingerprint='f',market_type='SPOT',capabilities={},permission_snapshot={},status='ACTIVE')); s.commit()
 return e,sf

def test_database_audit_detects_tampering():
 e,sf=setup(); a=DatabaseAuditStore(sf); a.append('admin','LIVE_DISABLE','account:a','c1','test'); assert a.verify()
 with sf() as s: s.execute(update(AuditLog).values(reason='tampered')); s.commit()
 assert not a.verify(); e.dispose()

def test_credential_vault_encrypts_and_rejects_withdrawal():
 e,sf=setup(); v=CredentialVault(sf,SecretBox(SecretBox.generate_key())); x=v.store('a','KEY','SECRET',{'READ':True,'TRADE':True}); loaded=v.load(x['credential_id']); assert loaded['api_secret']=='SECRET' and x['key_fingerprint']!='KEY'
 with pytest.raises(PermissionError): v.store('a','K2','S2',{'READ':True,'WITHDRAW':True})
 e.dispose()

def test_persistent_fencing_token_increases_after_expiry():
 e,sf=setup(); r=DatabaseLeaderRegistry(sf); now=datetime.now(timezone.utc); a=r.acquire('a','i1',1,now); b=r.acquire('a','i2',1,now+timedelta(seconds=2)); assert b.fencing_token>a.fencing_token and not r.validate('a','i1',a.fencing_token,now+timedelta(seconds=2)); e.dispose()

def test_persistent_reservation_prevents_double_spend():
 e,sf=setup(); r=DatabaseCapitalReservations(sf); r.reserve('i1','60','100',account_id='a')
 with pytest.raises(ValueError): r.reserve('i2','50','100',account_id='a')
 r.release('i1'); assert r.reserve('i2','50','100',account_id='a').amount==Decimal('50'); e.dispose()

def test_database_account_snapshot_survives_process_state():
 e,sf=setup()
 with sf() as s:
  s.add(AccountBalance(id='b',exchange_account_id='a',asset='USDT',free=100,locked=5)); s.add(Position(id='p',exchange_account_id='a',symbol='BTCUSDT',quantity=1,average_entry=10,realized_pnl=0)); s.add(Order(id='o',intent_id='i',exchange_account_id='a',symbol='BTCUSDT',side='SELL',order_type='STOP_LOSS_LIMIT',quantity=1,status='ACKNOWLEDGED',exchange_order_id='ex1',client_order_id='ctp-i')); s.commit()
 x=DatabaseAccountSnapshotProvider(sf).snapshot('a'); assert x.balances['USDT']==Decimal('105') and x.positions['BTCUSDT']==1 and 'ex1' in x.open_order_ids; e.dispose()


def test_disk_full_on_durability_critical_audit_write_halts_new_risk():
 from sqlalchemy.exc import OperationalError
 from app.risk.state import RiskMachine
 from app.core.storage_health import PersistentStorageUnavailable
 class FakeBind:
  class dialect: name='sqlite'
 class FakeSession:
  bind=FakeBind()
  def __enter__(self): return self
  def __exit__(self,*_): return False
  def scalar(self,*_): return None
  def add(self,*_): pass
  def rollback(self): pass
  def commit(self): raise OperationalError('INSERT',{},OSError(28,'No space left on device'))
 class SF:
  def __call__(self): return FakeSession()
 risk=RiskMachine()
 store=DatabaseAuditStore(SF(),risk_machine=risk)
 with pytest.raises(PersistentStorageUnavailable,match='DISK_FULL'):
  store.append('system','ORDER_SUBMIT','order:x','c-disk','test disk full')
 assert risk.state.value=='HALTED'
 assert not risk.allow_new_risk()
