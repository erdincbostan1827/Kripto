from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class PnLAttribution:
    signal_alpha:float; entry_timing:float; exit_timing:float; spread_cost:float; slippage:float; fees:float; funding_borrow:float; adverse_selection:float; missed_fill:float; stop_gap:float
    @property
    def total(self): return self.signal_alpha+self.entry_timing+self.exit_timing-self.spread_cost-self.slippage-self.fees-self.funding_borrow-self.adverse_selection-self.missed_fill-self.stop_gap

def implementation_shortfall(decision_price,fill_price,side='BUY'):
    sign=1 if side=='BUY' else -1; return sign*(fill_price-decision_price)/decision_price
