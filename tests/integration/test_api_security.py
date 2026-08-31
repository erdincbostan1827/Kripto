import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from app.main import create_app
from app.core.enums import Environment
from app.database.session import make_engine,init_db,session_factory
from app.auth.db_service import DatabaseAuthService
from app.core.security import SecretBox


def secured():
    e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e)
    svc=DatabaseAuthService(session_factory(e),SecretBox(SecretBox.generate_key()))
    token='TEST_BOOTSTRAP_TOKEN'; app=create_app(Environment.PROD,svc,hashlib.sha256(token.encode()).hexdigest()); return e,svc,TestClient(app,base_url='https://localhost'),token

def test_prod_is_fail_closed_without_session():
    e,svc,c,t=secured(); assert c.get('/api/v1/status').status_code==401; e.dispose()

def test_bootstrap_single_use_login_cookie_and_csrf():
    e,svc,c,t=secured(); r=c.post('/api/v1/auth/bootstrap-admin',json={'username':'admin','password':'long-password-123','bootstrap_token':t}); assert r.status_code==200
    assert c.post('/api/v1/auth/bootstrap-admin',json={'username':'x','password':'long-password-123','bootstrap_token':t}).status_code==403
    login=c.post('/api/v1/auth/login',json={'username':'admin','password':'long-password-123'}); assert login.status_code==200 and 'ctp_session' in c.cookies
    assert c.get('/api/v1/status').status_code==200
    assert c.post('/api/v1/trading/start',json={'reason':'operator start'}).status_code==403
    csrf=login.json()['csrf_token']; assert c.post('/api/v1/trading/start',json={'reason':'operator start'},headers={'X-CSRF-Token':csrf}).status_code==200
    e.dispose()

def test_prod_websocket_requires_session():
    e,svc,c,t=secured()
    try:
        with c.websocket_connect('/api/v1/ws') as ws: ws.receive_json(); ok=False
    except Exception: ok=True
    assert ok; e.dispose()
