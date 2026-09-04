from decimal import Decimal

import pytest

from scripts.external.binance_testnet_acceptance import (
    ACQUISITION_CAP_UTILIZATION,
    PARTIAL_CAP_UTILIZATION,
    _bounded_quantity_for_price,
    _effective_notional_cap,
    _executable_bid_quantity,
)
from app.exchange.models import SymbolFilters


def _filters(*, max_notional: str | None = None, min_notional: str = "5") -> SymbolFilters:
    return SymbolFilters(
        tick_size=Decimal("0.01"),
        step_size=Decimal("0.001"),
        min_qty=Decimal("0.001"),
        max_qty=Decimal("1000"),
        min_notional=Decimal(min_notional),
        max_notional=Decimal(max_notional) if max_notional is not None else None,
    )


def test_probe_quantity_stays_below_operator_cap_after_step_rounding() -> None:
    filters = _filters()
    price = Decimal("100")
    cap = Decimal("15")

    quantity = _bounded_quantity_for_price(
        filters,
        price,
        cap,
        utilization=PARTIAL_CAP_UTILIZATION,
    )

    assert quantity == Decimal("0.127")
    assert quantity * price <= cap * PARTIAL_CAP_UTILIZATION
    assert quantity * price <= cap
    assert quantity >= filters.min_qty
    assert quantity * price >= filters.min_notional


def test_effective_cap_honors_stricter_exchange_max_notional() -> None:
    filters = _filters(max_notional="10")
    assert _effective_notional_cap(filters, Decimal("15")) == Decimal("10")

    quantity = _bounded_quantity_for_price(
        filters,
        Decimal("100"),
        Decimal("15"),
        utilization=ACQUISITION_CAP_UTILIZATION,
    )
    assert quantity == Decimal("0.090")
    assert quantity * Decimal("100") <= Decimal("10")


def test_bounded_quantity_fails_closed_when_minimum_exceeds_budget() -> None:
    filters = _filters(min_notional="13")

    with pytest.raises(RuntimeError, match="minimum executable notional"):
        _bounded_quantity_for_price(
            filters,
            Decimal("100"),
            Decimal("15"),
            utilization=PARTIAL_CAP_UTILIZATION,
        )


class _BookAdapter:
    def get_order_book(self, symbol: str) -> dict:
        assert symbol == "TESTUSDT"
        return {
            "bids": [
                ["100.00", "0.030"],
                ["99.00", "0.020"],
                ["98.00", "9.000"],
            ]
        }


def test_executable_bid_quantity_counts_only_marketable_levels() -> None:
    adapter = _BookAdapter()

    assert _executable_bid_quantity(adapter, "TESTUSDT", Decimal("100")) == Decimal("0.030")
    assert _executable_bid_quantity(adapter, "TESTUSDT", Decimal("99")) == Decimal("0.050")


def test_phase254_source_preflights_partial_depth_before_any_order_submission() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "external"
        / "binance_testnet_acceptance.py"
    ).read_text(encoding="utf-8")

    preflight = source.index("executable_bid_quantity = _executable_bid_quantity")
    first_submit = source.index("market = adapter.submit_order")
    assert preflight < first_submit
    assert "executable_bid_quantity <= 0 or executable_bid_quantity >= probe_quantity" in source
    assert 'TESTNET_URL = "https://testnet.binance.vision"' in source
    assert 'result["all_pass"] = bool(market_ok and limit_ok and cancel_ok and partial_ok)' in source
