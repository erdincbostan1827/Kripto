from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json, math

@dataclass(frozen=True)
class ModelVersion:
    model_id:str; feature_version:str; training_cutoff:str; artifact_hash:str; approved_for_live:bool=False


def time_series_train_test(rows:list[dict], *, train_fraction:float=.7):
    if not 0.5<=train_fraction<1: raise ValueError("train_fraction out of range")
    ordered=sorted(rows,key=lambda r:r["available_at"])
    if len({r["available_at"] for r in ordered})!=len(ordered): raise ValueError("duplicate availability timestamp")
    cut=max(1,min(len(ordered)-1,int(len(ordered)*train_fraction))) if len(ordered)>=2 else len(ordered)
    return ordered[:cut],ordered[cut:]


def dataset_hash(rows:list[dict])->str:
    return sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()


def feature_importance(values:dict[str,float])->tuple[tuple[str,float],...]:
    cleaned={k:abs(float(v)) for k,v in values.items() if math.isfinite(float(v))}
    total=sum(cleaned.values())
    if total<=0:return tuple((k,0.0) for k in sorted(cleaned))
    return tuple(sorted(((k,v/total) for k,v in cleaned.items()),key=lambda x:(-x[1],x[0])))


def population_stability_index(expected:list[float],actual:list[float],*,bins:int=10)->float:
    if not expected or not actual or bins<2:return 0.0
    lo=min(expected+actual); hi=max(expected+actual)
    if hi<=lo:return 0.0
    step=(hi-lo)/bins
    def counts(xs):
        out=[0]*bins
        for x in xs: out[min(bins-1,max(0,int((x-lo)/step)))]+=1
        return [(c+1e-6)/(len(xs)+bins*1e-6) for c in out]
    e,a=counts(expected),counts(actual)
    return sum((av-ev)*math.log(av/ev) for ev,av in zip(e,a))
