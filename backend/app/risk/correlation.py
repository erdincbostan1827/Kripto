from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
import numpy as np

@dataclass(frozen=True)
class PortfolioCorrelationSnapshot:
    exposure_by_asset: dict[str,Decimal]
    exposure_by_symbol: dict[str,Decimal]
    exposure_by_quote: dict[str,Decimal]
    exposure_by_exchange: dict[str,Decimal]
    exposure_by_market_type: dict[str,Decimal]
    exposure_by_strategy: dict[str,Decimal]
    directional_exposure: dict[str,Decimal]
    rolling_correlation: dict[tuple[str,str],float]
    downside_correlation: dict[tuple[str,str],float]
    tail_correlation: dict[tuple[str,str],float]
    beta_to_btc: dict[str,float]
    beta_to_eth: dict[str,float]
    risk_contribution: dict[str,float]
    correlated_cluster_exposure: dict[str,Decimal]
    common_factor_exposure: Decimal
    stress_cluster_exposure: Decimal


def _corr(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)!=len(b) or len(a)<3: return 0.0
    x=np.corrcoef(a,b)[0,1]
    return float(x) if np.isfinite(x) else 0.0


def _beta(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)!=len(b) or len(a)<3: return 0.0
    var=float(np.var(b,ddof=1))
    if var <= 1e-15:return 0.0
    return float(np.cov(a,b,ddof=1)[0,1]/var)


def build_correlation_snapshot(*, positions:list[dict], returns:dict[str,list[float]], btc_returns:list[float], eth_returns:list[float]|None=None, cluster_threshold=.7, stress_correlation=.95):
    def sums(key):
        out={}
        for p in positions: out[p[key]]=out.get(p[key],Decimal('0'))+abs(Decimal(str(p['notional'])))
        return out
    direction={'long':Decimal('0'),'short':Decimal('0')}
    for p in positions: direction['long' if Decimal(str(p['notional']))>=0 else 'short'] += abs(Decimal(str(p['notional'])))
    syms=sorted(returns)
    rolling={}; downside={}; tail={}
    for i,a in enumerate(syms):
        for b in syms[i+1:]:
            ra=np.asarray(returns[a],float); rb=np.asarray(returns[b],float)
            rolling[(a,b)]=_corr(ra,rb)
            mask=(ra<0)&(rb<0); downside[(a,b)]=_corr(ra[mask],rb[mask]) if mask.sum()>=3 else 0.0
            qa=np.quantile(ra,.1); qb=np.quantile(rb,.1); mask=(ra<=qa)&(rb<=qb); tail[(a,b)]=_corr(ra[mask],rb[mask]) if mask.sum()>=3 else 0.0
    beta_btc={s:_beta(returns[s],btc_returns) for s in syms}
    beta_eth={s:_beta(returns[s],eth_returns) for s in syms} if eth_returns is not None else {}
    abs_exp={p['symbol']:abs(float(Decimal(str(p['notional'])))) for p in positions}
    total=sum(abs_exp.values()) or 1.0
    rc={s:v/total for s,v in abs_exp.items()}
    clusters={}; seen=set(); cidx=0
    for s in syms:
        if s in seen: continue
        group={s}; changed=True
        while changed:
            changed=False
            for t in syms:
                if t in group: continue
                if any(abs(rolling.get((min(x,t),max(x,t)),0.0))>=cluster_threshold for x in group): group.add(t); changed=True
        seen|=group; clusters[f'cluster_{cidx}']=sum((Decimal(str(abs_exp.get(x,0))) for x in group),Decimal('0')); cidx+=1
    common=sum((Decimal(str(abs_exp.get(s,0)))*Decimal(str(abs(beta_btc[s]))) for s in syms),Decimal('0'))
    gross=sum((Decimal(str(v)) for v in abs_exp.values()),Decimal('0'))
    stress=gross*Decimal(str(stress_correlation))
    return PortfolioCorrelationSnapshot(sums('asset'),sums('symbol'),sums('quote'),sums('exchange'),sums('market_type'),sums('strategy'),direction,rolling,downside,tail,beta_btc,beta_eth,rc,clusters,common,stress)


def concentration_breaches(snapshot:PortfolioCorrelationSnapshot, *, max_cluster:Decimal, max_common_factor:Decimal, max_stress_cluster:Decimal):
    reasons=[]
    if any(v>max_cluster for v in snapshot.correlated_cluster_exposure.values()): reasons.append('CORRELATED_CLUSTER_EXPOSURE')
    if snapshot.common_factor_exposure>max_common_factor: reasons.append('COMMON_FACTOR_EXPOSURE')
    if snapshot.stress_cluster_exposure>max_stress_cluster: reasons.append('STRESS_CORRELATION_EXPOSURE')
    return reasons
