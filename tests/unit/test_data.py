from datetime import datetime,timezone,timedelta
from decimal import Decimal
import pytest
from app.data.quality import ensure_fresh,validate_candles,spread_bps
from app.data.orderbook import LocalOrderBook,OrderBookIntegrityError

def candle(t): return {'open_time':t,'close_time':t+timedelta(minutes=1),'open':1,'high':2,'low':.5,'close':1.5,'volume':10,'closed':True}
def test_fresh(): assert ensure_fresh(datetime.now(timezone.utc)-timedelta(seconds=1),10)<10
def test_stale():
    with pytest.raises(ValueError): ensure_fresh(datetime.now(timezone.utc)-timedelta(seconds=11),10)
def test_future():
    with pytest.raises(ValueError): ensure_fresh(datetime.now(timezone.utc)+timedelta(seconds=1),10)
def test_naive_time_rejected():
    with pytest.raises(ValueError): ensure_fresh(datetime.now(),10)
def test_candle_sequence_good():
    t=datetime(2026,1,1,tzinfo=timezone.utc); assert validate_candles([candle(t),candle(t+timedelta(minutes=1))],60)
def test_candle_gap():
    t=datetime(2026,1,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError): validate_candles([candle(t),candle(t+timedelta(minutes=2))],60)
def test_duplicate_candle():
    t=datetime(2026,1,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError): validate_candles([candle(t),candle(t)],60)
def test_nonfinal_candle():
    t=datetime(2026,1,1,tzinfo=timezone.utc); x=candle(t); x['closed']=False
    with pytest.raises(ValueError): validate_candles([x],60)
def test_warmup():
    t=datetime(2026,1,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError): validate_candles([candle(t)],60,min_bars=2)
def test_spread_bps(): assert spread_bps(Decimal('99'),Decimal('101'))==Decimal('200')
def test_crossed_spread_rejected():
    with pytest.raises(ValueError): spread_bps(Decimal('101'),Decimal('100'))
def test_orderbook_snapshot():
    b=LocalOrderBook(); b.load_snapshot(10,[('99','2')],[('101','2')]); assert b.best_bid==Decimal('99') and b.best_ask==Decimal('101')
def test_orderbook_delta():
    b=LocalOrderBook(); b.load_snapshot(10,[('99','2')],[('101','2')]); b.apply_delta(11,11,[('100','1')],[]); assert b.best_bid==Decimal('100')
def test_orderbook_gap():
    b=LocalOrderBook(); b.load_snapshot(10,[('99','2')],[('101','2')])
    with pytest.raises(OrderBookIntegrityError): b.apply_delta(12,12,[],[])
def test_orderbook_crossed():
    b=LocalOrderBook()
    with pytest.raises(OrderBookIntegrityError): b.load_snapshot(1,[('102','1')],[('101','1')])


def test_orderbook_discards_stale_delta_and_tracks_telemetry():
    clock=[100.0]
    b=LocalOrderBook(monotonic=lambda:clock[0])
    b.load_snapshot(10,[('99','2')],[('101','2')])
    assert b.resync_count==1 and b.valid
    assert b.apply_delta(9,10,[('98','3')],[]) is False
    assert b.stale_event_count==1 and b.best_bid==Decimal('99')
    clock[0]=102.5
    assert b.age_seconds()==Decimal('2.5') or b.age_seconds()==2.5


def test_orderbook_gap_invalidates_until_fresh_snapshot_resync():
    b=LocalOrderBook()
    b.load_snapshot(10,[('99','2')],[('101','2')])
    with pytest.raises(OrderBookIntegrityError,match='sequence gap'):
        b.apply_delta(12,12,[],[])
    assert not b.valid and b.gap_count==1
    with pytest.raises(OrderBookIntegrityError,match='INVALID'):
        b.require_valid()
    with pytest.raises(OrderBookIntegrityError,match='snapshot required'):
        b.apply_delta(13,13,[],[])
    b.load_snapshot(20,[('100','3')],[('102','1')])
    assert b.valid and b.resync_count==2 and b.require_valid() is b


def test_orderbook_exposes_bid_ask_spread_lock_and_depth_imbalance():
    b=LocalOrderBook()
    b.load_snapshot(1,[('99','3')],[('101','1')])
    assert b.best_bid==Decimal('99') and b.best_ask==Decimal('101')
    assert b.spread==Decimal('2')
    assert not b.locked
    assert b.depth_imbalance==Decimal('0.5')
