from __future__ import annotations
import hashlib,hmac,secrets,time
from dataclasses import dataclass
from argon2 import PasswordHasher
from cryptography.fernet import Fernet

_ph=PasswordHasher()
def hash_password(password:str)->str:
    if len(password)<12: raise ValueError('password too short')
    return _ph.hash(password)
def verify_password(encoded:str,password:str)->bool:
    try: return _ph.verify(encoded,password)
    except Exception: return False

def password_hash_needs_upgrade(encoded:str)->bool:
    try: return _ph.check_needs_rehash(encoded)
    except Exception: return True

def fingerprint(value:str)->str: return hashlib.sha256(value.encode()).hexdigest()[:16]

class SecretBox:
    def __init__(self,key:bytes): self.fernet=Fernet(key)
    @staticmethod
    def generate_key()->bytes: return Fernet.generate_key()
    def encrypt(self,text:str)->str: return self.fernet.encrypt(text.encode()).decode()
    def decrypt(self,token:str)->str: return self.fernet.decrypt(token.encode()).decode()

@dataclass(frozen=True)
class Confirmation:
    nonce_hash:str; action:str; expires_at:float; used:bool=False
class ConfirmationStore:
    def __init__(self): self._items:dict[str,Confirmation]={}
    def issue(self,action:str,ttl_seconds:int=120)->str:
        raw=secrets.token_urlsafe(32); h=hashlib.sha256(raw.encode()).hexdigest()
        self._items[h]=Confirmation(h,action,time.time()+ttl_seconds,False); return raw
    def consume(self,raw:str,action:str)->bool:
        h=hashlib.sha256(raw.encode()).hexdigest(); item=self._items.get(h)
        if not item or item.used or item.action!=action or item.expires_at<time.time(): return False
        self._items[h]=Confirmation(item.nonce_hash,item.action,item.expires_at,True); return True

def secure_compare(a:str,b:str)->bool: return hmac.compare_digest(a,b)
