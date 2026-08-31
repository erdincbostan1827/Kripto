from decimal import Decimal
import pytest
from app.universe.manager import SymbolEligibility,eligibility
from app.universe.scanner import Candidate,rank_candidates,market_breadth
from app.universe.routing import Instrument,choose_instrument,aggregate_underlying

def good(**kw):
 d=dict(symbol='BTCUSDT',listing_age_days=1000,quote_volume_24h=Decimal('100000000'),spread_bps=Decimal('2'),depth_notional=Decimal('1000000'),history_bars=1000,data_fresh=True); d.update(kw); return SymbolEligibility(**d)
def test_eligible(): assert eligibility(good())[0]
@pytest.mark.parametrize('field,value,reason',[('listing_age_days',1,'NEW_LISTING_QUARANTINE'),('quote_volume_24h',Decimal('1'),'LOW_VOLUME'),('spread_bps',Decimal('50'),'WIDE_SPREAD'),('depth_notional',Decimal('1'),'THIN_BOOK'),('history_bars',2,'INSUFFICIENT_HISTORY'),('data_fresh',False,'STALE_DATA'),('suspended',True,'NOT_TRADABLE')])
def test_exclusion_reasons(field,value,reason):
 ok,reasons=eligibility(good(**{field:value})); assert not ok and reason in reasons
def test_ranking_deterministic():
 x=[Candidate('B',80,.8,5),Candidate('A',80,.8,5),Candidate('C',90,.7,-1)]; assert [i.symbol for i in rank_candidates(x)]==['A','B']
def test_risk_blocked_removed(): assert rank_candidates([Candidate('A',99,.9,9,True)])==[]
def test_breadth(): assert market_breadth({'A':'BULLISH_TREND','B':'BEARISH_TREND'})=={'bullish_pct':.5,'bearish_pct':.5,'count':2}
def test_routing_prefers_cost():
 a=Instrument('x','BTCUSDT','BTC','USDT',2,100,1,1); b=Instrument('y','BTCUSDC','BTC','USDC',1,100,1,1); assert choose_instrument([a,b])==b
def test_routing_rejects_unapproved_quote():
 with pytest.raises(ValueError): choose_instrument([Instrument('x','BTCBTC','BTC','BTC',1,100,1,1)])
def test_underlying_aggregation(): assert aggregate_underlying({('x','BTCUSDT'):10,('y','BTCUSDC'):5},{('x','BTCUSDT'):'BTC',('y','BTCUSDC'):'BTC'})['BTC']==15


def test_point_in_time_universe_excludes_future_listing_and_delisted_symbol():
 from datetime import datetime,timezone
 from app.universe.manager import UniverseMembership,PointInTimeUniverse
 t=lambda y,m,d: datetime(y,m,d,tzinfo=timezone.utc)
 u=PointInTimeUniverse([
  UniverseMembership('OLD',t(2024,1,1),delisted_at=t(2025,6,1)),
  UniverseMembership('NEW',t(2025,7,1)),
 ])
 assert u.members(t(2025,5,1))==('OLD',)
 assert u.members(t(2025,6,15))==()
 assert u.members(t(2025,7,2))==('NEW',)


def test_point_in_time_universe_respects_suspension_window():
 from datetime import datetime,timezone
 from app.universe.manager import UniverseMembership,PointInTimeUniverse
 t=lambda d: datetime(2025,1,d,tzinfo=timezone.utc)
 u=PointInTimeUniverse([UniverseMembership('BTCUSDT',t(1),suspended_from=t(10),suspended_until=t(20))])
 assert u.contains('BTCUSDT',t(9))
 assert not u.contains('BTCUSDT',t(15))
 assert u.contains('BTCUSDT',t(21))


def test_no_candidate_explicitly_returns_no_trade():
 from app.universe.scanner import scanner_signal
 from app.core.enums import Signal
 signal,candidate=scanner_signal([Candidate('A',99,.9,-1),Candidate('B',90,.8,5,True)])
 assert signal==Signal.NO_TRADE and candidate is None


def test_scanner_respects_requested_10_50_and_configured_max_limits():
    items=[Candidate(f'S{i:03d}',100-i/1000,0.9,5) for i in range(80)]
    assert len(rank_candidates(items,limit=10))==10
    assert len(rank_candidates(items,limit=50))==50
    assert len(rank_candidates(items,limit=64))==64
    assert [x.symbol for x in rank_candidates(items,limit=10)] == [f'S{i:03d}' for i in range(10)]
