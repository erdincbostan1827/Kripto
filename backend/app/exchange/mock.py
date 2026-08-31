from __future__ import annotations
from decimal import Decimal
from datetime import datetime,timezone,timedelta
from app.core.enums import OrderState
from .base import ExchangeAdapter
from .models import *
class MockExchange(ExchangeAdapter):
    def __init__(self):
        self.orders:dict[str,OrderRecord]={}; self.prices={'BTCUSDT':Decimal('60000'),'ETHUSDT':Decimal('3000')}
        self.filters={s:SymbolFilters(Decimal('0.01'),Decimal('0.00001'),Decimal('0.00001'),Decimal('1000'),Decimal('5')) for s in self.prices}
        self.cap=Capabilities(stop=True,take_profit=True,oco=True,post_only=True,stp_modes=('EXPIRE_MAKER','EXPIRE_TAKER','EXPIRE_BOTH'))
        self.balances={'USDT':Decimal('100000'),'BTC':Decimal('1'),'ETH':Decimal('10')}; self.fail_mode=None
    def get_ticker(self,symbol): return {'symbol':symbol,'price':self.prices[symbol],'event_time':datetime.now(timezone.utc)}
    def get_order_book(self,symbol):
        p=self.prices[symbol]; return {'symbol':symbol,'last_update_id':1,'bids':[(p-Decimal('1'),Decimal('5'))],'asks':[(p+Decimal('1'),Decimal('5'))]}
    def get_balance(self): return dict(self.balances)
    def get_positions(self): return []
    def get_open_orders(self,symbol=None): return [o for o in self.orders.values() if o.state not in {OrderState.FILLED,OrderState.CANCELLED,OrderState.REJECTED,OrderState.FAILED} and (not symbol or o.symbol==symbol)]
    def get_klines(self,symbol,interval,limit=500):
        seconds={'1m':60,'3m':180,'5m':300,'15m':900,'30m':1800,'1h':3600,'4h':14400,'1d':86400}[interval]
        end=datetime.now(timezone.utc).replace(second=0,microsecond=0)-timedelta(seconds=seconds)
        out=[]; p=self.prices[symbol]
        for i in range(limit):
            t=end-timedelta(seconds=seconds*(limit-1-i)); x=p+Decimal(i-limit//2)/Decimal('10')
            out.append({'open_time':t,'close_time':t+timedelta(seconds=seconds),'open':x,'high':x+2,'low':x-2,'close':x+1,'volume':Decimal('100')+i,'closed':True})
        return out
    def submit_order(self,intent):
        if self.fail_mode=='ambiguous': raise TimeoutError('ambiguous transport outcome')
        if intent.intent_id in self.orders: return self.orders[intent.intent_id]
        if self.fail_mode=='reject':
            rec=OrderRecord(intent.intent_id,intent.account_id,intent.symbol,intent.side,intent.order_type,intent.quantity,OrderState.REJECTED,intent.price,intent.stop_price,exchange_order_id=f'MOCK-{len(self.orders)+1}',client_order_id=intent.client_order_id or intent.intent_id)
            self.orders[intent.intent_id]=rec
            return rec
        rec=OrderRecord(intent.intent_id,intent.account_id,intent.symbol,intent.side,intent.order_type,intent.quantity,OrderState.ACKNOWLEDGED,intent.price,intent.stop_price,exchange_order_id=f'MOCK-{len(self.orders)+1}',client_order_id=intent.client_order_id or intent.intent_id)
        self.orders[intent.intent_id]=rec; return rec
    def cancel_order(self,symbol,order_id):
        rec=next(o for o in self.orders.values() if o.exchange_order_id==order_id); rec.state=OrderState.CANCELLED; return rec
    def get_order(self,symbol,order_id=None,client_order_id=None):
        for o in self.orders.values():
            if o.symbol==symbol and ((order_id and o.exchange_order_id==order_id) or (client_order_id and o.client_order_id==client_order_id)): return o
        return None
    def list_markets(self): return list(self.prices)
    def get_symbol_filters(self,symbol): return self.filters[symbol]
    def get_capabilities(self,symbol): return self.cap
    def get_server_time(self): return datetime.now(timezone.utc)
