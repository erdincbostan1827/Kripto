from __future__ import annotations
from dataclasses import dataclass
import hashlib,hmac,secrets,time

PRIVILEGED={'admin','trader'}

@dataclass(frozen=True)
class RecoveryPolicy:
    require_mfa_for_privileged:bool=True
    require_admin_approval_for_admin_reset:bool=True
    token_ttl_seconds:int=900
    max_attempts:int=5

@dataclass
class RecoveryGrant:
    token_hash:str
    user_id:str
    role:str
    expires_at:float
    attempts:int=0
    used:bool=False
    approved_by:str|None=None

class RecoveryGrantStore:
    """One-time, role-aware recovery grants with constant-time token comparison semantics."""
    def __init__(self,policy:RecoveryPolicy=RecoveryPolicy(),clock=time.time):
        self.policy=policy; self.clock=clock; self._grants:list[RecoveryGrant]=[]
    def issue(self,user_id:str,role:str,*,mfa_verified:bool=False,approved_by:str|None=None)->str:
        role=role.lower()
        if role in PRIVILEGED and self.policy.require_mfa_for_privileged and not mfa_verified:
            raise PermissionError('privileged recovery requires MFA evidence')
        if role=='admin' and self.policy.require_admin_approval_for_admin_reset and not approved_by:
            raise PermissionError('admin recovery requires independent approval')
        raw=secrets.token_urlsafe(32)
        self._grants.append(RecoveryGrant(hashlib.sha256(raw.encode()).hexdigest(),user_id,role,self.clock()+self.policy.token_ttl_seconds,approved_by=approved_by))
        return raw
    def consume(self,raw:str,user_id:str)->RecoveryGrant:
        digest=hashlib.sha256(raw.encode()).hexdigest(); now=self.clock()
        matched=None
        for grant in self._grants:
            # Compare every candidate with constant-time primitive; do not early-compare plaintext.
            if hmac.compare_digest(grant.token_hash,digest): matched=grant
        if matched is None or matched.user_id!=user_id or matched.used or matched.expires_at<=now:
            raise PermissionError('invalid or expired recovery token')
        if matched.attempts>=self.policy.max_attempts:
            raise PermissionError('recovery attempts exhausted')
        matched.attempts+=1; matched.used=True
        return matched
