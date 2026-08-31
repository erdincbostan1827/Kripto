from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class Instrument:
    venue:str; symbol:str; underlying:str; quote:str; spread_bps:float; depth:float; fee_bps:float; slippage_bps:float; healthy:bool=True

def choose_instrument(items:list[Instrument],approved_quotes=('USDT','USDC')):
    ok=[x for x in items if x.healthy and x.quote in approved_quotes]
    if not ok: raise ValueError('no eligible instrument')
    return min(ok,key=lambda x:(x.spread_bps+x.fee_bps+x.slippage_bps,-x.depth,x.venue,x.symbol))
def aggregate_underlying(exposures:dict[tuple[str,str],float],mapping:dict[tuple[str,str],str]):
    out={}
    for k,v in exposures.items(): out[mapping[k]]=out.get(mapping[k],0)+v
    return out
