from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from statistics import median

RISK_CLASSES=('NORMAL','ELEVATED_VOLATILITY','NEW_LISTING','THIN_LIQUIDITY','QUOTE_RISK','VENUE_RISK','RESTRICTED','NO_TRADE')

@dataclass(frozen=True)
class AssetRiskDecision:
    risk_class:str
    max_position_multiplier:Decimal
    min_edge_multiplier:Decimal
    max_slippage_multiplier:Decimal
    stricter_liquidity_filter:bool
    manual_confirmation:bool
    paper_only:bool
    no_trade:bool
    reasons:tuple[str,...]


def classify_asset_risk(*,listing_age_days:int,volatility_ratio:Decimal,liquidity_score:Decimal,quote_risky:bool=False,venue_healthy:bool=True,restricted:bool=False)->AssetRiskDecision:
    reasons=[]; cls='NORMAL'
    if restricted:
        cls='RESTRICTED'; reasons.append('RESTRICTED_ASSET')
    elif not venue_healthy:
        cls='VENUE_RISK'; reasons.append('VENUE_UNHEALTHY')
    elif quote_risky:
        cls='QUOTE_RISK'; reasons.append('QUOTE_ASSET_RISK')
    elif listing_age_days<30:
        cls='NEW_LISTING'; reasons.append('NEW_LISTING_QUARANTINE')
    elif Decimal(volatility_ratio)>=Decimal('2'):
        cls='ELEVATED_VOLATILITY'; reasons.append('ELEVATED_VOLATILITY')
    elif Decimal(liquidity_score)<Decimal('0.35'):
        cls='THIN_LIQUIDITY'; reasons.append('THIN_LIQUIDITY')
    no_trade=cls in {'RESTRICTED','VENUE_RISK'}
    paper_only=cls in {'NEW_LISTING','QUOTE_RISK'}
    manual=cls in {'NEW_LISTING','QUOTE_RISK','THIN_LIQUIDITY'}
    return AssetRiskDecision(
        cls,
        Decimal('0') if no_trade else (Decimal('0.25') if cls!='NORMAL' else Decimal('1')),
        Decimal('2') if cls!='NORMAL' else Decimal('1'),
        Decimal('0.5') if cls!='NORMAL' else Decimal('1'),
        cls!='NORMAL',manual,paper_only,no_trade,tuple(reasons)
    )

@dataclass(frozen=True)
class BreadthSnapshot:
    advancers_ratio:Decimal
    median_return:Decimal
    median_realized_volatility:Decimal
    percent_above_ma:Decimal
    btc_leadership:Decimal|None
    eth_leadership:Decimal|None
    altcoin_breadth:Decimal
    dispersion:Decimal
    cross_sectional_momentum_dispersion:Decimal
    universe_version:str


def market_breadth(rows:list[dict],*,universe_version:str)->BreadthSnapshot:
    if not universe_version: raise ValueError('point-in-time universe version required')
    if not rows: raise ValueError('eligible universe rows required')
    returns=[Decimal(str(r['return'])) for r in rows]
    vols=[Decimal(str(r['realized_volatility'])) for r in rows]
    momenta=[Decimal(str(r.get('momentum',r['return']))) for r in rows]
    above=[bool(r.get('above_ma',False)) for r in rows]
    def med(xs): return Decimal(str(median(xs)))
    mret=med(returns); disp=med([abs(x-mret) for x in returns]); mmom=med(momenta)
    mdisp=med([abs(x-mmom) for x in momenta])
    by={str(r.get('symbol','')).upper():Decimal(str(r['return'])) for r in rows}
    alts=[x for r,x in zip(rows,returns) if str(r.get('symbol','')).upper() not in {'BTCUSDT','ETHUSDT'}]
    return BreadthSnapshot(
        Decimal(sum(x>0 for x in returns))/Decimal(len(returns)),mret,med(vols),
        Decimal(sum(above))/Decimal(len(above)),by.get('BTCUSDT'),by.get('ETHUSDT'),
        Decimal(sum(x>0 for x in alts))/Decimal(len(alts)) if alts else Decimal('0'),disp,mdisp,universe_version
    )
