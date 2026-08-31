from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone

D = Decimal

@dataclass(frozen=True)
class PreTradeLimits:
    max_order_notional: D
    max_quantity: D
    max_position_notional: D
    max_price_deviation_bps: D = D('100')
    max_spread_bps: D = D('50')
    max_expected_slippage_bps: D = D('50')
    max_reference_age_ms: int = 3000

@dataclass(frozen=True)
class PreTradeContext:
    reference_price: D
    reference_time: datetime
    bid: D
    ask: D
    expected_slippage_bps: D
    current_position_qty: D
    available_balance: D
    symbol_trading: bool
    trading_state_allows_new_risk: bool
    min_price: D | None = None
    max_price: D | None = None

@dataclass(frozen=True)
class PreTradeDecision:
    allowed: bool
    reasons: tuple[str, ...]
    order_notional: D
    resulting_position_notional: D
    spread_bps: D
    reference_age_ms: int


def _bps(a: D, b: D) -> D:
    if b <= 0:
        raise ValueError('reference price must be positive')
    return abs(a-b) / b * D('10000')


def evaluate_pretrade(intent, limits: PreTradeLimits, ctx: PreTradeContext, *, now: datetime | None = None) -> PreTradeDecision:
    now = now or datetime.now(timezone.utc)
    if ctx.reference_time.tzinfo is None:
        raise ValueError('reference_time must be timezone-aware')
    age_ms=max(0,int((now-ctx.reference_time).total_seconds()*1000))
    qty=D(intent.quantity)
    side=intent.side.upper()
    px=D(intent.price) if intent.price is not None else D(ctx.reference_price)
    order_notional=abs(qty*px)
    side_sign=D('1') if side=='BUY' else D('-1')
    resulting_qty=D(ctx.current_position_qty)+side_sign*qty
    resulting_notional=abs(resulting_qty*D(ctx.reference_price))
    spread_bps=((D(ctx.ask)-D(ctx.bid))/D(ctx.reference_price)*D('10000')) if D(ctx.reference_price)>0 else D('Infinity')
    reasons=[]
    if side not in {'BUY','SELL'}: reasons.append('SIDE_SANITY')
    if not ctx.trading_state_allows_new_risk and not intent.reduce_only: reasons.append('TRADING_STATE_BLOCKS_NEW_RISK')
    if not ctx.symbol_trading: reasons.append('SYMBOL_NOT_TRADING')
    if age_ms>limits.max_reference_age_ms: reasons.append('STALE_REFERENCE_PRICE')
    if qty<=0 or qty>limits.max_quantity: reasons.append('MAX_QUANTITY')
    if order_notional>limits.max_order_notional: reasons.append('MAX_ORDER_NOTIONAL')
    if resulting_notional>limits.max_position_notional and not intent.reduce_only: reasons.append('MAX_POSITION_NOTIONAL')
    if _bps(px,D(ctx.reference_price))>limits.max_price_deviation_bps: reasons.append('PRICE_COLLAR')
    if spread_bps>limits.max_spread_bps: reasons.append('SPREAD_LIMIT')
    if D(ctx.expected_slippage_bps)>limits.max_expected_slippage_bps: reasons.append('SLIPPAGE_LIMIT')
    if ctx.min_price is not None and px<D(ctx.min_price): reasons.append('EXCHANGE_MIN_PRICE')
    if ctx.max_price is not None and px>D(ctx.max_price): reasons.append('EXCHANGE_MAX_PRICE')
    # Spot BUY affordability is checked against quote balance. SELL base-asset
    # affordability remains enforced separately by validate_spot_sell_balance.
    market_type=str(intent.market_type.value if hasattr(intent.market_type,'value') else intent.market_type).upper()
    if market_type=='SPOT' and intent.side.upper()=='BUY' and order_notional>D(ctx.available_balance): reasons.append('INSUFFICIENT_AVAILABLE_BALANCE')
    if intent.reduce_only:
        pos=D(ctx.current_position_qty)
        if pos==0: reasons.append('REDUCE_ONLY_FLAT')
        elif pos>0 and intent.side.upper()!='SELL': reasons.append('REDUCE_ONLY_SIDE')
        elif pos<0 and intent.side.upper()!='BUY': reasons.append('REDUCE_ONLY_SIDE')
        elif qty>abs(pos): reasons.append('REDUCE_ONLY_CROSS_ZERO')
    return PreTradeDecision(not reasons,tuple(reasons),order_notional,resulting_notional,spread_bps,age_ms)


def require_pretrade(intent, limits: PreTradeLimits, ctx: PreTradeContext, *, now: datetime | None = None) -> PreTradeDecision:
    decision=evaluate_pretrade(intent,limits,ctx,now=now)
    if not decision.allowed:
        raise PermissionError('pre-trade rejected: '+','.join(decision.reasons))
    return decision
