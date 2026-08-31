from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from uuid import uuid4


class PositionSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class NettingPolicy(StrEnum):
    FIFO_PER_STRATEGY = "FIFO_PER_STRATEGY"
    REJECT_CROSS_STRATEGY_EXIT = "REJECT_CROSS_STRATEGY_EXIT"


@dataclass
class StrategyAllocationLot:
    lot_id: str
    strategy_id: str
    symbol: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    source_order_id: str
    source_fill_id: str
    fees: Decimal = Decimal("0")
    funding: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")

    @property
    def signed_quantity(self) -> Decimal:
        return self.quantity if self.side is PositionSide.LONG else -self.quantity


@dataclass(frozen=True)
class SleeveReconciliation:
    symbol: str
    account_net_quantity: Decimal
    sleeve_net_quantity: Decimal
    consistent: bool


@dataclass
class StrategySleeveBook:
    netting_policy: NettingPolicy = NettingPolicy.FIFO_PER_STRATEGY
    hedging_supported: bool = False
    ownership_transfer_allowed: bool = False
    lots: list[StrategyAllocationLot] = field(default_factory=list)

    def allocate_fill(
        self,
        *,
        strategy_id: str,
        symbol: str,
        side: PositionSide | str,
        quantity: Decimal,
        entry_price: Decimal,
        source_order_id: str,
        source_fill_id: str,
        fee: Decimal = Decimal("0"),
        funding: Decimal = Decimal("0"),
    ) -> StrategyAllocationLot:
        qty = Decimal(quantity)
        price = Decimal(entry_price)
        if not strategy_id or not symbol or not source_order_id or not source_fill_id:
            raise ValueError("entry/fill attribution identifiers are required")
        if qty <= 0 or price <= 0:
            raise ValueError("quantity and entry price must be positive")
        position_side = PositionSide(str(side).upper())
        opposite = PositionSide.SHORT if position_side is PositionSide.LONG else PositionSide.LONG
        if not self.hedging_supported and any(
            lot.symbol == symbol.upper() and lot.quantity > 0 and lot.side is opposite
            for lot in self.lots
        ):
            raise ValueError("hedging conflict for account/symbol")
        lot = StrategyAllocationLot(
            lot_id=uuid4().hex,
            strategy_id=strategy_id,
            symbol=symbol.upper(),
            side=position_side,
            quantity=qty,
            entry_price=price,
            source_order_id=source_order_id,
            source_fill_id=source_fill_id,
            fees=Decimal(fee),
            funding=Decimal(funding),
        )
        self.lots.append(lot)
        return lot

    def _open_lots(self, strategy_id: str, symbol: str, side: PositionSide) -> list[StrategyAllocationLot]:
        return [
            lot
            for lot in self.lots
            if lot.strategy_id == strategy_id
            and lot.symbol == symbol.upper()
            and lot.side is side
            and lot.quantity > 0
        ]

    def close(
        self,
        *,
        strategy_id: str,
        symbol: str,
        side: PositionSide | str,
        quantity: Decimal,
        exit_price: Decimal,
        exit_fee: Decimal = Decimal("0"),
        funding: Decimal = Decimal("0"),
    ) -> Decimal:
        qty_left = Decimal(quantity)
        price = Decimal(exit_price)
        position_side = PositionSide(str(side).upper())
        if qty_left <= 0 or price <= 0:
            raise ValueError("close quantity and price must be positive")
        candidates = self._open_lots(strategy_id, symbol, position_side)
        available = sum((lot.quantity for lot in candidates), Decimal("0"))
        if qty_left > available:
            raise ValueError("strategy cannot exit another strategy's exposure")
        realized = Decimal("0")
        total_qty = qty_left
        for lot in candidates:
            if qty_left <= 0:
                break
            closed = min(lot.quantity, qty_left)
            gross = (price - lot.entry_price) * closed
            if position_side is PositionSide.SHORT:
                gross = -gross
            allocated_exit_fee = Decimal(exit_fee) * (closed / total_qty)
            allocated_funding = Decimal(funding) * (closed / total_qty)
            pnl = gross - allocated_exit_fee - allocated_funding
            lot.quantity -= closed
            lot.realized_pnl += pnl
            lot.fees += allocated_exit_fee
            lot.funding += allocated_funding
            realized += pnl
            qty_left -= closed
        return realized

    def transfer_ownership(self, *, lot_id: str, from_strategy: str, to_strategy: str) -> None:
        if not self.ownership_transfer_allowed:
            raise PermissionError("ownership transfer policy forbids transfer")
        lot = next((item for item in self.lots if item.lot_id == lot_id), None)
        if lot is None or lot.strategy_id != from_strategy:
            raise ValueError("lot ownership mismatch")
        if not to_strategy or to_strategy == from_strategy:
            raise ValueError("invalid target strategy")
        lot.strategy_id = to_strategy

    def strategy_virtual_sleeve(self, strategy_id: str, symbol: str) -> Decimal:
        return sum(
            (lot.signed_quantity for lot in self.lots if lot.strategy_id == strategy_id and lot.symbol == symbol.upper()),
            Decimal("0"),
        )

    def account_net_position(self, symbol: str) -> Decimal:
        return sum((lot.signed_quantity for lot in self.lots if lot.symbol == symbol.upper()), Decimal("0"))

    def reconcile_account_net(self, *, symbol: str, exchange_account_net_quantity: Decimal) -> SleeveReconciliation:
        sleeve = self.account_net_position(symbol)
        account = Decimal(exchange_account_net_quantity)
        return SleeveReconciliation(symbol.upper(), account, sleeve, account == sleeve)
