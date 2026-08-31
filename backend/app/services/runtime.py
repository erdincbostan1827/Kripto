from __future__ import annotations
from dataclasses import asdict
from datetime import datetime,timezone
from decimal import Decimal
from app.exchange.mock import MockExchange
from app.services.pipeline import analyze
from app.universe.manager import SymbolEligibility,eligibility
from app.universe.scanner import Candidate,rank_candidates,market_breadth

class RuntimeFacade:
    """Read/query facade. Default DEV/PAPER provider is explicitly MOCK, never presented as live venue truth."""
    def __init__(self,exchange=None,source='MOCK'):
        self.exchange=exchange or MockExchange(); self.source=source
    def market(self,symbol):
        if symbol not in self.exchange.list_markets(): raise KeyError(symbol)
        t=self.exchange.get_ticker(symbol); b=self.exchange.get_order_book(symbol)
        return {'source':self.source,'symbol':symbol,'ticker':t,'order_book':b,'data_timestamp':t['event_time']}
    def signal(self,symbol,timeframe='1h'):
        d=analyze(self.exchange.get_klines(symbol,timeframe,250),timeframe); x=asdict(d); x['signal']=str(d.signal); x['source']=self.source; x['symbol']=symbol; x['timeframe']=timeframe; return x
    def signals(self): return [self.signal(s) for s in self.exchange.list_markets()]
    def positions(self): return {'source':self.source,'items':self.exchange.get_positions()}
    def orders(self): return {'source':self.source,'items':[asdict(x) for x in self.exchange.get_open_orders()]}
    def portfolio(self):
        balances=self.exchange.get_balance(); return {'source':self.source,'balances':balances,'open_positions':len(self.exchange.get_positions()),'open_orders':len(self.exchange.get_open_orders())}
    def universe(self):
        rows=[]; excluded={}
        for symbol in self.exchange.list_markets():
            book=self.exchange.get_order_book(symbol); bid=book['bids'][0][0]; ask=book['asks'][0][0]; mid=(bid+ask)/2; spread=(ask-bid)/mid*Decimal('10000')
            meta=SymbolEligibility(symbol,365,Decimal('100000000'),spread,Decimal('1000000'),500,True)
            ok,reasons=eligibility(meta); rows.append({'symbol':symbol,'eligible':ok,'reasons':reasons,'source':self.source})
            if reasons: excluded[symbol]=reasons
        return {'source':self.source,'timestamp':datetime.now(timezone.utc),'members':[x['symbol'] for x in rows if x['eligible']],'items':rows,'excluded':excluded}
    def scanner(self):
        raw=[]; regimes={}; details={}
        for s in self.exchange.list_markets():
            x=self.signal(s); regimes[s]=x['regime']; details[s]=x; raw.append(Candidate(s,float(x['score']),float(x['confidence']),max(0,float(x['score'])-50),x['signal']=='NO_TRADE'))
        ranked=rank_candidates(raw,10)
        items=[]
        now=datetime.now(timezone.utc)
        for rank,c in enumerate(ranked, start=1):
            d=details[c.symbol]
            ticker=self.exchange.get_ticker(c.symbol); book=self.exchange.get_order_book(c.symbol)
            price=Decimal(str(ticker.get('last_price', ticker.get('price'))))
            bid=Decimal(str(book['bids'][0][0])); ask=Decimal(str(book['asks'][0][0])); mid=(bid+ask)/2
            spread_bps=float((ask-bid)/mid*Decimal('10000')) if mid else None
            candles=self.exchange.get_klines(c.symbol,'1h',24)
            closes=[float(x['close']) for x in candles]
            returns=[closes[i]/closes[i-1]-1 for i in range(1,len(closes)) if closes[i-1]]
            volatility=(sum((r-(sum(returns)/len(returns)))**2 for r in returns)/len(returns))**0.5 if returns else 0.0
            quote_volume=float(sum(Decimal(str(x['close']))*Decimal(str(x['volume'])) for x in candles))
            event_time=ticker.get('event_time')
            age=(now-event_time).total_seconds() if isinstance(event_time,datetime) else None
            liquidity_score=max(0.0,min(100.0,100.0-(spread_bps or 100.0)))
            item=asdict(c)
            item.update({'signal':d['signal'],'regime':d['regime'],'reasons':d.get('reasons',()),'data_timestamp':d.get('data_timestamp'),'price':float(price),'quote_volume_24h':quote_volume,'spread_bps':spread_bps,'volatility':volatility,'liquidity_score':liquidity_score,'rank':rank,'block_reason':None,'data_age_seconds':max(0.0,age) if age is not None else None})
            items.append(item)
        return {'source':self.source,'items':items,'breadth':market_breadth(regimes)}
    def symbol_metadata(self,symbol):
        f=self.exchange.get_symbol_filters(symbol); c=self.exchange.get_capabilities(symbol)
        return {'source':self.source,'symbol':symbol,'filters':asdict(f),'capabilities':asdict(c),'trading_status':self.exchange.get_trading_status(symbol)}
