from __future__ import annotations
import uuid
from sqlalchemy import select
from app.core.security import SecretBox,fingerprint
from app.database.models import ApiCredential

class CredentialVault:
    def __init__(self,session_factory,box:SecretBox): self.sf=session_factory; self.box=box
    def store(self,exchange_account_id,api_key,api_secret,permissions:dict):
        normalized={str(k).upper():bool(v) for k,v in permissions.items()}
        if normalized.get('WITHDRAW') or normalized.get('WITHDRAWAL'): raise PermissionError('withdrawal permission is forbidden')
        if not normalized.get('READ',False): raise PermissionError('READ permission required')
        with self.sf() as s:
            row=ApiCredential(id=uuid.uuid4().hex,exchange_account_id=exchange_account_id,key_fingerprint=fingerprint(api_key),encrypted_api_key=self.box.encrypt(api_key),encrypted_secret=self.box.encrypt(api_secret),permission_snapshot=normalized)
            s.add(row); s.commit(); return {'credential_id':row.id,'key_fingerprint':row.key_fingerprint,'permissions':normalized}
    def load(self,credential_id):
        with self.sf() as s:
            row=s.get(ApiCredential,credential_id)
            if row is None: raise LookupError('credential not found')
            return {'api_key':self.box.decrypt(row.encrypted_api_key),'api_secret':self.box.decrypt(row.encrypted_secret),'permissions':dict(row.permission_snapshot),'key_fingerprint':row.key_fingerprint}
