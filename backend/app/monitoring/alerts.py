from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class DeliveryResult: channel:str; delivered:bool; error:str|None=None
class AlertFanout:
    def __init__(self,channels:dict[str,callable]): self.channels=channels
    def send(self,message:str,critical=False):
        results=[]
        for name,fn in self.channels.items():
            try: fn(message); results.append(DeliveryResult(name,True))
            except Exception as exc: results.append(DeliveryResult(name,False,str(exc)))
            if not critical and results[-1].delivered: break
        if critical and not any(x.delivered for x in results): raise RuntimeError('CRITICAL_ALERT_DELIVERY_FAILED')
        return results
