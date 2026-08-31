from decimal import Decimal as D

from app.paper.engine import PaperBroker


def test_paper_market_partial_fill_models_fee_slippage_and_latency():
    broker=PaperBroker(D('10'),D('5'))
    fill=broker.fill_market('BUY',D('2'),D('99'),D('100'),latency_ms=73,available_qty=D('0.5'))
    assert fill.status=='PARTIALLY_FILLED'
    assert fill.qty==D('0.5')
    assert fill.price>D('100')
    assert fill.fee>0
    assert fill.latency_ms==73


def test_paper_position_stop_is_protective_and_closes_remaining_quantity():
    broker=PaperBroker(D('10'),D('5'))
    pos=broker.open_long('BTCUSDT',D('1'),D('99'),D('100'),D('95'),(D('105'),D('110'),D('115')))
    fills=broker.on_quote('BTCUSDT',D('94'),D('94.2'))
    assert len(fills)==1 and fills[0].reason=='STOP_LOSS'
    assert pos.closed and pos.remaining_qty==0
    assert pos.realized_pnl<0


def test_paper_partial_take_profits_close_30_30_40_without_overfill():
    broker=PaperBroker(D('10'),D('5'))
    pos=broker.open_long('ETHUSDT',D('10'),D('99'),D('100'),D('95'),(D('105'),D('110'),D('115')))
    first=broker.on_quote('ETHUSDT',D('105'),D('105.1'))
    second=broker.on_quote('ETHUSDT',D('110'),D('110.1'))
    third=broker.on_quote('ETHUSDT',D('116'),D('116.1'))
    assert [x.reason for x in first+second+third]==['TP1','TP2','TP3']
    assert [x.qty for x in first+second+third]==[D('3.00'),D('3.00'),D('4.00')]
    assert pos.closed and pos.remaining_qty==0
    assert pos.realized_pnl>0
