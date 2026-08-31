from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib,json
@dataclass(frozen=True)
class DatasetManifest:
    dataset_id:str; provider_id:str; symbols:tuple[str,...]; start:str; end:str; universe_version:str; metadata_versions:dict; cost_model_version:str; row_count:int; content_sha256:str

def manifest(dataset_id,provider_id,symbols,start,end,universe_version,metadata_versions,cost_model_version,rows):
    canonical=json.dumps(rows,sort_keys=True,separators=(',',':'),default=str).encode(); h=hashlib.sha256(canonical).hexdigest(); return DatasetManifest(dataset_id,provider_id,tuple(symbols),start,end,universe_version,metadata_versions,cost_model_version,len(rows),h)
def verify_manifest(m:DatasetManifest,rows): return manifest(m.dataset_id,m.provider_id,m.symbols,m.start,m.end,m.universe_version,m.metadata_versions,m.cost_model_version,rows).content_sha256==m.content_sha256

@dataclass(frozen=True)
class ReproducibilityManifest:
    exchange:str
    symbols:tuple[str,...]
    timeframe:str
    start:str
    end:str
    source:str
    downloaded_at:str
    candle_count:int
    missing_candle_count:int
    rows_sha256:str
    preprocessing_version:str
    strategy_version:str
    config_hash:str
    dataset_hash:str
    code_git_sha:str
    random_seed:int
    execution_model_version:str


def reproducibility_manifest(*,exchange,symbols,timeframe,start,end,source,downloaded_at,rows,missing_candle_count,preprocessing_version,strategy_version,config_hash,code_git_sha,random_seed,execution_model_version):
    canonical=json.dumps(rows,sort_keys=True,separators=(',',':'),default=str).encode()
    rows_hash=hashlib.sha256(canonical).hexdigest()
    identity={
        'exchange':exchange,'symbols':tuple(symbols),'timeframe':timeframe,'start':start,'end':end,'source':source,
        'downloaded_at':downloaded_at,'candle_count':len(rows),'missing_candle_count':int(missing_candle_count),
        'rows_sha256':rows_hash,'preprocessing_version':preprocessing_version,'strategy_version':strategy_version,
        'config_hash':config_hash,'code_git_sha':code_git_sha,'random_seed':int(random_seed),'execution_model_version':execution_model_version,
    }
    dataset_hash=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
    return ReproducibilityManifest(dataset_hash=dataset_hash,**identity)


def verify_reproducibility_manifest(m:ReproducibilityManifest,rows)->bool:
    canonical=json.dumps(rows,sort_keys=True,separators=(',',':'),default=str).encode()
    if hashlib.sha256(canonical).hexdigest()!=m.rows_sha256: return False
    rebuilt=reproducibility_manifest(exchange=m.exchange,symbols=m.symbols,timeframe=m.timeframe,start=m.start,end=m.end,source=m.source,downloaded_at=m.downloaded_at,rows=rows,missing_candle_count=m.missing_candle_count,preprocessing_version=m.preprocessing_version,strategy_version=m.strategy_version,config_hash=m.config_hash,code_git_sha=m.code_git_sha,random_seed=m.random_seed,execution_model_version=m.execution_model_version)
    return rebuilt.dataset_hash==m.dataset_hash
