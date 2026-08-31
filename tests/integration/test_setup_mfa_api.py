import hashlib
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from app.main import create_app
from app.core.enums import Environment
from app.database.session import make_engine, init_db, session_factory
from app.auth.db_service import DatabaseAuthService
from app.core.security import SecretBox
from app.auth.mfa import totp
from app.services.setup_wizard import SetupWizardService

PASSWORD = 'long-password-123'


def secured():
    engine = make_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    init_db(engine)
    sf = session_factory(engine)
    auth = DatabaseAuthService(sf, SecretBox(SecretBox.generate_key()))
    setup = SetupWizardService(sf)
    bootstrap = 'TEST_BOOTSTRAP_TOKEN'
    app = create_app(Environment.PROD, auth, hashlib.sha256(bootstrap.encode()).hexdigest(), setup_service=setup)
    client = TestClient(app, base_url='https://localhost')
    created = client.post('/api/v1/auth/bootstrap-admin', json={'username': 'admin', 'password': PASSWORD, 'bootstrap_token': bootstrap})
    assert created.status_code == 200
    login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': PASSWORD})
    assert login.status_code == 200
    return engine, auth, client, login.json()['csrf_token'], created.json()['user_id']


def test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper():
    engine, auth, client, csrf, user_id = secured()
    first = client.get('/api/v1/setup').json()
    assert first['current_step'] == 1 and first['startup_mode'] == 'PAPER'
    headers = {'X-CSRF-Token': csrf}
    for step in range(1, 8):
        payload = {'requested_mode': 'LIVE'} if step == 4 else {'value': step}
        if step == 2:
            payload.update({'api_key': 'MUST_NOT_PERSIST', 'api_secret': 'MUST_NOT_PERSIST'})
        response = client.post('/api/v1/setup/step', json={'step': step, 'data': payload}, headers=headers)
        assert response.status_code == 200
    resumed = client.get('/api/v1/setup').json()
    assert resumed['completed_steps'] == list(range(1, 8))
    assert 'api_key' not in resumed['non_secret_config']['step_2']
    assert 'api_secret' not in resumed['non_secret_config']['step_2']
    blocked = client.post('/api/v1/setup/step', json={'step': 8, 'data': {'preflight_ok': False}}, headers=headers)
    assert blocked.status_code == 423
    completed = client.post('/api/v1/setup/step', json={'step': 8, 'data': {'preflight_ok': True}}, headers=headers).json()
    assert completed['completed'] is True and completed['startup_mode'] == 'PAPER'
    engine.dispose()


def test_setup_api_rejects_skipping_steps():
    engine, auth, client, csrf, user_id = secured()
    client.get('/api/v1/setup')
    response = client.post('/api/v1/setup/step', json={'step': 2, 'data': {}}, headers={'X-CSRF-Token': csrf})
    assert response.status_code == 422
    engine.dispose()


def test_mfa_enrollment_api_secret_once_and_recovery_codes_then_login_enforced():
    engine, auth, client, csrf, user_id = secured()
    headers = {'X-CSRF-Token': csrf}
    enroll = client.post('/api/v1/auth/mfa/enroll', json={'password': PASSWORD}, headers=headers)
    assert enroll.status_code == 200
    secret = enroll.json()['secret']
    assert secret in enroll.json()['otpauth_uri']
    confirm = client.post('/api/v1/auth/mfa/confirm', json={'code': totp(secret)}, headers=headers)
    assert confirm.status_code == 200 and len(confirm.json()['recovery_codes']) == 10
    client.cookies.clear()
    denied = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': PASSWORD})
    assert denied.status_code == 401
    allowed = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': PASSWORD, 'mfa_code': totp(secret)})
    assert allowed.status_code == 200
    engine.dispose()


def test_mfa_reset_api_requires_one_time_high_risk_confirmation():
    engine, auth, client, csrf, user_id = secured()
    headers = {'X-CSRF-Token': csrf}
    secret = client.post('/api/v1/auth/mfa/enroll', json={'password': PASSWORD}, headers=headers).json()['secret']
    client.post('/api/v1/auth/mfa/confirm', json={'code': totp(secret)}, headers=headers)
    confirmation = client.post('/api/v1/auth/confirm-high-risk', json={'password': PASSWORD, 'action': 'RESET_MFA'}, headers=headers)
    assert confirmation.status_code == 200
    nonce = confirmation.json()['confirmation_nonce']
    reset = client.post('/api/v1/auth/mfa/reset', json={'target_user_id': user_id, 'password': PASSWORD, 'confirmation_nonce': nonce}, headers=headers)
    assert reset.status_code == 200
    replay = client.post('/api/v1/auth/mfa/reset', json={'target_user_id': user_id, 'password': PASSWORD, 'confirmation_nonce': nonce}, headers=headers)
    assert replay.status_code == 403
    engine.dispose()
