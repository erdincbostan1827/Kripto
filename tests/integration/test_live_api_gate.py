import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from app.main import create_app
from app.core.enums import Environment
from app.core.live_gate import LiveGateEvidence,MANDATORY_GATES
from app.database.session import make_engine,init_db,session_factory
from app.auth.db_service import DatabaseAuthService
from app.core.security import SecretBox

def client(evidence=None):
    e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e)
    svc=DatabaseAuthService(session_factory(e),SecretBox(SecretBox.generate_key())); token='TEST_BOOTSTRAP_TOKEN'
    c=TestClient(create_app(Environment.PROD,svc,hashlib.sha256(token.encode()).hexdigest(),evidence),base_url='https://localhost')
    c.post('/api/v1/auth/bootstrap-admin',json={'username':'admin','password':'long-password-123','bootstrap_token':token})
    login=c.post('/api/v1/auth/login',json={'username':'admin','password':'long-password-123'}).json(); return e,c,login['csrf_token']

def confirmation(c,csrf):
    r=c.post('/api/v1/auth/confirm-high-risk',json={'password':'long-password-123','action':'ENABLE_LIVE'},headers={'X-CSRF-Token':csrf}); assert r.status_code==200; return r.json()['confirmation_nonce']

def test_live_blocked_when_evidence_missing():
    e,c,csrf=client(); n=confirmation(c,csrf); r=c.post('/api/v1/trading/live',json={'reason':'approved launch','confirmation_nonce':n},headers={'X-CSRF-Token':csrf}); assert r.status_code==423; e.dispose()

def test_live_requires_one_time_nonce_and_all_gates():
    ev=LiveGateEvidence('release-test',{k:True for k in MANDATORY_GATES}); e,c,csrf=client(ev); n=confirmation(c,csrf)
    r=c.post('/api/v1/trading/live',json={'reason':'approved launch','confirmation_nonce':n},headers={'X-CSRF-Token':csrf}); assert r.status_code==200 and r.json()['label']=='GERÇEK PARA'
    r2=c.post('/api/v1/trading/live',json={'reason':'repeat attempt','confirmation_nonce':n},headers={'X-CSRF-Token':csrf}); assert r2.status_code==423; e.dispose()
