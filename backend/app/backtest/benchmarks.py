from __future__ import annotations

def buy_and_hold(prices):
    if len(prices)<2:return 0.0
    return float(prices[-1]/prices[0]-1)
def equal_weight_asset_returns(asset_price_series:dict[str,list[float]]):
    rs=[buy_and_hold(v) for v in asset_price_series.values() if len(v)>=2]; return sum(rs)/len(rs) if rs else 0.0
def cash_baseline(): return 0.0
def simple_dca(prices,interval=10):
    entries=[prices[i] for i in range(0,len(prices),interval)]
    if not entries:return 0.0
    units=sum(1/x for x in entries); spent=len(entries); return prices[-1]*units/spent-1
def simple_trend(prices,lookback=20):
    cash=1.0; units=0.0
    for i,p in enumerate(prices):
        if i<lookback:continue
        ma=sum(prices[i-lookback:i])/lookback
        if p>ma and units==0: units=cash/p; cash=0
        elif p<ma and units>0: cash=units*p; units=0
    return (cash+units*prices[-1])-1
