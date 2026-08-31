from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

@dataclass(frozen=True)
class WebSocketState:
    connection_started_at: datetime
    max_lifetime: timedelta
    planned_rotation_at: datetime
    ping_pong_healthy: bool
    inbound_rate: float
    outbound_rate: float
    subscription_count: int
    reconnect_count: int
    disconnect_reason: str|None=None
    subscriptions_verified: bool=False
    continuity_verified: bool=False
    private_state_reconciled: bool=False
    healthy: bool=False

def new_state(start, *, max_lifetime=timedelta(hours=23,minutes=30)):
    return WebSocketState(start,max_lifetime,start+max_lifetime,True,0,0,0,0)

def handover(old:WebSocketState,new:WebSocketState,*,is_private=False)->tuple[WebSocketState,bool]:
    ready=new.ping_pong_healthy and new.subscriptions_verified and new.continuity_verified and (new.private_state_reconciled or not is_private)
    return replace(new,healthy=ready), ready
