from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradeLevelConfig:
    atr_multiple: Decimal = Decimal("2")
    percent_stop: Decimal = Decimal("0.02")
    swing_buffer_atr: Decimal = Decimal("0.25")
    max_stop_fraction: Decimal = Decimal("0.06")
    take_profit_rr: tuple[Decimal, ...] = (Decimal("1"), Decimal("2"), Decimal("3"))
    break_even_at_rr: Decimal = Decimal("1")
    trail_atr_multiple: Decimal = Decimal("2")


@dataclass(frozen=True)
class TradeLevels:
    entry: Decimal
    stop: Decimal
    take_profits: tuple[Decimal, ...]
    risk_per_unit: Decimal
    stop_method: str


def build_long_levels(*, price: Decimal, atr: Decimal, swing_low: Decimal | None = None, config: TradeLevelConfig | None = None) -> TradeLevels:
    c = config or TradeLevelConfig()
    price, atr = Decimal(price), Decimal(atr)
    if price <= 0 or atr <= 0:
        raise ValueError("price and atr must be positive")
    candidates = {
        "ATR": price - atr * c.atr_multiple,
        "PERCENT": price * (Decimal("1") - c.percent_stop),
    }
    if swing_low is not None and Decimal(swing_low) < price:
        candidates["SWING"] = Decimal(swing_low) - atr * c.swing_buffer_atr
    floor = price * (Decimal("1") - c.max_stop_fraction)
    # Prefer the structurally closest valid stop while bounding maximum loss distance.
    valid = {name: max(level, floor) for name, level in candidates.items() if level > 0 and level < price}
    if not valid:
        raise ValueError("no valid stop candidate")
    method, stop = max(valid.items(), key=lambda item: item[1])
    risk = price - stop
    tps = tuple(price + risk * rr for rr in c.take_profit_rr)
    return TradeLevels(price, stop, tps, risk, method)


def update_protective_stop(*, current_stop: Decimal, entry: Decimal, price: Decimal, atr: Decimal, config: TradeLevelConfig | None = None) -> Decimal:
    c = config or TradeLevelConfig()
    current_stop, entry, price, atr = map(Decimal, (current_stop, entry, price, atr))
    if not (0 < current_stop < price) or entry <= 0 or atr <= 0:
        raise ValueError("invalid stop update inputs")
    initial_risk = max(entry-current_stop, Decimal("0"))
    break_even = entry if initial_risk > 0 and price >= entry + initial_risk*c.break_even_at_rr else current_stop
    trailing = price - atr*c.trail_atr_multiple
    # Protective stops can tighten, never widen.
    return max(current_stop, break_even, trailing)
