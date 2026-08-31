from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


D = Decimal


@dataclass
class PaperFill:
    side: str
    qty: Decimal
    price: Decimal
    fee: Decimal
    latency_ms: int
    status: str
    reason: str


@dataclass
class PaperPosition:
    symbol: str
    qty: Decimal
    entry_price: Decimal
    stop_loss: Decimal
    take_profits: tuple[Decimal, Decimal, Decimal]
    remaining_qty: Decimal
    realized_pnl: Decimal = D("0")
    closed: bool = False
    triggered_tps: set[int] = field(default_factory=set)


class PaperBroker:
    """Market-data driven simulator. It never calls an exchange order endpoint."""

    def __init__(self, fee_bps: Decimal = D("10"), slippage_bps: Decimal = D("5")):
        self.fee_bps = D(fee_bps)
        self.slippage_bps = D(slippage_bps)
        self.fills: list[PaperFill] = []
        self.positions: dict[str, PaperPosition] = {}

    def _fill(self, side: str, qty: Decimal, reference_price: Decimal, latency_ms: int, reason: str, requested_qty: Decimal | None = None) -> PaperFill:
        qty = D(qty)
        reference_price = D(reference_price)
        if qty <= 0 or reference_price <= 0:
            raise ValueError("paper fill requires positive quantity and price")
        slip = reference_price * self.slippage_bps / D(10000)
        fill_price = reference_price + slip if side == "BUY" else reference_price - slip
        fee = fill_price * qty * self.fee_bps / D(10000)
        status = "PARTIALLY_FILLED" if requested_qty is not None and qty < requested_qty else "FILLED"
        fill = PaperFill(side, qty, fill_price, fee, int(latency_ms), status, reason)
        self.fills.append(fill)
        return fill

    def fill_market(self, side, qty, bid, ask, latency_ms: int = 50, available_qty: Decimal | None = None):
        requested = D(qty)
        actual = requested if available_qty is None else min(requested, D(available_qty))
        if actual <= 0:
            raise ValueError("no executable paper liquidity")
        reference = D(ask if side == "BUY" else bid)
        return self._fill(side, actual, reference, latency_ms, "MARKET", requested)

    def open_long(self, symbol: str, qty: Decimal, bid: Decimal, ask: Decimal, stop_loss: Decimal, take_profits: tuple[Decimal, Decimal, Decimal], latency_ms: int = 50, available_qty: Decimal | None = None) -> PaperPosition:
        if symbol in self.positions and not self.positions[symbol].closed:
            raise ValueError("paper position already open")
        stop_loss = D(stop_loss)
        tps = tuple(D(x) for x in take_profits)
        if not (stop_loss < D(ask) < tps[0] < tps[1] < tps[2]):
            raise ValueError("invalid long protective levels")
        fill = self.fill_market("BUY", qty, bid, ask, latency_ms, available_qty)
        position = PaperPosition(symbol, fill.qty, fill.price, stop_loss, tps, fill.qty)
        self.positions[symbol] = position
        return position

    def on_quote(self, symbol: str, bid: Decimal, ask: Decimal, latency_ms: int = 50) -> list[PaperFill]:
        position = self.positions.get(symbol)
        if position is None or position.closed:
            return []
        bid = D(bid)
        generated: list[PaperFill] = []
        if bid <= position.stop_loss:
            generated.append(self._close_qty(position, position.remaining_qty, bid, latency_ms, "STOP_LOSS"))
            position.closed = True
            return generated

        fractions = (D("0.30"), D("0.30"), D("0.40"))
        for index, level in enumerate(position.take_profits):
            if index in position.triggered_tps or bid < level or position.remaining_qty <= 0:
                continue
            position.triggered_tps.add(index)
            qty = position.qty * fractions[index]
            if index == 2:
                qty = position.remaining_qty
            qty = min(qty, position.remaining_qty)
            generated.append(self._close_qty(position, qty, bid, latency_ms, f"TP{index + 1}"))
        if position.remaining_qty <= 0:
            position.closed = True
        return generated

    def _close_qty(self, position: PaperPosition, qty: Decimal, bid: Decimal, latency_ms: int, reason: str) -> PaperFill:
        fill = self._fill("SELL", qty, bid, latency_ms, reason)
        gross = (fill.price - position.entry_price) * fill.qty
        position.realized_pnl += gross - fill.fee
        position.remaining_qty -= fill.qty
        if position.remaining_qty < 0:
            raise RuntimeError("paper remaining quantity became negative")
        return fill
