from __future__ import annotations
import base64,hashlib,hmac,secrets,struct,time

def new_totp_secret()->str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')

def _decode(secret:str)->bytes:
    padded=secret + '='*((8-len(secret)%8)%8)
    return base64.b32decode(padded,casefold=True)

def totp(secret:str,at:int|None=None,step:int=30,digits:int=6)->str:
    counter=int((at if at is not None else time.time())//step)
    digest=hmac.new(_decode(secret),struct.pack('>Q',counter),hashlib.sha1).digest()
    offset=digest[-1]&0x0F; code=(struct.unpack('>I',digest[offset:offset+4])[0]&0x7FFFFFFF)%(10**digits)
    return f'{code:0{digits}d}'

def verify_totp(secret:str,code:str,at:int|None=None,window:int=1)->bool:
    at=int(at if at is not None else time.time())
    return any(hmac.compare_digest(totp(secret,at+i*30),str(code)) for i in range(-window,window+1))

def generate_recovery_codes(count:int=10)->list[str]:
    return [secrets.token_urlsafe(9).replace('-','A').replace('_','B') for _ in range(count)]

def recovery_hash(code:str)->str:
    return hashlib.sha256(code.encode()).hexdigest()
