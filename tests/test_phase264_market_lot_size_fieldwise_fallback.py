from __future__ import annotations

from decimal import Decimal

from app.exchange.models import SymbolFilters
from app.release.acceptance_contract import ACCEPTANCE_PLANS
from scripts.external import binance_testnet_acceptance_v2 as phase264


def _base_filters() -> SymbolFilters:
    return SymbolFilters(
        tick_size=Decimal("0.01"),
        step_size=Decimal("0.001"),
        min_qty=Decimal("0.001"),
        max_qty=Decimal("1000"),
        min_notional=Decimal("0.1"),
        max_notional=None,
    )


class _Adapter:
    def __init__(self, market_filter: dict | None) -> None:
        self.market_filter = market_filter

    def get_symbol_filters(self, symbol: str) -> SymbolFilters:
        assert symbol == "TESTUSDT"
        return _base_filters()

    def get_symbol_metadata(self, symbol: str) -> dict:
        assert symbol == "TESTUSDT"
        filters = [] if self.market_filter is None else [self.market_filter]
        return {"filters": filters}


def test_mixed_market_lot_size_preserves_active_max_qty() -> None:
    adapter = _Adapter(
        {
            "filterType": "MARKET_LOT_SIZE",
            "stepSize": "0.00000000",
            "minQty": "0.00000000",
            "maxQty": "25.00000000",
        }
    )

    effective = phase264._fieldwise_market_symbol_filters(adapter, "TESTUSDT")

    assert effective.step_size == Decimal("0.001")
    assert effective.min_qty == Decimal("0.001")
    assert effective.max_qty == Decimal("25.00000000")


def test_mixed_market_lot_size_preserves_active_step_and_min() -> None:
    adapter = _Adapter(
        {
            "filterType": "MARKET_LOT_SIZE",
            "stepSize": "0.01",
            "minQty": "0.10",
            "maxQty": "0.00000000",
        }
    )

    effective = phase264._fieldwise_market_symbol_filters(adapter, "TESTUSDT")

    assert effective.step_size == Decimal("0.01")
    assert effective.min_qty == Decimal("0.10")
    assert effective.max_qty == Decimal("1000")


def test_all_disabled_market_lot_size_falls_back_to_lot_size() -> None:
    adapter = _Adapter(
        {
            "filterType": "MARKET_LOT_SIZE",
            "stepSize": "0.00000000",
            "minQty": "0.00000000",
            "maxQty": "0.00000000",
        }
    )

    assert phase264._fieldwise_market_symbol_filters(adapter, "TESTUSDT") == _base_filters()


def test_testnet_acceptance_contract_uses_phase264_wrapper() -> None:
    command = ACCEPTANCE_PLANS["testnet"][0][1]
    assert command[-3:] == (
        "app",
        "python",
        "scripts/external/binance_testnet_acceptance_v2.py",
    )
    assert "BINANCE_TESTNET_MAX_NOTIONAL" in command
    assert "BINANCE_TESTNET_PARTIAL_PRICE" in command
