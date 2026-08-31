from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime
from decimal import Decimal
import hashlib,json

@dataclass(frozen=True)
class DecisionEvidence:
    symbol:str
    decision:str
    reasons:tuple[str,...]
    indicators:dict[str,float]
    parameters:dict[str,object]
    market_price:Decimal
    data_timestamp:datetime
    risk:dict[str,object]
    order_reason:str|None
    exchange_response:dict[str,object]|None
    portfolio_state:dict[str,object]
    universe_snapshot_id:str|None
    metadata_version:str|None
    model_version:str
    config_hash:str

    def canonical(self)->dict:
        if self.data_timestamp.tzinfo is None: raise ValueError('data_timestamp must be timezone-aware')
        d=asdict(self)
        d['market_price']=str(self.market_price)
        d['data_timestamp']=self.data_timestamp.isoformat()
        return d
    def fingerprint(self)->str:
        raw=json.dumps(self.canonical(),sort_keys=True,separators=(',',':'),default=str).encode()
        return hashlib.sha256(raw).hexdigest()


def validate_decision_evidence(e:DecisionEvidence)->DecisionEvidence:
    if not e.symbol or not e.decision or not e.reasons: raise ValueError('decision evidence missing identity/reasons')
    if not e.indicators: raise ValueError('indicator evidence required')
    if not e.parameters: raise ValueError('parameter evidence required')
    if Decimal(e.market_price)<=0: raise ValueError('market price must be positive')
    if e.data_timestamp.tzinfo is None: raise ValueError('timezone-aware data timestamp required')
    if not e.risk: raise ValueError('risk evidence required')
    if 'correlation' not in e.portfolio_state or 'concentration' not in e.portfolio_state:
        raise ValueError('portfolio correlation/concentration evidence required')
    if not e.model_version or not e.config_hash: raise ValueError('version/config evidence required')
    if e.order_reason is not None and e.exchange_response is None:
        raise ValueError('exchange response required for order decision')
    return e
