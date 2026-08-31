from __future__ import annotations
from dataclasses import dataclass,field
from decimal import Decimal
from datetime import datetime,timezone
from app.core.enums import MarketType,OrderState

@dataclass(frozen=True)
class SymbolFilters:
    tick_size:Decimal; step_size:Decimal; min_qty:Decimal; max_qty:Decimal; min_notional:Decimal; max_notional:Decimal|None=None; max_orders:int|None=None
@dataclass(frozen=True)
class Capabilities:
    market:bool=True; limit:bool=True; stop:bool=False; take_profit:bool=False; trailing_stop:bool=False; oco:bool=False; post_only:bool=False; reduce_only:bool=False; client_order_id:bool=True; testnet:bool=True; private_stream:bool=True; stp_modes:tuple[str,...]=(); time_in_force:tuple[str,...]=('GTC','IOC','FOK')
@dataclass(frozen=True)
class OrderIntent:
    intent_id:str; account_id:str; symbol:str; side:str; order_type:str; quantity:Decimal; price:Decimal|None=None; stop_price:Decimal|None=None; market_type:MarketType=MarketType.SPOT; strategy_id:str='default'; reduce_only:bool=False; client_order_id:str|None=None
@dataclass
class OrderRecord:
    intent_id:str; account_id:str; symbol:str; side:str; order_type:str; quantity:Decimal; state:OrderState=OrderState.CREATED; price:Decimal|None=None; stop_price:Decimal|None=None; exchange_order_id:str|None=None; client_order_id:str|None=None; filled_quantity:Decimal=Decimal('0'); average_fill_price:Decimal|None=None; fees:dict[str,Decimal]=field(default_factory=dict); updated_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
