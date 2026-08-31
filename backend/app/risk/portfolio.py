from __future__ import annotations
import numpy as np
from decimal import Decimal
def correlation_matrix(returns:dict[str,list[float]]):
    keys=list(returns); arr=np.array([returns[k] for k in keys]); return keys,np.corrcoef(arr)
def cluster_exposure(exposures:dict[str,Decimal],correlations:dict[tuple[str,str],float],threshold=0.7):
    seen=set(); groups=[]
    for a in exposures:
        if a in seen: continue
        group={a}; changed=True
        while changed:
            changed=False
            for b in exposures:
                if b in group: continue
                if any(abs(correlations.get((x,b),correlations.get((b,x),0)))>=threshold for x in group): group.add(b); changed=True
        seen|=group; groups.append((group,sum(abs(exposures[x]) for x in group)))
    return groups
