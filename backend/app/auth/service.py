from __future__ import annotations
from dataclasses import dataclass
import secrets,time,hashlib
from app.core.security import hash_password,verify_password
@dataclass
class SessionInfo: user_id:str; role:str; expires_at:float; csrf:str
class SessionStore:
    def __init__(self): self.items={}
    def create(self,user_id,role,ttl=3600):
        raw=secrets.token_urlsafe(32); self.items[hashlib.sha256(raw.encode()).hexdigest()]=SessionInfo(user_id,role,time.time()+ttl,secrets.token_urlsafe(24)); return raw
    def get(self,raw):
        x=self.items.get(hashlib.sha256(raw.encode()).hexdigest()); return x if x and x.expires_at>time.time() else None
    def revoke(self,raw): self.items.pop(hashlib.sha256(raw.encode()).hexdigest(),None)
