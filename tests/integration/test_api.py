from fastapi.testclient import TestClient
from datetime import datetime,timezone,timedelta
from app.main import app
client=TestClient(app,base_url='http://localhost')
def candle(t,p): return {'open_time':t.isoformat(),'close_time':(t+timedelta(hours=1)).isoformat(),'open':p,'high':p+1,'low':p-1,'close':p+.5,'volume':100,'closed':True}
def test_compatibility(): assert client.get('/api/v1/compatibility').json()['api_version']=='v1'
def test_health(): assert client.get('/health').json()['ready_for_new_risk'] is True
def test_ready(): assert client.get('/ready').status_code==200
def test_metrics(): assert client.get('/metrics').status_code==200
def test_status_paper(): assert client.get('/api/v1/status').json()['mode']=='PAPER'
def test_analyze():
 t=datetime(2020,1,1,tzinfo=timezone.utc); cs=[candle(t+timedelta(hours=i),100+i) for i in range(60)]; r=client.post('/api/v1/analyze',json={'symbol':'BTCUSDT','timeframe':'1h','candles':cs}); assert r.status_code==200 and 'signal' in r.json()
def test_analyze_gap_rejected():
 t=datetime(2020,1,1,tzinfo=timezone.utc); cs=[candle(t,100),candle(t+timedelta(hours=2),101)]; r=client.post('/api/v1/analyze',json={'symbol':'BTCUSDT','timeframe':'1h','candles':cs}); assert r.status_code==422
def test_trading_start_stop():
 assert client.post('/api/v1/trading/start',json={'reason':'operator start'}).status_code==200; assert client.post('/api/v1/trading/stop',json={'reason':'operator stop'}).status_code==200
def test_websocket_contract():
 with client.websocket_connect('/api/v1/ws') as ws:
  x=ws.receive_json(); assert x['schema_version']==1 and x['message_type']=='status' and x['sequence']==1
