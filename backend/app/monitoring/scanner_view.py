from __future__ import annotations
from dataclasses import dataclass
from typing import Any

DEFAULT_COLUMNS=('symbol','price','signal','score','confidence','net_edge','rank','block_reason','data_age_seconds')
ADVANCED_COLUMNS=('quote_volume_24h','spread_bps','volatility','regime','liquidity_score')

@dataclass(frozen=True)
class ScannerViewPreferences:
    visible_columns: tuple[str,...]=DEFAULT_COLUMNS
    search: str=''
    sort_by: str='rank'
    descending: bool=False
    page: int=1
    page_size: int=25
    mobile: bool=False
    saved_view_name: str|None=None
    def __post_init__(self):
        allowed=set(DEFAULT_COLUMNS+ADVANCED_COLUMNS)
        if not self.visible_columns or not set(self.visible_columns)<=allowed: raise ValueError('invalid visible columns')
        if self.sort_by not in allowed: raise ValueError('invalid sort column')
        if self.page<1 or self.page_size<1 or self.page_size>200: raise ValueError('invalid pagination')

@dataclass(frozen=True)
class ScannerViewResult:
    rows: tuple[dict[str,Any],...]
    total: int
    page: int
    page_size: int
    mobile_cards: bool
    stable_sort_key: str

def apply_scanner_view(items:list[dict[str,Any]], prefs:ScannerViewPreferences)->ScannerViewResult:
    q=prefs.search.strip().upper()
    filtered=[dict(x) for x in items if not q or q in str(x.get('symbol','')).upper()]
    def val(row):
        v=row.get(prefs.sort_by)
        missing=v is None
        # deterministic tie breaker keeps stable order independent of input ordering
        return (missing, v if v is not None else 0, str(row.get('symbol','')))
    ordered=sorted(filtered,key=val,reverse=prefs.descending)
    start=(prefs.page-1)*prefs.page_size
    page=ordered[start:start+prefs.page_size]
    projected=tuple({k:r.get(k) for k in prefs.visible_columns} for r in page)
    return ScannerViewResult(projected,len(filtered),prefs.page,prefs.page_size,prefs.mobile,prefs.sort_by)
