from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
import hashlib,secrets,time,uuid
from sqlalchemy import select
from app.core.security import hash_password,verify_password,password_hash_needs_upgrade,SecretBox
from app.database.models import User,SessionRow,MfaRecoveryCode,PasswordResetToken,SystemEvent
from .mfa import new_totp_secret,verify_totp,generate_recovery_codes,recovery_hash

ROLE_LEVEL={'viewer':1,'trader':2,'admin':3}
@dataclass(frozen=True)
class LoginResult:
    session_token:str; csrf_token:str; user_id:str; role:str

class LoginThrottle:
    def __init__(self,max_attempts=5,window_seconds=300): self.max_attempts=max_attempts; self.window_seconds=window_seconds; self.attempts={}
    def check(self,key:str,now=None):
        now=now or time.time(); xs=[x for x in self.attempts.get(key,[]) if now-x<self.window_seconds]; self.attempts[key]=xs
        if len(xs)>=self.max_attempts: raise PermissionError('login throttled')
    def fail(self,key:str,now=None): self.attempts.setdefault(key,[]).append(now or time.time())
    def success(self,key:str): self.attempts.pop(key,None)

class DatabaseAuthService:
    def __init__(self,session_factory,secret_box:SecretBox,session_ttl_seconds=3600,inactivity_timeout_seconds=900):
        self.sf=session_factory; self.box=secret_box; self.ttl=session_ttl_seconds; self.inactivity_timeout=inactivity_timeout_seconds; self.throttle=LoginThrottle()
    def _event(self,s,event_type,severity,user_id=None,**payload):
        s.add(SystemEvent(id=uuid.uuid4().hex,event_type=event_type,severity=severity,correlation_id=uuid.uuid4().hex,payload={'user_id':user_id,**payload}))
    def bootstrap_admin(self,username,password):
        with self.sf() as s:
            if s.scalar(select(User.id).limit(1)) is not None: raise PermissionError('admin already exists')
        return self.create_user(username,password,'admin')
    def create_user(self,username,password,role='viewer'):
        if role not in ROLE_LEVEL: raise ValueError('invalid role')
        with self.sf() as s:
            if s.scalar(select(User).where(User.username==username)): raise ValueError('username exists')
            u=User(id=uuid.uuid4().hex,username=username,password_hash=hash_password(password),role=role,mfa_enabled=False); s.add(u); self._event(s,'USER_CREATED','INFO',u.id,role=role); s.commit(); return u.id
    def begin_mfa_enrollment(self,user_id,password):
        with self.sf() as s:
            u=s.get(User,user_id)
            if not u or not verify_password(u.password_hash,password):
                self._event(s,'MFA_ENROLLMENT_REAUTH_FAILED','WARN',user_id); s.commit(); raise PermissionError('re-authentication failed')
            secret=new_totp_secret(); u.mfa_secret_encrypted=self.box.encrypt(secret); self._event(s,'MFA_ENROLLMENT_STARTED','INFO',user_id); s.commit(); return secret
    def confirm_mfa_enrollment(self,user_id,code,at=None):
        with self.sf() as s:
            u=s.get(User,user_id)
            if not u or not u.mfa_secret_encrypted: raise PermissionError('no pending MFA enrollment')
            secret=self.box.decrypt(u.mfa_secret_encrypted)
            if not verify_totp(secret,code,at):
                self._event(s,'MFA_ENROLLMENT_FAILED','WARN',user_id); s.commit(); raise PermissionError('invalid MFA code')
            codes=generate_recovery_codes()
            for c in codes: s.add(MfaRecoveryCode(id=uuid.uuid4().hex,user_id=user_id,code_hash=recovery_hash(c)))
            u.mfa_enabled=True; self._event(s,'MFA_ENABLED','INFO',user_id); s.commit(); return codes
    def reset_mfa(self,user_id,actor_user_id,actor_password):
        now=datetime.now(timezone.utc)
        with self.sf() as s:
            actor=s.get(User,actor_user_id); target=s.get(User,user_id)
            if not actor or actor.role!='admin' or not verify_password(actor.password_hash,actor_password):
                self._event(s,'MFA_RESET_DENIED','WARN',user_id,actor_user_id=actor_user_id); s.commit(); raise PermissionError('admin re-authentication required')
            if not target: raise ValueError('user not found')
            target.mfa_enabled=False; target.mfa_secret_encrypted=None
            for row in s.scalars(select(MfaRecoveryCode).where(MfaRecoveryCode.user_id==user_id,MfaRecoveryCode.used_at.is_(None))).all(): row.used_at=now
            self._event(s,'MFA_RESET','WARN',user_id,actor_user_id=actor_user_id); s.commit()

    def issue_password_reset(self,user_id,ttl_seconds=900):
        raw=secrets.token_urlsafe(32); now=datetime.now(timezone.utc); digest=hashlib.sha256(raw.encode()).hexdigest()
        with self.sf() as s:
            if not s.get(User,user_id): raise ValueError('user not found')
            s.add(PasswordResetToken(id=uuid.uuid4().hex,user_id=user_id,token_hash=digest,expires_at=now+timedelta(seconds=ttl_seconds)))
            self._event(s,'PASSWORD_RESET_ISSUED','WARN',user_id); s.commit()
        return raw

    def consume_password_reset(self,raw_token,new_password,now=None):
        now=now or datetime.now(timezone.utc); digest=hashlib.sha256(raw_token.encode()).hexdigest()
        with self.sf() as s:
            row=s.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash==digest,PasswordResetToken.used_at.is_(None)))
            expires=self._aware(row.expires_at) if row else None
            if not row or not expires or expires<=now: raise PermissionError('invalid or expired password reset token')
            user=s.get(User,row.user_id)
            if not user: raise PermissionError('invalid password reset token')
            user.password_hash=hash_password(new_password); row.used_at=now
            for session in s.scalars(select(SessionRow).where(SessionRow.user_id==user.id,SessionRow.revoked_at.is_(None))).all(): session.revoked_at=now
            self._event(s,'PASSWORD_RESET_COMPLETED','WARN',user.id); s.commit(); return user.id

    def login(self,username,password,mfa_code=None,recovery_code=None,at=None):
        key=username.casefold(); self.throttle.check(key)
        with self.sf() as s:
            u=s.scalar(select(User).where(User.username==username))
            if not u or not verify_password(u.password_hash,password):
                self.throttle.fail(key); self._event(s,'SUSPICIOUS_LOGIN_FAILED','WARN',getattr(u,'id',None),username=username); s.commit(); raise PermissionError('invalid credentials')
            if password_hash_needs_upgrade(u.password_hash):
                u.password_hash=hash_password(password)
            if u.mfa_enabled:
                ok=False; method=None
                if mfa_code and u.mfa_secret_encrypted:
                    ok=verify_totp(self.box.decrypt(u.mfa_secret_encrypted),mfa_code,at); method='TOTP' if ok else None
                if recovery_code and not ok:
                    h=recovery_hash(recovery_code); row=s.scalar(select(MfaRecoveryCode).where(MfaRecoveryCode.user_id==u.id,MfaRecoveryCode.code_hash==h,MfaRecoveryCode.used_at.is_(None)))
                    if row: row.used_at=datetime.now(timezone.utc); ok=True; method='RECOVERY_CODE'
                if not ok:
                    self.throttle.fail(key); self._event(s,'SUSPICIOUS_LOGIN_MFA_FAILED','WARN',u.id); s.commit(); raise PermissionError('MFA required')
                if method=='RECOVERY_CODE': self._event(s,'MFA_RECOVERY_CODE_USED','WARN',u.id)
            raw=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24); now=datetime.now(timezone.utc)
            s.add(SessionRow(id=uuid.uuid4().hex,user_id=u.id,token_hash=hashlib.sha256(raw.encode()).hexdigest(),csrf_hash=hashlib.sha256(csrf.encode()).hexdigest(),expires_at=now+timedelta(seconds=self.ttl),last_seen_at=now)); self._event(s,'LOGIN_SUCCEEDED','INFO',u.id); s.commit(); self.throttle.success(key); return LoginResult(raw,csrf,u.id,u.role)
    def reauthenticate(self,user_id,password):
        with self.sf() as s:
            u=s.get(User,user_id)
            if not u or not verify_password(u.password_hash,password):
                self._event(s,'HIGH_RISK_REAUTH_FAILED','WARN',user_id); s.commit(); raise PermissionError('re-authentication failed')
            self._event(s,'HIGH_RISK_REAUTH_SUCCEEDED','INFO',user_id); s.commit(); return {'user_id':u.id,'role':u.role}
    @staticmethod
    def _aware(value):
        if value is None: return None
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    def authenticate(self,session_token,required_role='viewer'):
        h=hashlib.sha256(session_token.encode()).hexdigest(); now=datetime.now(timezone.utc)
        with self.sf() as s:
            row=s.scalar(select(SessionRow).where(SessionRow.token_hash==h,SessionRow.revoked_at.is_(None)))
            expires=self._aware(row.expires_at) if row else None; last_seen=self._aware(row.last_seen_at) if row else None
            inactive=bool(last_seen and last_seen + timedelta(seconds=self.inactivity_timeout) <= now)
            if not row or not expires or expires <= now or inactive:
                if row and row.revoked_at is None: row.revoked_at=now; self._event(s,'SESSION_EXPIRED','INFO',row.user_id,reason='INACTIVITY' if inactive else 'ABSOLUTE_EXPIRY'); s.commit()
                raise PermissionError('invalid session')
            u=s.get(User,row.user_id)
            if not u or ROLE_LEVEL[u.role]<ROLE_LEVEL[required_role]: raise PermissionError('insufficient role')
            row.last_seen_at=now; s.commit(); return {'user_id':u.id,'username':u.username,'role':u.role,'csrf_hash':row.csrf_hash}
    def verify_csrf(self,session_token,csrf_token):
        ctx=self.authenticate(session_token); return hmac_compare(ctx['csrf_hash'],hashlib.sha256(csrf_token.encode()).hexdigest())
    def rotate_csrf(self,session_token):
        token_hash=hashlib.sha256(session_token.encode()).hexdigest(); raw=secrets.token_urlsafe(24)
        with self.sf() as s:
            row=s.scalar(select(SessionRow).where(SessionRow.token_hash==token_hash,SessionRow.revoked_at.is_(None)))
            if not row: raise PermissionError('invalid session')
            row.csrf_hash=hashlib.sha256(raw.encode()).hexdigest(); self._event(s,'CSRF_ROTATED','INFO',row.user_id); s.commit(); return raw
    def revoke(self,session_token):
        h=hashlib.sha256(session_token.encode()).hexdigest()
        with self.sf() as s:
            row=s.scalar(select(SessionRow).where(SessionRow.token_hash==h))
            if row: row.revoked_at=datetime.now(timezone.utc); self._event(s,'SESSION_REVOKED','INFO',row.user_id); s.commit()

def hmac_compare(a,b):
    import hmac
    return hmac.compare_digest(a,b)
