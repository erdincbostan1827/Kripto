from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app,base_url='http://localhost')

def test_market_and_signal_are_functional_and_source_labeled():
    m=c.get('/api/v1/market/BTCUSDT'); assert m.status_code==200 and m.json()['source']=='MOCK'
    s=c.get('/api/v1/signals/BTCUSDT'); assert s.status_code==200 and s.json()['source']=='MOCK' and 'reasons' in s.json()

def test_portfolio_and_order_endpoints_do_not_invent_data():
    assert c.get('/api/v1/positions').json()['items']==[]
    assert c.get('/api/v1/performance').json()['status']=='NO_DATA'
    assert c.get('/api/v1/portfolio/correlation').json()['sample_count']==0

def test_universe_scanner_metadata_and_breadth():
    u=c.get('/api/v1/universe'); assert u.status_code==200 and u.json()['source']=='MOCK' and u.json()['members']
    sc=c.get('/api/v1/scanner'); assert sc.status_code==200 and 'breadth' in sc.json(); assert sc.json()['items']; assert {'signal','confidence','net_edge_bps','regime','reasons','price','quote_volume_24h','spread_bps','volatility','liquidity_score','rank','block_reason','data_age_seconds'} <= set(sc.json()['items'][0])
    md=c.get('/api/v1/symbols/BTCUSDT/metadata'); assert md.status_code==200 and md.json()['filters']['tick_size']==0.01
    assert c.get('/api/v1/market-breadth').status_code==200

def test_required_mutation_endpoints_work_in_dev_paper():
    assert c.post('/api/v1/universe/refresh',json={'reason':'refresh universe'}).status_code==200
    assert c.post('/api/v1/scanner/run',json={'reason':'run scanner'}).status_code==200


def test_dashboard_endpoint_exposes_user_facing_operational_snapshot():
    r=c.get('/api/v1/dashboard'); assert r.status_code==200
    d=r.json()
    for key in ['mode','exchange_status','data_status','engine_status','risk_status','system_safe','user_message','top_candidates','open_positions','open_orders','critical_alerts','selected_symbol','selected_price','recent_signals']:
        assert key in d
    assert d['mode'].endswith('PAPER')
    assert d['source']=='MOCK'
    assert d['selected_symbol'] in {'BTCUSDT','ETHUSDT'} and d['selected_price'] is not None
    assert d['recent_signals']
