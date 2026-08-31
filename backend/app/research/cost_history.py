from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class CostVintage:
    symbol: str
    valid_from: datetime
    valid_to: datetime|None
    maker_fee_bps: float
    taker_fee_bps: float
    fee_discount_bps: float
    vip_tier: str
    funding_bps: float
    borrow_bps: float
    min_notional: float
    tick_size: float
    source: str
    assumption: str
    sensitivity_bps: tuple[float,float]

    def contains(self, ts: datetime) -> bool:
        return self.valid_from<=ts and (self.valid_to is None or ts<self.valid_to)

class PointInTimeCostModel:
    def __init__(self, vintages): self.vintages=tuple(vintages)
    def resolve(self,symbol,ts):
        rows=[v for v in self.vintages if v.symbol==symbol and v.contains(ts)]
        if len(rows)!=1: raise ValueError('cost vintage missing or ambiguous')
        return rows[0]
    def estimate_bps(self,symbol,ts,*,maker:bool,include_funding=True,include_borrow=False):
        v=self.resolve(symbol,ts); fee=(v.maker_fee_bps if maker else v.taker_fee_bps)-v.fee_discount_bps
        return max(0.0,fee)+(v.funding_bps if include_funding else 0)+(v.borrow_bps if include_borrow else 0)
