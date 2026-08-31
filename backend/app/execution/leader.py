from __future__ import annotations
from dataclasses import dataclass
import time
@dataclass
class Lease: account_id:str; instance_id:str; fencing_token:int; expires_at:float
class LeaderRegistry:
    def __init__(self): self.leases={}; self.tokens={}
    def acquire(self,account_id,instance_id,ttl=10,now=None):
        now=now or time.time(); cur=self.leases.get(account_id)
        if cur and cur.expires_at>now and cur.instance_id!=instance_id: raise PermissionError('leader already active')
        token=self.tokens.get(account_id,0)+(0 if cur and cur.instance_id==instance_id and cur.expires_at>now else 1); self.tokens[account_id]=token
        lease=Lease(account_id,instance_id,token,now+ttl); self.leases[account_id]=lease; return lease
    def validate(self,account_id,instance_id,token,now=None):
        now=now or time.time(); cur=self.leases.get(account_id); return bool(cur and cur.instance_id==instance_id and cur.fencing_token==token and cur.expires_at>now)
    def heartbeat(self,account_id,instance_id,token,ttl=10,now=None):
        now=now or time.time(); cur=self.leases.get(account_id)
        if not cur or cur.instance_id!=instance_id or cur.fencing_token!=token or cur.expires_at<=now:
            raise PermissionError('cannot heartbeat stale or expired leader lease')
        cur.expires_at=now+ttl
        return cur
