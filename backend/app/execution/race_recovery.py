from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

TERMINAL={'FILLED','CANCELLED','CANCELED','REJECTED','EXPIRED'}
OPEN={'NEW','ACKNOWLEDGED','PARTIALLY_FILLED','PENDING_CANCEL','SUBMITTED'}

@dataclass(frozen=True)
class ReplaceRaceEvidence:
    old_order_id:str
    replacement_order_id:str|None
    old_exchange_status:str|None
    replacement_exchange_status:str|None
    old_cumulative_qty:Decimal=Decimal('0')
    local_expected_old_qty:Decimal=Decimal('0')
    ack_lost:bool=False

@dataclass(frozen=True)
class ReplaceRaceDecision:
    safe:bool
    action:str
    reasons:tuple[str,...]
    halt_new_risk:bool


def resolve_replace_race(e:ReplaceRaceEvidence)->ReplaceRaceDecision:
    """Fail closed across cancel/replace races and acknowledgement loss."""
    reasons=[]
    old=(e.old_exchange_status or 'UNKNOWN').upper()
    new=(e.replacement_exchange_status or 'UNKNOWN').upper()
    if e.ack_lost:
        reasons.append('ACK_LOST_DURING_DISCONNECT')
    if old=='UNKNOWN':
        reasons.append('OLD_ORDER_OUTCOME_UNKNOWN')
    if e.replacement_order_id and new=='UNKNOWN':
        reasons.append('REPLACEMENT_OUTCOME_UNKNOWN')
    if Decimal(e.old_cumulative_qty)>Decimal(e.local_expected_old_qty):
        reasons.append('OLD_ORDER_FILLED_DURING_REPLACE')
    if old in OPEN and e.replacement_order_id and new in OPEN:
        reasons.append('OVERLAPPING_LIVE_ORDERS')
    if reasons:
        return ReplaceRaceDecision(False,'RECONCILE_OPEN_ORDERS_AND_FILLS',tuple(reasons),True)
    if old not in TERMINAL:
        return ReplaceRaceDecision(False,'QUERY_ORDER_HISTORY',('OLD_ORDER_NOT_TERMINAL',),True)
    return ReplaceRaceDecision(True,'APPLY_EXCHANGE_TRUTH',(),False)

@dataclass(frozen=True)
class UnknownOutcomeEvidence:
    client_order_id:str
    user_stream_status:str|None
    open_order_status:str|None
    fill_quantity:Decimal
    requested_quantity:Decimal

@dataclass(frozen=True)
class UnknownOutcomeDecision:
    resolved_status:str
    action:str
    manual_review:bool


def resolve_unknown_outcome(e:UnknownOutcomeEvidence)->UnknownOutcomeDecision:
    """Resolve ambiguous submit from user stream + open orders + fills, never by timeout assumption."""
    user=(e.user_stream_status or '').upper()
    opened=(e.open_order_status or '').upper()
    fill=Decimal(e.fill_quantity); requested=Decimal(e.requested_quantity)
    if requested<=0 or fill<0 or fill>requested:
        return UnknownOutcomeDecision('UNKNOWN','MANUAL_REVIEW_INVALID_FILL_EVIDENCE',True)
    if fill==requested:
        return UnknownOutcomeDecision('FILLED','APPLY_FILL_TRUTH',False)
    if fill>0:
        return UnknownOutcomeDecision('PARTIALLY_FILLED','APPLY_FILL_AND_RECONCILE_REMAINDER',False)
    for status in (user,opened):
        if status in TERMINAL|OPEN:
            return UnknownOutcomeDecision(status,'APPLY_EXCHANGE_TRUTH',False)
    return UnknownOutcomeDecision('UNKNOWN','QUERY_USER_STREAM_OPEN_ORDERS_AND_FILLS',True)
