from app.backtest.dataset import reproducibility_manifest,verify_reproducibility_manifest

def test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions():
    rows=[{'open_time':'2026-01-01T00:00:00Z','open':'1','high':'2','low':'1','close':'2','volume':'5'}]
    m=reproducibility_manifest(exchange='BINANCE',symbols=['BTCUSDT'],timeframe='1m',start='2026-01-01',end='2026-01-02',source='official-rest',downloaded_at='2026-01-03T00:00:00Z',rows=rows,missing_candle_count=0,preprocessing_version='prep-v2',strategy_version='s-v5',config_hash='cfg',code_git_sha='deadbeef',random_seed=42,execution_model_version='conservative-intrabar-v1')
    assert m.exchange=='BINANCE' and m.symbols==('BTCUSDT',) and m.timeframe=='1m'
    assert m.start=='2026-01-01' and m.end=='2026-01-02' and m.source=='official-rest'
    assert m.downloaded_at.endswith('Z') and m.candle_count==1 and m.missing_candle_count==0
    assert len(m.rows_sha256)==64 and len(m.dataset_hash)==64
    assert m.preprocessing_version=='prep-v2' and m.strategy_version=='s-v5' and m.config_hash=='cfg'
    assert m.code_git_sha=='deadbeef' and m.random_seed==42 and m.execution_model_version=='conservative-intrabar-v1'
    assert verify_reproducibility_manifest(m,rows)

def test_dataset_reproducibility_manifest_detects_row_or_metadata_change():
    rows=[{'t':1,'p':2}]
    kw=dict(exchange='X',symbols=['A'],timeframe='1h',start='a',end='b',source='src',downloaded_at='c',rows=rows,missing_candle_count=0,preprocessing_version='p',strategy_version='s',config_hash='c',code_git_sha='g',random_seed=1,execution_model_version='e')
    m=reproducibility_manifest(**kw)
    assert not verify_reproducibility_manifest(m,[{'t':1,'p':3}])
    m2=reproducibility_manifest(**{**kw,'timeframe':'5m'})
    assert m.dataset_hash!=m2.dataset_hash
