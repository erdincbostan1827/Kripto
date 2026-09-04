from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import httpx

from app.exchange.models import SymbolFilters
from scripts.extract_phase245_scenario import extract_scenario
from scripts.external import binance_testnet_acceptance as phase245


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase245-binance-testnet-acceptance.yml"


def _filters() -> SymbolFilters:
    return SymbolFilters(
        tick_size=Decimal("0.01"),
        step_size=Decimal("0.001"),
        min_qty=Decimal("0.001"),
        max_qty=Decimal("1000"),
        min_notional=Decimal("0.1"),
        max_notional=None,
    )


class _FilterAdapter:
    def __init__(self, market_filter: dict | None) -> None:
        self.market_filter = market_filter

    def get_symbol_filters(self, symbol: str) -> SymbolFilters:
        assert symbol == "TESTUSDT"
        return _filters()

    def get_symbol_metadata(self, symbol: str) -> dict:
        assert symbol == "TESTUSDT"
        filters = [] if self.market_filter is None else [self.market_filter]
        return {"filters": filters}


def test_market_acquisition_uses_market_lot_size_when_binance_exposes_it() -> None:
    adapter = _FilterAdapter(
        {
            "filterType": "MARKET_LOT_SIZE",
            "stepSize": "0.01",
            "minQty": "0.10",
            "maxQty": "25",
        }
    )

    market = phase245._market_symbol_filters(adapter, "TESTUSDT")
    limit = adapter.get_symbol_filters("TESTUSDT")

    assert market.step_size == Decimal("0.01")
    assert market.min_qty == Decimal("0.10")
    assert market.max_qty == Decimal("25")
    assert limit.step_size == Decimal("0.001")


def test_zero_market_lot_size_fails_safe_to_normal_lot_size() -> None:
    adapter = _FilterAdapter(
        {
            "filterType": "MARKET_LOT_SIZE",
            "stepSize": "0.00000000",
            "minQty": "0.00000000",
            "maxQty": "0.00000000",
        }
    )
    assert phase245._market_symbol_filters(adapter, "TESTUSDT") == _filters()


def test_spendable_cap_never_uses_locked_or_exceeds_operator_cap() -> None:
    assert phase245._spendable_notional_cap(Decimal("15"), Decimal("10")) == Decimal("9.00")
    assert phase245._spendable_notional_cap(Decimal("5"), Decimal("100")) == Decimal("5")


class _AutoAdapter:
    def get_exchange_info(self) -> dict:
        return {
            "symbols": [
                {
                    "symbol": "AAAUSDT",
                    "quoteAsset": "USDT",
                    "status": "TRADING",
                    "orderTypes": ["MARKET", "LIMIT"],
                },
                {
                    "symbol": "BBBBNB",
                    "quoteAsset": "BNB",
                    "status": "TRADING",
                    "orderTypes": ["MARKET", "LIMIT"],
                },
            ]
        }

    def get_symbol_filters(self, symbol: str) -> SymbolFilters:
        return _filters()


def test_auto_target_skips_quote_assets_without_free_balance(monkeypatch) -> None:
    adapter = _AutoAdapter()
    probe = {
        "price": Decimal("1"),
        "quantity": Decimal("1"),
        "executable_bid_quantity": Decimal("0.2"),
        "ratio": Decimal("0.2"),
    }
    monkeypatch.setattr(phase245, "_auto_probe_for_symbol", lambda *args, **kwargs: probe)
    monkeypatch.setattr(
        phase245,
        "_safe_quantity",
        lambda *args, **kwargs: (Decimal("1.2"), Decimal("1")),
    )

    symbol, selected_probe, effective_cap, quote_asset = phase245._select_auto_target(
        adapter,
        Decimal("15"),
        {"BNB": Decimal("2")},
    )

    assert symbol == "BBBBNB"
    assert quote_asset == "BNB"
    assert selected_probe is probe
    assert effective_cap == Decimal("1.80")


def test_http_400_evidence_keeps_exchange_reason_without_signed_request_url() -> None:
    request = httpx.Request(
        "POST",
        "https://testnet.binance.vision/api/v3/order?signature=super-secret-signature",
    )
    response = httpx.Response(
        400,
        request=request,
        json={"code": -1013, "msg": "Filter failure: MARKET_LOT_SIZE"},
    )
    exc = httpx.HTTPStatusError("bad request", request=request, response=response)

    evidence = phase245._safe_http_error(exc)
    encoded = json.dumps(evidence)

    assert evidence["exchange_http_status"] == 400
    assert evidence["exchange_code"] == -1013
    assert evidence["exchange_message"] == "Filter failure: MARKET_LOT_SIZE"
    assert "signature=" not in encoded
    assert "super-secret-signature" not in encoded


def test_scenario_extractor_handles_docker_prefix_and_single_line_failure_json() -> None:
    mixed = (
        " Container postgres Running\n"
        " Container app-run Created\n"
        '{"all_pass": false, "endpoint": "https://testnet.binance.vision", '
        '"error_type": "HTTPStatusError", "exchange_code": -1013}\n'
    )
    scenario = extract_scenario(mixed)
    assert scenario is not None
    assert scenario["all_pass"] is False
    assert scenario["checks"]["market_order"]["pass"] is False
    assert scenario["checks"]["partial_fill"]["pass"] is False


def test_scenario_extractor_handles_docker_prefix_and_pretty_success_json() -> None:
    mixed = " Container redis Running\n" + json.dumps(
        {
            "all_pass": True,
            "endpoint": "https://testnet.binance.vision",
            "symbol": "BTCUSDT",
            "symbol_selection_mode": "AUTO",
            "partial_price_mode": "AUTO",
            "checks": {
                "market_order": {"pass": True},
                "limit_order": {"pass": True},
                "cancel": {"pass": True},
                "partial_fill": {"pass": True, "probe_price": "1"},
            },
        },
        indent=2,
    )
    scenario = extract_scenario(mixed)
    assert scenario is not None
    assert scenario["all_pass"] is True
    assert all(scenario["checks"][key]["pass"] for key in phase245_result_checks())


def phase245_result_checks() -> tuple[str, ...]:
    return ("market_order", "limit_order", "cancel", "partial_fill")


def test_workflow_extracts_clean_scenario_before_convert_from_json() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "python scripts/extract_phase245_scenario.py $scenarioPath $scenarioCleanPath" in text
    assert "$scenario = Get-Content -LiteralPath $scenarioCleanPath -Raw | ConvertFrom-Json" in text
    assert "$scenario = Get-Content -LiteralPath $scenarioPath -Raw | ConvertFrom-Json" not in text
    assert "SCENARIO_EVIDENCE_UNPARSEABLE" in text
    assert "production_ready = $false" in text
    assert "live_enabled = $false" in text
