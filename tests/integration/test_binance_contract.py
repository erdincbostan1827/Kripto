import httpx, pytest
from decimal import Decimal
from app.exchange.binance import BinanceSpotAdapter
from app.exchange.models import OrderIntent
from app.exchange.base import AmbiguousExecution, UnsupportedCapability


def handler(req):
    path = req.url.path
    if path.endswith('/exchangeInfo'):
        return httpx.Response(200, json={
            'rateLimits': [{'rateLimitType': 'REQUEST_WEIGHT', 'limit': 6000}],
            'symbols': [{
                'symbol': 'BTCUSDT', 'status': 'TRADING', 'baseAsset': 'BTC', 'quoteAsset': 'USDT',
                'permissions': ['SPOT'], 'ocoAllowed': False,
                'orderTypes': ['LIMIT', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
                'allowedSelfTradePreventionModes': ['EXPIRE_MAKER'],
                'filters': [
                    {'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
                    {'filterType': 'LOT_SIZE', 'stepSize': '0.00001', 'minQty': '0.00001', 'maxQty': '100'},
                    {'filterType': 'NOTIONAL', 'minNotional': '5', 'maxNotional': '1000000'},
                    {'filterType': 'TRAILING_DELTA', 'minTrailingAboveDelta': 10, 'maxTrailingAboveDelta': 2000},
                ],
            }],
        })
    if path.endswith('/open-symbol-list'):
        assert req.headers.get('X-MBX-APIKEY') == 'key'
        assert 'signature=' not in str(req.url)
        return httpx.Response(200, json=[{'openTime': 1770000000000, 'symbols': ['FOOUSDT', 'FOOUSDC']}])
    if path.endswith('/time'):
        return httpx.Response(200, json={'serverTime': 1760000000000})
    if path.endswith('/ticker/price'):
        return httpx.Response(200, json={'symbol': 'BTCUSDT', 'price': '60000'})
    if path.endswith('/order') and req.method == 'POST':
        return httpx.Response(200, json={'symbol': 'BTCUSDT', 'orderId': 7, 'clientOrderId': 'i1', 'status': 'NEW', 'type': 'LIMIT', 'side': 'BUY', 'origQty': '0.01', 'executedQty': '0', 'price': '60000', 'stopPrice': '0'})
    return httpx.Response(200, json=[])


def adapter():
    return BinanceSpotAdapter('key', 'secret', transport=httpx.MockTransport(handler))


def test_filters_from_exchange_info():
    assert adapter().get_symbol_filters('BTCUSDT').tick_size == Decimal('.01')


def test_capabilities_are_discovered_not_assumed():
    cap = adapter().get_capabilities('BTCUSDT')
    assert cap.stop and cap.take_profit and cap.trailing_stop
    assert cap.oco is False
    assert cap.stp_modes == ('EXPIRE_MAKER',)


def test_list_markets():
    assert adapter().list_markets() == ['BTCUSDT']


def test_rate_limits_runtime():
    assert adapter().get_rate_limits()[0]['limit'] == 6000


def test_exchange_symbol_and_asset_metadata_are_from_exchange_info():
    a = adapter()
    assert a.get_exchange_info()['symbols'][0]['symbol'] == 'BTCUSDT'
    meta = a.get_symbol_metadata('BTCUSDT')
    assert meta['base_asset'] == 'BTC' and meta['quote_asset'] == 'USDT' and meta['source'].endswith('exchangeInfo')
    asset = a.get_asset_metadata('BTC')
    assert asset['trading'] is True and asset['symbols'] == ['BTCUSDT']
    assert 'not inferred' in asset['limitations'][0]


def test_scheduled_listings_use_documented_market_data_endpoint_and_api_key_only():
    items = adapter().get_scheduled_listings()
    assert items == [{'open_time': 1770000000000, 'symbols': ('FOOUSDT', 'FOOUSDC'), 'source': 'GET /sapi/v1/spot/open-symbol-list'}]


def test_scheduled_listings_testnet_is_explicitly_unsupported():
    a = BinanceSpotAdapter('key', 'secret', testnet=True, transport=httpx.MockTransport(handler))
    with pytest.raises(UnsupportedCapability):
        a.get_scheduled_listings()


def test_submit_maps_order():
    a = adapter()
    x = a.submit_order(OrderIntent('i1', 'a', 'BTCUSDT', 'BUY', 'LIMIT', Decimal('.01'), Decimal('60000')))
    assert x.exchange_order_id == '7'


def test_signed_request_contains_signature():
    seen = {}
    def h(req):
        seen['url'] = str(req.url)
        return httpx.Response(200, json=[])
    a = BinanceSpotAdapter('key', 'secret', transport=httpx.MockTransport(h))
    a.get_open_orders('BTCUSDT')
    assert 'signature=' in seen['url'] and 'timestamp=' in seen['url']


def test_mutation_5xx_is_ambiguous():
    def h(req):
        if req.url.path.endswith('/exchangeInfo'):
            return httpx.Response(200, json={'symbols': [{'symbol': 'BTCUSDT', 'status': 'TRADING', 'orderTypes': ['LIMIT'], 'filters': [{'filterType': 'PRICE_FILTER', 'tickSize': '0.01'}, {'filterType': 'LOT_SIZE', 'stepSize': '0.001', 'minQty': '0.001', 'maxQty': '100'}, {'filterType': 'MIN_NOTIONAL', 'minNotional': '5'}]}]})
        return httpx.Response(500, json={'msg': 'internal'})
    a = BinanceSpotAdapter('key', 'secret', transport=httpx.MockTransport(h))
    with pytest.raises(AmbiguousExecution):
        a.submit_order(OrderIntent('i', 'a', 'BTCUSDT', 'BUY', 'LIMIT', Decimal('.01'), Decimal('60000')))


def test_get_order_requires_a_stable_query_identifier():
    with pytest.raises(ValueError):
        adapter().get_order('BTCUSDT')

def test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract():
    seen=[]
    def h(req):
        if req.url.path.endswith('/exchangeInfo'):
            return handler(req)
        if req.url.path.endswith('/order') and req.method=='POST':
            params=dict(req.url.params)
            seen.append(params['type'])
            return httpx.Response(200,json={'symbol':'BTCUSDT','orderId':len(seen),'clientOrderId':params['newClientOrderId'],'status':'NEW','type':params['type'],'side':params['side'],'origQty':params['quantity'],'executedQty':'0','price':params.get('price','0'),'stopPrice':params.get('stopPrice','0')})
        if req.url.path.endswith('/openOrders'):
            return httpx.Response(200,json=[])
        return handler(req)
    a=BinanceSpotAdapter('key','secret',transport=httpx.MockTransport(h))
    common={'account_id':'acct','symbol':'BTCUSDT','side':'BUY','quantity':Decimal('0.01')}
    a.create_market_order(intent_id='m1',**common)
    a.create_limit_order(intent_id='l1',price=Decimal('60000'),**common)
    a.create_stop_order(intent_id='s1',price=Decimal('59000'),stop_price=Decimal('59100'),**common)
    a.create_take_profit_order(intent_id='t1',price=Decimal('62000'),stop_price=Decimal('61900'),**common)
    assert seen==['MARKET','LIMIT','STOP_LOSS_LIMIT','TAKE_PROFIT_LIMIT']
    assert a.cancel_all_orders('BTCUSDT')==[]

def test_exchange_adapter_read_and_cancel_query_contract_methods():
    def h(req):
        path=req.url.path
        if path.endswith('/exchangeInfo'): return handler(req)
        if path.endswith('/time'): return handler(req)
        if path.endswith('/ticker/price'): return handler(req)
        if path.endswith('/depth'): return httpx.Response(200,json={'lastUpdateId':1,'bids':[['59999','1']],'asks':[['60001','1']]})
        if path.endswith('/account'): return httpx.Response(200,json={'balances':[{'asset':'USDT','free':'10','locked':'2'}]})
        if path.endswith('/openOrders'): return httpx.Response(200,json=[])
        if path.endswith('/klines'): return httpx.Response(200,json=[[1,'1','1','1','1','1',2]])
        if path.endswith('/order') and req.method=='GET':
            return httpx.Response(200,json={'symbol':'BTCUSDT','orderId':7,'clientOrderId':'i1','status':'NEW','type':'LIMIT','side':'BUY','origQty':'0.01','executedQty':'0','price':'60000','stopPrice':'0'})
        if path.endswith('/order') and req.method=='DELETE':
            return httpx.Response(200,json={'symbol':'BTCUSDT','orderId':7,'clientOrderId':'i1','status':'CANCELED','type':'LIMIT','side':'BUY','origQty':'0.01','executedQty':'0','price':'60000','stopPrice':'0'})
        return httpx.Response(404,json={'msg':'unexpected'})
    a=BinanceSpotAdapter('key','secret',transport=httpx.MockTransport(h))
    assert a.get_ticker('BTCUSDT')['price']=='60000'
    assert a.get_order_book('BTCUSDT')['lastUpdateId']==1
    assert a.get_balance()['USDT']==Decimal('12')
    assert a.get_positions()==[]
    assert a.get_open_orders('BTCUSDT')==[]
    assert len(a.get_klines('BTCUSDT','1m',1))==1
    assert a.get_order('BTCUSDT',order_id='7').exchange_order_id=='7'
    assert a.cancel_order('BTCUSDT','7').state.value=='CANCELLED'
    assert a.get_server_time().tzinfo is not None
    assert a.get_trading_status('BTCUSDT')['tradable'] is True
    assert a.get_exchange_status()['status']=='ONLINE'


def test_rate_limit_response_headers_are_parsed_and_exposed_without_guessing_missing_headers():
    def h(req):
        if req.url.path.endswith('/ticker/price'):
            return httpx.Response(200, json={'symbol': 'BTCUSDT', 'price': '60000'}, headers={
                'X-MBX-USED-WEIGHT-1M': '123',
                'X-MBX-ORDER-COUNT-10S': '7',
                'Retry-After': '2',
            })
        return handler(req)
    a = BinanceSpotAdapter('key', 'secret', transport=httpx.MockTransport(h))
    a.get_ticker('BTCUSDT')
    observation = a.get_last_rate_limit_observation()
    assert observation['X-MBX-USED-WEIGHT-1M'] == 123
    assert observation['X-MBX-ORDER-COUNT-10S'] == 7
    assert observation['RETRY-AFTER'] == 2


def test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed():
    a = adapter()
    mapped = a._map_order({
        'symbol': 'BTCUSDT', 'orderId': 999, 'clientOrderId': 'future',
        'status': 'FUTURE_NEW_STATUS', 'type': 'LIMIT', 'side': 'BUY',
        'origQty': '0.01', 'executedQty': '0', 'price': '60000', 'stopPrice': '0',
        'newFutureField': {'nested': True},
    })
    assert mapped.state.value == 'UNKNOWN'
    assert mapped.exchange_order_id == '999'


def test_capability_snapshot_is_content_addressed_and_changes_when_filters_change():
    a = adapter()
    first = a.get_capability_snapshot('BTCUSDT')
    second = a.get_capability_snapshot('BTCUSDT')
    assert first['version'] == second['version']
    assert first['source'].endswith('exchangeInfo')
    a._info['symbols'][0]['filters'][0]['tickSize'] = '0.10'
    changed = a.get_capability_snapshot('BTCUSDT')
    assert changed['version'] != first['version']


def test_adapter_manifest_captures_contract_limits_filters_and_auth_profile():
    manifest = adapter().get_adapter_manifest('BTCUSDT')
    assert manifest['exchange'] == 'BINANCE'
    assert manifest['market_type'] == 'SPOT'
    assert manifest['api_family'].endswith('v3')
    assert 'HMAC-SHA256' in manifest['authentication_type']
    assert '/api/v3/order' in manifest['supported_endpoints']
    assert manifest['limits_snapshot'][0]['rateLimitType'] == 'REQUEST_WEIGHT'
    assert len(manifest['filters_snapshot_version']) == 16


def test_missing_required_order_contract_field_fails_explicitly():
    with pytest.raises(ValueError, match='required order field missing'):
        adapter()._map_order({'symbol': 'BTCUSDT', 'status': 'NEW'})


def test_http_429_maps_to_explicit_rate_limit_error_and_retry_after():
    from app.exchange.base import ExchangeRateLimited
    def h(req):
        return httpx.Response(429, json={'code': -1003, 'msg': 'Too many requests'}, headers={'Retry-After': '3', 'X-MBX-USED-WEIGHT-1M': '6000'})
    a = BinanceSpotAdapter('key', 'secret', transport=httpx.MockTransport(h))
    with pytest.raises(ExchangeRateLimited) as exc:
        a.get_ticker('BTCUSDT')
    assert exc.value.retry_after == 3
    assert a.get_last_rate_limit_observation()['X-MBX-USED-WEIGHT-1M'] == 6000
