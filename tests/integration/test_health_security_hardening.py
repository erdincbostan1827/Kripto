from datetime import datetime, timezone, timedelta
import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.pool import StaticPool

from app.auth.db_service import DatabaseAuthService
from app.core.enums import Environment
from app.core.security import SecretBox
from app.database.models import SessionRow, SystemEvent
from app.database.session import init_db, make_engine, session_factory
from app.main import create_app
from app.monitoring.health import HealthService, ProbeResult


def make_auth(inactivity=900):
    engine=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool)
    init_db(engine)
    sf=session_factory(engine)
    svc=DatabaseAuthService(sf,SecretBox(SecretBox.generate_key()),session_ttl_seconds=3600,inactivity_timeout_seconds=inactivity)
    return engine,sf,svc


def test_prod_health_is_fail_closed_when_probes_are_unconfigured():
    app=create_app(Environment.PROD)
    with TestClient(app,base_url='https://localhost') as client:
        health=client.get('/health')
        assert health.status_code==200
        body=health.json()
        assert body['ready_for_new_risk'] is False
        assert body['database']=='UNCONFIGURED'
        assert client.get('/ready').status_code==503


def test_prod_health_can_be_ready_only_with_healthy_explicit_probes():
    ok=lambda: ProbeResult('UP',0.1)
    health=HealthService({'database':ok,'redis':ok,'exchange':ok,'clock':ok},fail_closed=True)
    app=create_app(Environment.PROD,health_service=health)
    with TestClient(app,base_url='https://localhost') as client:
        assert client.get('/ready').status_code==200


def test_prod_security_headers_docs_disabled_and_correlation_id_preserved():
    app=create_app(Environment.PROD)
    with TestClient(app,base_url='https://localhost') as client:
        r=client.get('/health',headers={'X-Correlation-ID':'corr-123'})
        assert r.headers['x-correlation-id']=='corr-123'
        assert r.headers['strict-transport-security'].startswith('max-age=')
        assert r.headers['x-content-type-options']=='nosniff'
        assert r.headers['x-frame-options']=='DENY'
        assert "frame-ancestors 'none'" in r.headers['content-security-policy']
        assert client.get('/docs').status_code==404
        assert client.get('/openapi.json').status_code==404


def test_untrusted_host_is_rejected_in_prod():
    app=create_app(Environment.PROD)
    with TestClient(app,base_url='https://evil.example') as client:
        assert client.get('/health').status_code==400


def test_auth_response_is_no_store_and_session_inactivity_revokes_session():
    engine,sf,svc=make_auth(inactivity=60)
    token='TEST_BOOTSTRAP_TOKEN'
    app=create_app(Environment.PROD,svc,hashlib.sha256(token.encode()).hexdigest())
    with TestClient(app,base_url='https://localhost') as client:
        client.post('/api/v1/auth/bootstrap-admin',json={'username':'admin','password':'long-password-123','bootstrap_token':token})
        login=client.post('/api/v1/auth/login',json={'username':'admin','password':'long-password-123'})
        assert login.status_code==200
        assert login.headers['cache-control'].startswith('no-store')
        raw=client.cookies.get('ctp_session')
        with sf() as s:
            row=s.scalar(select(SessionRow))
            row.last_seen_at=datetime.now(timezone.utc)-timedelta(minutes=5)
            s.commit()
        with pytest.raises(PermissionError):
            svc.authenticate(raw)
        with sf() as s:
            events=s.scalars(select(SystemEvent).where(SystemEvent.event_type=='SESSION_EXPIRED')).all()
            assert events and events[-1].payload['reason']=='INACTIVITY'
    engine.dispose()


def test_failed_login_creates_suspicious_login_event_without_password():
    engine,sf,svc=make_auth()
    user_id=svc.create_user('alice','long-password-123','viewer')
    with pytest.raises(PermissionError):
        svc.login('alice','wrong-password-value')
    with sf() as s:
        evt=s.scalar(select(SystemEvent).where(SystemEvent.event_type=='SUSPICIOUS_LOGIN_FAILED'))
        assert evt is not None and evt.payload['user_id']==user_id
        assert 'password' not in str(evt.payload).lower()
    engine.dispose()

def test_validation_error_does_not_echo_secret_input():
    engine,sf,svc=make_auth()
    token='TEST_BOOTSTRAP_TOKEN'
    app=create_app(Environment.PROD,svc,hashlib.sha256(token.encode()).hexdigest())
    with TestClient(app,base_url='https://localhost') as client:
        response=client.post('/api/v1/auth/bootstrap-admin',json={'username':'admin','password':'PwS3cr3t!','bootstrap_token':'SENSITIVE_TOKEN_VALUE'})
        text=response.text
        assert response.status_code==422
        assert 'SENSITIVE_TOKEN_VALUE' not in text and 'PwS3cr3t!' not in text
        assert 'correlation_id' in response.json()
    engine.dispose()
