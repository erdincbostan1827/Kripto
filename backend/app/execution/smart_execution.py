from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionContext:
    urgency:float; alpha_half_life_seconds:float; spread_bps:float; depth_score:float; expected_slippage_bps:float
    adverse_selection:float; maker_taker_fee_diff_bps:float; fill_probability:float; time_to_fill_seconds:float
    rejection_risk:float; volatility:float; notional:float

def choose_policy(x:ExecutionContext,*,slice_threshold=100_000)->str:
    if x.rejection_risk>.5 or x.depth_score<.1: return 'NO_TRADE'
    if x.urgency>.8 or x.alpha_half_life_seconds < max(1,x.time_to_fill_seconds): return 'AGGRESSIVE_LIMIT'
    if x.fill_probability>.75 and x.maker_taker_fee_diff_bps>0 and x.adverse_selection<.4: return 'PASSIVE_POST_ONLY'
    if x.urgency>.6: return 'IOC'
    return 'SLICED_LIMIT' if x.notional>slice_threshold else 'LIMIT'

@dataclass(frozen=True)
class ProtectiveOrderSpec:
    trigger_source:str
    trigger_direction:str
    reduce_only:bool
    close_position:bool
    working_type:str|None
    quantity:float
    protected_position_quantity:float

    def __post_init__(self):
        if self.trigger_source not in {'LAST','MARK','INDEX','BID','ASK','MID'}: raise ValueError('invalid trigger source')
        if self.trigger_direction not in {'ABOVE','BELOW'}: raise ValueError('invalid trigger direction')
        if not self.reduce_only: raise ValueError('protective order must be reduce-only')
        if self.quantity<=0 or self.protected_position_quantity<=0 or self.quantity>self.protected_position_quantity: raise ValueError('invalid protective quantity')
