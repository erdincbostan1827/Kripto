from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse
import httpx

@dataclass(frozen=True)
class ChannelDelivery:
    delivered: bool
    channel: str

class WebhookAlertChannel:
    def __init__(self,url:str,*,client=None,timeout_seconds:float=5.0):
        p=urlparse(url)
        if p.scheme!='https' or not p.netloc: raise ValueError('production webhook must use https')
        self._url=url; self._client=client; self._timeout=timeout_seconds
    def send(self,message:str)->ChannelDelivery:
        try:
            c=self._client
            r=(c.post(self._url,json={'message':message},timeout=self._timeout) if c else httpx.post(self._url,json={'message':message},timeout=self._timeout))
            r.raise_for_status(); return ChannelDelivery(True,'webhook')
        except Exception as exc: raise RuntimeError('webhook alert delivery failed') from exc

class EmailAlertChannel:
    """Transport-injected email channel; keeps SMTP/provider credentials outside messages/logs."""
    def __init__(self,sender,recipient:str):
        if '@' not in recipient: raise ValueError('valid recipient required')
        self._sender=sender; self._recipient=recipient
    def send(self,message:str)->ChannelDelivery:
        try: self._sender(self._recipient,'Trading platform critical alert',message); return ChannelDelivery(True,'email')
        except Exception as exc: raise RuntimeError('email alert delivery failed') from exc
