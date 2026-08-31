from datetime import datetime,timedelta,timezone
from decimal import Decimal as D
import pytest
from app.data.time_alignment import AlignedCandle,align_latest_final,align_multi_timeframe,MonotonicTimer
from app.backtest.execution_model import next_bar_market_fill,conservative_exit_long,conservative_limit_fill,EXECUTION_MODEL_VERSION

def c(tf,o,minutes,price): return AlignedCandle(tf,o,o+timedelta(minutes=minutes),{'close':price})

def test_time_alignment_never_uses_future_higher_timeframe_candle():
    base=datetime(2026,1,1,tzinfo=timezone.utc); decision=base+timedelta(minutes=70)
    h1=[c('1h',base,60,100),c('1h',base+timedelta(minutes=60),60,999)]
    m5=[c('5m',base+timedelta(minutes=60),5,101),c('5m',base+timedelta(minutes=65),5,102)]
    out=align_multi_timeframe({'1h':h1,'5m':m5},decision)
    assert out['1h'].payload['close']==100 and out['5m'].payload['close']==102

def test_time_alignment_rejects_naive_or_nonfinal_and_separates_open_close_time():
    base=datetime(2026,1,1,tzinfo=timezone.utc)
    with pytest.raises(ValueError): align_latest_final([c('1h',base,60,100)],base+timedelta(minutes=30))
    bad=AlignedCandle('1h',base,base,{'close':1})
    with pytest.raises(ValueError): align_latest_final([bad],base+timedelta(hours=2))

def test_monotonic_timer_rejects_clock_regression():
    vals=iter([10.0,11.0,10.5]); t=MonotonicTimer(lambda:next(vals)); start=t.sample(); assert t.elapsed(start)==1.0
    with pytest.raises(RuntimeError,match='MONOTONIC_CLOCK_REGRESSION'): t.sample()

def test_market_fill_is_next_bar_open_with_slippage_and_versioned():
    f=next_bar_market_fill('BUY',D('101'),D('10'))
    assert f.price==D('101')*D('1.001') and f.reason=='NEXT_BAR_MARKET' and f.model_version==EXECUTION_MODEL_VERSION

def test_conservative_intrabar_chooses_stop_when_stop_and_tp_both_touch():
    f=conservative_exit_long(bar_open=D('100'),bar_high=D('110'),bar_low=D('90'),stop=D('95'),tp=D('105'),slippage_bps=D('10'))
    assert f.reason=='STOP_CONSERVATIVE' and f.price < D('95')

def test_stop_gap_through_never_assumes_guaranteed_stop_price():
    f=conservative_exit_long(bar_open=D('90'),bar_high=D('96'),bar_low=D('88'),stop=D('95'),tp=D('110'),slippage_bps=D('10'))
    assert f.reason=='STOP_GAP_THROUGH' and f.price < D('90')

def test_limit_touch_is_not_guaranteed_fill_and_queue_liquidity_can_block():
    assert not conservative_limit_fill('BUY',D('100'),D('101'),D('102'),D('100')).filled
    assert not conservative_limit_fill('BUY',D('100'),D('101'),D('102'),D('99'),queue_fill_ratio=D('0')).filled
    assert not conservative_limit_fill('BUY',D('100'),D('101'),D('102'),D('99'),available_liquidity=D('0')).filled
    assert conservative_limit_fill('BUY',D('100'),D('101'),D('102'),D('99'),available_liquidity=D('1')).filled
