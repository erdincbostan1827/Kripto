from datetime import datetime,timezone,timedelta
import hashlib
import pytest
from sqlalchemy import select
from sqlalchemy.pool import StaticPool
from app.auth.db_service import DatabaseAuthService
from app.core.security import SecretBox
from app.database.models import PasswordResetToken,SessionRow,SystemEvent,User
from app.database.session import make_engine,init_db,session_factory


def service():
    engine=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(engine); sf=session_factory(engine)
    return engine,sf,DatabaseAuthService(sf,SecretBox(SecretBox.generate_key()))

def test_password_reset_token_is_hashed_single_use_and_revokes_sessions():
    e,sf,svc=service(); uid=svc.create_user('u','old-password-123','viewer'); login=svc.login('u','old-password-123'); raw=svc.issue_password_reset(uid,900)
    with sf() as s:
        row=s.scalar(select(PasswordResetToken)); assert row.token_hash==hashlib.sha256(raw.encode()).hexdigest() and raw not in row.token_hash
    svc.consume_password_reset(raw,'new-password-123')
    with pytest.raises(PermissionError): svc.consume_password_reset(raw,'another-password-123')
    with pytest.raises(PermissionError): svc.authenticate(login.session_token)
    assert svc.login('u','new-password-123').user_id==uid
    e.dispose()

def test_expired_password_reset_token_is_rejected():
    e,sf,svc=service(); uid=svc.create_user('u','old-password-123','viewer'); raw=svc.issue_password_reset(uid,1)
    with pytest.raises(PermissionError): svc.consume_password_reset(raw,'new-password-123',datetime.now(timezone.utc)+timedelta(minutes=5))
    e.dispose()

def test_mfa_reset_requires_admin_reauthentication_and_is_audited():
    e,sf,svc=service(); admin=svc.create_user('admin','admin-password-123','admin'); user=svc.create_user('user','user-password-123','trader')
    secret=svc.begin_mfa_enrollment(user,'user-password-123')
    from app.auth.mfa import totp
    svc.confirm_mfa_enrollment(user,totp(secret))
    with pytest.raises(PermissionError): svc.reset_mfa(user,admin,'wrong-admin-password')
    svc.reset_mfa(user,admin,'admin-password-123')
    with sf() as s:
        u=s.get(User,user); assert u.mfa_enabled is False and u.mfa_secret_encrypted is None
        assert s.scalar(select(SystemEvent).where(SystemEvent.event_type=='MFA_RESET')) is not None
    e.dispose()
