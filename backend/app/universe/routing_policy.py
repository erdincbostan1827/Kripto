from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class RouteCandidate:
    venue: str
    symbol: str
    quote: str
    market_type: str
    venue_healthy: bool
    quote_depeg_risk: Decimal
    spread_bps: Decimal
    fee_bps: Decimal
    slippage_bps: Decimal
    funding_or_basis_bps: Decimal
    account_capable: bool
    depth_score: Decimal

@dataclass(frozen=True)
class RouteDecision:
    selected: RouteCandidate
    total_cost_bps: Decimal
    reasons: tuple[str,...]


def choose_route(items:list[RouteCandidate], *, approved_quotes:tuple[str,...]=('USDT','USDC'), max_depeg_risk:Decimal=Decimal('0.02'), allowed_market_types:tuple[str,...]=('SPOT',)) -> RouteDecision:
    eligible=[]
    for x in items:
        if not x.venue_healthy or not x.account_capable: continue
        if x.quote not in approved_quotes: continue
        if x.market_type not in allowed_market_types: continue
        if x.quote_depeg_risk > max_depeg_risk: continue
        cost=x.spread_bps+x.fee_bps+x.slippage_bps+abs(x.funding_or_basis_bps)
        eligible.append((cost,-x.depth_score,x.venue,x.symbol,x))
    if not eligible: raise RuntimeError('no safe route')
    cost,_,_,_,x=min(eligible)
    return RouteDecision(x,cost,('VENUE_HEALTH_OK','QUOTE_DEPEG_RISK_OK','MARKET_TYPE_ALLOWED','ACCOUNT_CAPABILITY_OK','TOTAL_COST_MINIMIZED'))
