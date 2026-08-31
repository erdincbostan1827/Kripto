from __future__ import annotations
from dataclasses import dataclass
from statistics import mean

@dataclass(frozen=True)
class SignalOutcome:
    signal_id:str
    outcome:str
    return_value:float
    time_to_tp_seconds:float|None=None
    time_to_sl_seconds:float|None=None


def summarize_outcomes(rows:list[SignalOutcome])->dict:
    if not rows: return {"samples":0,"mean_return":0.0,"win_rate":0.0,"degraded":False}
    wins=sum(r.return_value>0 for r in rows); avg=mean(r.return_value for r in rows)
    return {"samples":len(rows),"mean_return":avg,"win_rate":wins/len(rows),"degraded":len(rows)>=20 and avg<0}
