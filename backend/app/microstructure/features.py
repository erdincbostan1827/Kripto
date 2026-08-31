from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


D = Decimal


@dataclass(frozen=True)
class BookLevel:
    price: Decimal
    quantity: Decimal


@dataclass(frozen=True)
class TradePrint:
    price: Decimal
    quantity: Decimal
    aggressor_side: str


@dataclass(frozen=True)
class MicrostructureFeatures:
    spread_bps: Decimal
    order_book_imbalance: Decimal
    depth_imbalance: Decimal
    microprice: Decimal
    buy_volume: Decimal
    sell_volume: Decimal
    volume_delta: Decimal
    cumulative_volume_delta: Decimal
    order_flow_momentum: Decimal
    abnormal_sweep: bool
    liquidity_vacuum: bool


def _sum_qty(levels: Iterable[BookLevel]) -> Decimal:
    return sum((D(str(x.quantity)) for x in levels), D("0"))


def extract_microstructure_features(
    *,
    bids: list[BookLevel],
    asks: list[BookLevel],
    trades: list[TradePrint],
    previous_cvd: Decimal = D("0"),
    sweep_notional_threshold: Decimal = D("100000"),
    vacuum_depth_threshold: Decimal = D("1000"),
) -> MicrostructureFeatures:
    if not bids or not asks:
        raise ValueError("both bid and ask books are required")
    best_bid = max(bids, key=lambda x: x.price)
    best_ask = min(asks, key=lambda x: x.price)
    if best_bid.price <= 0 or best_ask.price <= 0 or best_ask.price < best_bid.price:
        raise ValueError("invalid top of book")
    mid = (D(str(best_bid.price)) + D(str(best_ask.price))) / D("2")
    spread_bps = ((D(str(best_ask.price)) - D(str(best_bid.price))) / mid * D("10000")) if mid else D("0")
    bid_depth = _sum_qty(bids)
    ask_depth = _sum_qty(asks)
    total_depth = bid_depth + ask_depth
    imbalance = (bid_depth - ask_depth) / total_depth if total_depth else D("0")
    top_total = D(str(best_bid.quantity)) + D(str(best_ask.quantity))
    microprice = (
        (D(str(best_ask.price)) * D(str(best_bid.quantity)) + D(str(best_bid.price)) * D(str(best_ask.quantity))) / top_total
        if top_total else mid
    )
    buy_volume = sum((D(str(t.quantity)) for t in trades if t.aggressor_side.upper() == "BUY"), D("0"))
    sell_volume = sum((D(str(t.quantity)) for t in trades if t.aggressor_side.upper() == "SELL"), D("0"))
    for trade in trades:
        if trade.aggressor_side.upper() not in {"BUY", "SELL"}:
            raise ValueError("trade aggressor side must be BUY or SELL")
    delta = buy_volume - sell_volume
    cvd = D(str(previous_cvd)) + delta
    total_trade_volume = buy_volume + sell_volume
    momentum = delta / total_trade_volume if total_trade_volume else D("0")
    buy_notional = sum((D(str(t.price)) * D(str(t.quantity)) for t in trades if t.aggressor_side.upper() == "BUY"), D("0"))
    sell_notional = sum((D(str(t.price)) * D(str(t.quantity)) for t in trades if t.aggressor_side.upper() == "SELL"), D("0"))
    abnormal_sweep = max(buy_notional, sell_notional) >= D(str(sweep_notional_threshold)) and abs(momentum) >= D("0.8")
    liquidity_vacuum = total_depth < D(str(vacuum_depth_threshold))
    return MicrostructureFeatures(
        spread_bps=spread_bps,
        order_book_imbalance=imbalance,
        depth_imbalance=imbalance,
        microprice=microprice,
        buy_volume=buy_volume,
        sell_volume=sell_volume,
        volume_delta=delta,
        cumulative_volume_delta=cvd,
        order_flow_momentum=momentum,
        abnormal_sweep=abnormal_sweep,
        liquidity_vacuum=liquidity_vacuum,
    )
