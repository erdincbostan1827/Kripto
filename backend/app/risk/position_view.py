from __future__ import annotations

def position_health(*, entry:float, price:float, stop:float, take_profits:list[float], quantity:float, fees:float=0.0)->dict:
    if not (entry>0 and price>0 and stop>0 and quantity>=0) or stop>=entry:
        raise ValueError("invalid position inputs")
    risk=entry-stop
    unrealized=(price-entry)*quantity-fees
    current_r=(price-entry)/risk
    distance_to_sl=(price-stop)/price
    distances_to_tp=tuple((tp-price)/price for tp in take_profits)
    return {"unrealized_pnl":unrealized,"current_r":current_r,"distance_to_sl":distance_to_sl,"distance_to_tp":distances_to_tp,"at_or_below_stop":price<=stop}

def position_management_actions(*, entry:float, price:float, stop:float, atr:float, take_profits:list[float], filled_take_profits:int=0, volatility_ratio:float=1.0, trend_changed:bool=False)->dict:
    if entry<=0 or price<=0 or stop<=0 or atr<=0 or stop>=entry:
        raise ValueError('invalid position management inputs')
    if filled_take_profits<0 or filled_take_profits>len(take_profits):
        raise ValueError('invalid partial TP state')
    risk=entry-stop
    current_r=(price-entry)/risk
    # Volatility expansion tightens rather than widens protection.
    trail_multiple=max(1.0, 2.0/max(volatility_ratio,1.0))
    trailing_candidate=max(stop, price-atr*trail_multiple)
    if current_r>=1.0:
        trailing_candidate=max(trailing_candidate,entry)
    next_partial_tp=take_profits[filled_take_profits] if filled_take_profits<len(take_profits) else None
    partial_tp_due=next_partial_tp is not None and price>=next_partial_tp
    return {
        'volatility_ratio':volatility_ratio,
        'trend_changed':bool(trend_changed),
        'trailing_stop':trailing_candidate,
        'partial_tp_due':partial_tp_due,
        'next_take_profit':next_partial_tp,
        'reduce_only_recommended':bool(trend_changed),
    }
