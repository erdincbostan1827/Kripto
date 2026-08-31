from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class ShadowDecision:
    champion_signal:str; challenger_signal:str; divergence:bool; real_order_allowed:bool=False
class LiveShadow:
    def compare(self,champion_signal,challenger_signal): return ShadowDecision(champion_signal,challenger_signal,champion_signal!=challenger_signal,False)
