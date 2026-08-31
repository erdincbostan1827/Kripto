from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
@dataclass
class StrategyLot:
    strategy_id:str; symbol:str; quantity:Decimal; cost_basis:Decimal; realized_pnl:Decimal=Decimal('0')
class OwnershipBook:
    def __init__(self): self.lots:dict[tuple[str,str],StrategyLot]={}
    def allocate(self,strategy_id,symbol,quantity,cost_basis):
        key=(strategy_id,symbol); self.lots[key]=StrategyLot(strategy_id,symbol,Decimal(quantity),Decimal(cost_basis)); return self.lots[key]
    def exit(self,strategy_id,symbol,quantity,price):
        lot=self.lots[(strategy_id,symbol)]; q=Decimal(quantity)
        if q>lot.quantity: raise ValueError('strategy cannot exit another strategy exposure')
        pnl=(Decimal(price)-lot.cost_basis)*q; lot.quantity-=q; lot.realized_pnl+=pnl; return pnl
