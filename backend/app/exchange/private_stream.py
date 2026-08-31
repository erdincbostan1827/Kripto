from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import hashlib,hmac,time,uuid,urllib.parse

@dataclass(frozen=True)
class ExecutionReport:
    symbol:str; client_order_id:str; side:str; order_type:str; execution_type:str; order_status:str; exchange_order_id:str; last_qty:Decimal; cumulative_qty:Decimal; last_price:Decimal; fee:Decimal; fee_asset:str|None; trade_id:str|None; event_time_ms:int; stp_prevented_match_id:str|None=None
@dataclass(frozen=True)
class BalancePosition:
    balances:dict[str,tuple[Decimal,Decimal]]; event_time_ms:int
@dataclass(frozen=True)
class BalanceUpdate:
    asset:str; delta:Decimal; clear_time_ms:int; event_time_ms:int
@dataclass(frozen=True)
class FuturesPositionUpdate:
    positions:dict[str,Decimal]; balances:dict[str,Decimal]; event_time_ms:int
@dataclass(frozen=True)
class StreamTerminated:
    event_time_ms:int
@dataclass(frozen=True)
class UnknownUserEvent:
    event_type:str; raw:dict

def _payload(message:dict)->dict:
    return message.get('event') if isinstance(message.get('event'),dict) else message

def parse_user_event(message:dict):
    x=_payload(message); typ=x.get('e') or x.get('eventType') or ''
    if typ=='executionReport':
        return ExecutionReport(str(x.get('s','')),str(x.get('c','')),str(x.get('S','')),str(x.get('o','')),str(x.get('x','')),str(x.get('X','')),str(x.get('i','')),Decimal(str(x.get('l','0'))),Decimal(str(x.get('z','0'))),Decimal(str(x.get('L','0'))),Decimal(str(x.get('n','0'))),x.get('N'),None if x.get('t') in (None,-1,'-1') else str(x.get('t')),int(x.get('E',0)),None if x.get('v') is None else str(x.get('v')))
    if typ=='outboundAccountPosition':
        return BalancePosition({str(b['a']):(Decimal(str(b['f'])),Decimal(str(b['l']))) for b in x.get('B',[])},int(x.get('E',0)))
    if typ=='ACCOUNT_UPDATE':
        account=x.get('a') or {}
        positions={str(p.get('s','')):Decimal(str(p.get('pa','0'))) for p in account.get('P',[]) if p.get('s')}
        balances={str(b.get('a','')):Decimal(str(b.get('wb','0'))) for b in account.get('B',[]) if b.get('a')}
        return FuturesPositionUpdate(positions,balances,int(x.get('E',0)))
    if typ=='balanceUpdate': return BalanceUpdate(str(x.get('a','')),Decimal(str(x.get('d','0'))),int(x.get('T',0)),int(x.get('E',0)))
    if typ=='eventStreamTerminated': return StreamTerminated(int(x.get('E',0)))
    return UnknownUserEvent(str(typ),x)

def signature_subscription_request(api_key:str,api_secret:str,timestamp_ms:int|None=None,recv_window:int=5000,request_id:str|None=None)->dict:
    ts=timestamp_ms or int(time.time()*1000); params={'apiKey':api_key,'recvWindow':recv_window,'timestamp':ts}
    query=urllib.parse.urlencode(sorted(params.items())); params['signature']=hmac.new(api_secret.encode(),query.encode(),hashlib.sha256).hexdigest()
    return {'id':request_id or str(uuid.uuid4()),'method':'userDataStream.subscribe.signature','params':params}

@dataclass(frozen=True)
class ProjectionResult:
    classification:str; action:str; payload:dict
class PrivateStreamProjector:
    TERMINAL = {'FILLED','CANCELED','CANCELLED','REJECTED','EXPIRED','EXPIRED_IN_MATCH'}
    RANK = {'NEW':1,'PENDING_NEW':1,'PARTIALLY_FILLED':2,'PENDING_CANCEL':3,'FILLED':4,'CANCELED':4,'CANCELLED':4,'REJECTED':4,'EXPIRED':4,'EXPIRED_IN_MATCH':4}

    def __init__(self,client_order_prefix='ctp-'):
        self.prefix=client_order_prefix; self.seen_trades=set(); self.order_states={}; self.balances={}; self.positions={}; self.terminated=False
        self.order_progress={}
    def project(self,event):
        if isinstance(event,ExecutionReport):
            platform=event.client_order_id.startswith(self.prefix)
            if not platform: return ProjectionResult('UNKNOWN_ORDER','MANUAL_REVIEW_REQUIRED',{'client_order_id':event.client_order_id,'symbol':event.symbol})
            if event.trade_id and event.trade_id in self.seen_trades: return ProjectionResult('DUPLICATE_FILL','IGNORE_IDEMPOTENT',{'trade_id':event.trade_id})
            previous=self.order_progress.get(event.client_order_id)
            if previous is not None:
                prev_status,prev_qty,prev_time=previous
                if event.event_time_ms < prev_time or event.cumulative_qty < prev_qty:
                    return ProjectionResult('STALE_ORDER_EVENT','IGNORE_AND_RECONCILE',{'status':event.order_status,'previous_status':prev_status})
                if prev_status in self.TERMINAL and event.order_status != prev_status:
                    return ProjectionResult('TERMINAL_ORDER_REGRESSION','MANUAL_REVIEW_REQUIRED',{'status':event.order_status,'previous_status':prev_status})
                prev_rank=self.RANK.get(prev_status,0); new_rank=self.RANK.get(event.order_status,0)
                if new_rank < prev_rank and event.cumulative_qty <= prev_qty:
                    return ProjectionResult('OUT_OF_ORDER_ORDER_EVENT','IGNORE_AND_RECONCILE',{'status':event.order_status,'previous_status':prev_status})
                if event.event_time_ms == prev_time and event.order_status == prev_status and event.cumulative_qty == prev_qty:
                    return ProjectionResult('DUPLICATE_ORDER_EVENT','IGNORE_IDEMPOTENT',{'status':event.order_status})
            if event.trade_id: self.seen_trades.add(event.trade_id)
            self.order_states[event.client_order_id]=event.order_status
            self.order_progress[event.client_order_id]=(event.order_status,event.cumulative_qty,event.event_time_ms)
            return ProjectionResult('KNOWN_PLATFORM_ACTIVITY','APPLY_ORDER_EVENT',{'status':event.order_status,'last_qty':str(event.last_qty),'trade_id':event.trade_id})
        if isinstance(event,BalancePosition): self.balances.update(event.balances); return ProjectionResult('KNOWN_ACCOUNT_SNAPSHOT','APPLY_BALANCE_SNAPSHOT',{'assets':len(event.balances)})
        if isinstance(event,FuturesPositionUpdate):
            self.positions.update(event.positions); return ProjectionResult('KNOWN_POSITION_SNAPSHOT','APPLY_POSITION_AND_BALANCE_SNAPSHOT',{'positions':len(event.positions),'balances':len(event.balances)})
        if isinstance(event,BalanceUpdate): return ProjectionResult('UNKNOWN_BALANCE_CHANGE','MANUAL_REVIEW_REQUIRED',{'asset':event.asset,'delta':str(event.delta)})
        if isinstance(event,StreamTerminated): self.terminated=True; return ProjectionResult('PRIVATE_STREAM_TERMINATED','HALT_NEW_RISK',{})
        return ProjectionResult('UNKNOWN_EVENT','QUARANTINE',{'event_type':getattr(event,'event_type','')})
