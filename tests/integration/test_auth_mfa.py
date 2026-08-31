from sqlalchemy.pool import StaticPool
import pytest
from app.database.session import make_engine,init_db,session_factory
from app.core.security import SecretBox
from app.auth.db_service import DatabaseAuthService
from app.auth.mfa import totp

def service():
    e=make_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool); init_db(e); return e,DatabaseAuthService(session_factory(e),SecretBox(SecretBox.generate_key()))
def test_login_and_rbac():
    e,s=service(); uid=s.create_user('alice','long-password-123','trader'); x=s.login('alice','long-password-123'); assert s.authenticate(x.session_token,'viewer')['role']=='trader'; assert s.authenticate(x.session_token,'trader')['user_id']==uid; e.dispose()
def test_rbac_denies_admin():
    e,s=service(); s.create_user('alice','long-password-123','viewer'); x=s.login('alice','long-password-123')
    with pytest.raises(PermissionError): s.authenticate(x.session_token,'admin')
    e.dispose()
def test_mfa_enrollment_reauth_required():
    e,s=service(); uid=s.create_user('alice','long-password-123','admin')
    with pytest.raises(PermissionError): s.begin_mfa_enrollment(uid,'wrong-password')
    e.dispose()
def test_mfa_login_and_single_use_recovery():
    e,s=service(); uid=s.create_user('alice','long-password-123','admin'); secret=s.begin_mfa_enrollment(uid,'long-password-123'); at=1760000000; codes=s.confirm_mfa_enrollment(uid,totp(secret,at),at)
    with pytest.raises(PermissionError): s.login('alice','long-password-123',at=at)
    assert s.login('alice','long-password-123',mfa_code=totp(secret,at),at=at).user_id==uid
    assert s.login('alice','long-password-123',recovery_code=codes[0],at=at).user_id==uid
    with pytest.raises(PermissionError): s.login('alice','long-password-123',recovery_code=codes[0],at=at)
    e.dispose()
def test_csrf_and_revocation():
    e,s=service(); s.create_user('alice','long-password-123'); x=s.login('alice','long-password-123'); assert s.verify_csrf(x.session_token,x.csrf_token); assert not s.verify_csrf(x.session_token,'wrong'); s.revoke(x.session_token)
    with pytest.raises(PermissionError): s.authenticate(x.session_token)
    e.dispose()
