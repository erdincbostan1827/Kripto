from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from app.execution.reconciliation import AccountSnapshot, ReconciliationResult, reconcile


@dataclass(frozen=True)
class ReconciliationAuditEvidence:
    correlation_id: str
    drift: tuple[str, ...]
    risk_state: str
    audit_hash: str


def reconcile_with_audit(*, local: AccountSnapshot, exchange: AccountSnapshot, audit_store, correlation_id: str, actor: str='reconciliation') -> tuple[ReconciliationResult, ReconciliationAuditEvidence]:
    """Reconcile and durably bind the exact outcome to the immutable audit chain."""
    result = reconcile(local, exchange)
    reason = ';'.join(sorted(result.drift)) if result.drift else 'NO_DRIFT'
    cur = audit_store.append(actor, 'ACCOUNT_RECONCILIATION', 'exchange_account', correlation_id, reason)
    return result, ReconciliationAuditEvidence(correlation_id, tuple(sorted(result.drift)), result.risk_state.value, cur)


def account_net_positions(*position_sources: Iterable[dict[str, Decimal]]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for source in position_sources:
        for symbol, qty in source.items():
            q = Decimal(str(qty))
            totals[symbol.upper()] = totals.get(symbol.upper(), Decimal('0')) + q
    return {s:q for s,q in totals.items() if q != 0}


@dataclass(frozen=True)
class SelfTradeDecision:
    allowed: bool
    reason: str


def prevent_self_trade(*, symbol: str, incoming_side: str, open_orders: Iterable[object], incoming_price: Decimal | None=None) -> SelfTradeDecision:
    """Conservative account/symbol self-trade prevention.

    If a platform-owned opposite order can cross the incoming order, reject the
    new order and require cancel/reprice of one side first.
    """
    side = incoming_side.upper()
    if side not in {'BUY','SELL'}:
        return SelfTradeDecision(False, 'INVALID_SIDE')
    price = None if incoming_price is None else Decimal(str(incoming_price))
    for order in open_orders:
        if str(getattr(order, 'symbol', '')).upper() != symbol.upper():
            continue
        other_side = str(getattr(getattr(order, 'side', None), 'value', getattr(order, 'side', ''))).upper()
        if other_side == side or other_side not in {'BUY','SELL'}:
            continue
        other_price_raw = getattr(order, 'price', None)
        other_price = None if other_price_raw is None else Decimal(str(other_price_raw))
        # Market order or unknown price is assumed crossing. Limit orders cross
        # when BUY >= SELL.
        if price is None or other_price is None:
            return SelfTradeDecision(False, 'OPPOSITE_PLATFORM_ORDER_MAY_CROSS')
        crosses = (side == 'BUY' and price >= other_price) or (side == 'SELL' and price <= other_price)
        if crosses:
            return SelfTradeDecision(False, 'OPPOSITE_PLATFORM_ORDER_WOULD_CROSS')
    return SelfTradeDecision(True, 'NO_SELF_TRADE_RISK')
