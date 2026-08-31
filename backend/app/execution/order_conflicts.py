from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class ProtectiveOrderEvidence:
    position_qty: Decimal
    stop_live_qty: Decimal
    take_profit_live_qty: Decimal
    replacement_generation: int
    current_generation: int
    reduce_only: bool
    market_type: str
    cancel_replace_in_flight: bool=False

@dataclass(frozen=True)
class ConflictDecision:
    safe: bool
    halt_new_risk: bool
    action: str
    reasons: tuple[str,...]


def evaluate_protective_conflicts(e:ProtectiveOrderEvidence)->ConflictDecision:
    q=abs(Decimal(e.position_qty)); stop=abs(Decimal(e.stop_live_qty)); tp=abs(Decimal(e.take_profit_live_qty)); reasons=[]
    if e.replacement_generation != e.current_generation: reasons.append('STALE_REPLACE_ORDER')
    # Independently-live SL + TP can over-close unless exchange-native OCO/order-list semantics are proven.
    if stop>0 and tp>0 and stop+tp>q: reasons.append('OVERLAPPING_STOP_TP_EXCEEDS_POSITION')
    if e.cancel_replace_in_flight: reasons.append('CANCEL_REPLACE_RACE_REQUIRES_RECONCILIATION')
    if e.market_type.upper() in {'FUTURES','PERPETUAL','MARGIN'} and q>0 and not e.reduce_only:
        reasons.append('REDUCE_ONLY_REQUIRED_FOR_PROTECTIVE_EXIT')
    if q==0 and (stop>0 or tp>0): reasons.append('ORPHAN_PROTECTIVE_ORDER')
    if reasons: return ConflictDecision(False,True,'RECONCILE_AND_CANCEL_UNSAFE_ORDERS',tuple(reasons))
    return ConflictDecision(True,False,'KEEP_PROTECTIVE_ORDERS',())
