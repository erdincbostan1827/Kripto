from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Mapping

AUTH_TYPES=frozenset({'HMAC','ED25519'})
TRANSPORT_TYPES=frozenset({'REST_JSON','WS_REQUEST_RESPONSE','WS_STREAM'})

@dataclass(frozen=True)
class TransportRequest:
    transport:str
    auth_type:str|None
    operation:str
    payload:Mapping[str,object]

class Transport(Protocol):
    def send(self,request:TransportRequest)->Mapping[str,object]: ...

def validate_request(req:TransportRequest)->None:
    if req.transport not in TRANSPORT_TYPES: raise ValueError('unsupported transport')
    if req.auth_type is not None and req.auth_type not in AUTH_TYPES: raise ValueError('unsupported auth')
