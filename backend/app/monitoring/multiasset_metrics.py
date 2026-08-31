from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from decimal import Decimal

ALLOWED_METRICS={
 'websocket_shards','rate_limit_budget_remaining','symbol_data_latency','symbol_order_reject_rate','symbol_slippage',
 'portfolio_concentration','correlated_cluster_exposure','quote_asset_exposure','capital_reserved','capital_available'
}

@dataclass(frozen=True)
class MetricPoint:
    name:str; value:Decimal; labels:tuple[tuple[str,str],...]

class BoundedMetricRegistry:
    """Bound high-cardinality metric storage while preserving operational portfolio metrics."""
    def __init__(self,max_points:int=512,max_symbol_labels:int=100):
        if max_points<=0 or max_symbol_labels<=0: raise ValueError('positive bounds required')
        self.points=deque(maxlen=max_points); self.max_symbol_labels=max_symbol_labels; self.symbols=set()
    def observe(self,name:str,value,**labels):
        if name not in ALLOWED_METRICS: raise ValueError('unapproved metric')
        symbol=labels.get('symbol')
        if symbol and symbol not in self.symbols:
            if len(self.symbols)>=self.max_symbol_labels: raise OverflowError('symbol metric cardinality bound exceeded')
            self.symbols.add(symbol)
        safe=tuple(sorted((str(k),str(v)) for k,v in labels.items() if k in {'symbol','exchange','market_type','strategy'}))
        self.points.append(MetricPoint(name,Decimal(str(value)),safe)); return self.points[-1]
