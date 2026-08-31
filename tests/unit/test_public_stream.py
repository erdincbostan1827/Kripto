import asyncio
import json

import pytest

from app.exchange.public_stream import BinancePublicMarketStream


def test_public_stream_url_uses_documented_combined_stream_shapes():
    stream=BinancePublicMarketStream(['BTCUSDT'],timeframes=('1m','1h'))
    assert stream.url.startswith('wss://stream.binance.com:9443/stream?streams=')
    for name in ('btcusdt@trade','btcusdt@bookTicker','btcusdt@depth@100ms','btcusdt@kline_1m','btcusdt@kline_1h'):
        assert name in stream.url


def test_public_stream_parser_and_stale_detection():
    clock=[100.0]
    stream=BinancePublicMarketStream(['BTCUSDT'],monotonic=lambda:clock[0],stale_after_seconds=5)
    assert stream.is_stale()
    event=stream.parse(json.dumps({'stream':'btcusdt@trade','data':{'e':'trade','E':123,'s':'BTCUSDT','p':'1'}}))
    assert event.event_type=='trade' and event.symbol=='BTCUSDT' and event.event_time_ms==123
    stream.last_message_at=100.0
    assert not stream.is_stale(104.9)
    assert stream.is_stale(105.1)


@pytest.mark.asyncio
async def test_public_stream_reconnects_with_backoff_then_processes_event():
    stop=asyncio.Event(); sleeps=[]; calls={'n':0}; connect_kwargs=[]

    class FakeSocket:
        def __init__(self): self.items=[json.dumps({'stream':'btcusdt@bookTicker','data':{'s':'BTCUSDT','E':456,'b':'1','a':'2'}})]
        def __aiter__(self): return self
        async def __anext__(self):
            if not self.items: raise StopAsyncIteration
            return self.items.pop(0)

    class Ctx:
        def __init__(self,fail): self.fail=fail
        async def __aenter__(self):
            if self.fail: raise OSError('disconnect')
            return FakeSocket()
        async def __aexit__(self,*_): return False

    def connector(*_args,**_kwargs):
        calls['n']+=1
        connect_kwargs.append(_kwargs)
        return Ctx(calls['n']==1)

    async def sleep(delay): sleeps.append(delay)
    async def handler(event):
        assert event.symbol=='BTCUSDT'
        stop.set()

    stream=BinancePublicMarketStream(['BTCUSDT'],timeframes=(),connector=connector,sleep=sleep,jitter=lambda:0.0)
    await stream.run(handler,stop)
    assert stream.reconnects==1
    assert sleeps==[0.5]
    assert calls['n']==2
    assert connect_kwargs[-1]['ping_interval']==20 and connect_kwargs[-1]['ping_timeout']==20
    assert connect_kwargs[-1]['max_queue']==1024


def test_public_stream_detects_depth_packet_gap_delay_and_clock_jump():
    wall=[10_000]
    stream=BinancePublicMarketStream(['BTCUSDT'],timeframes=(),max_event_delay_ms=1000,wall_time_ms=lambda:wall[0],monotonic=lambda:100.0)
    a=stream.parse(json.dumps({'stream':'btcusdt@depth@100ms','data':{'e':'depthUpdate','E':9000,'s':'BTCUSDT','U':10,'u':12}}))
    b=stream.parse(json.dumps({'stream':'btcusdt@depth@100ms','data':{'e':'depthUpdate','E':8000,'s':'BTCUSDT','U':15,'u':16}}))
    stream.observe(a); stream.observe(b)
    stream.last_message_at=101.0
    assert stream.is_stale(100.0)
    health=stream.health(100.0)
    assert health.sequence_gaps==1
    assert health.delayed_events==1
    assert health.out_of_order_events>=1
    assert health.clock_anomaly
    assert not health.healthy


def test_public_stream_detects_duplicate_depth_update_as_out_of_order():
    wall=[1000]
    stream=BinancePublicMarketStream(['BTCUSDT'],timeframes=(),max_event_delay_ms=5000,wall_time_ms=lambda:wall[0])
    for first,final in [(1,2),(1,2)]:
        stream.observe(stream.parse(json.dumps({'stream':'btcusdt@depth@100ms','data':{'e':'depthUpdate','E':1000,'s':'BTCUSDT','U':first,'u':final}})))
    assert stream.out_of_order_events==1


@pytest.mark.asyncio
async def test_one_symbol_poison_message_isolated_without_reconnect_storm():
    stop=asyncio.Event(); handled=[]; calls={'n':0}
    class FakeSocket:
        def __init__(self): self.items=['not-json',json.dumps({'stream':'ethusdt@trade','data':{'e':'trade','E':1000,'s':'ETHUSDT'}})]
        def __aiter__(self): return self
        async def __anext__(self):
            if not self.items: raise StopAsyncIteration
            return self.items.pop(0)
    class Ctx:
        async def __aenter__(self): return FakeSocket()
        async def __aexit__(self,*_): return False
    def connector(*_a,**_kw): calls['n']+=1; return Ctx()
    async def handler(event): handled.append(event.symbol); stop.set()
    stream=BinancePublicMarketStream(['BTCUSDT','ETHUSDT'],timeframes=(),connector=connector,wall_time_ms=lambda:1000)
    await stream.run(handler,stop)
    assert handled==['ETHUSDT']
    assert stream.bad_messages==1
    assert stream.reconnects==0 and calls['n']==1
