from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ShadowObservation:
    champion_signal:str; challenger_signal:str; hypothetical_order_intent:str; expected_fill:float|None; actual_market_price:float
    estimated_cost_bps:float; gates_passed:bool; challenger_order_sent:bool=False
    def __post_init__(self):
        if self.challenger_order_sent: raise ValueError('challenger is shadow-only')
    @property
    def divergence(self)->float|None:
        return None if self.expected_fill is None else self.actual_market_price-self.expected_fill
