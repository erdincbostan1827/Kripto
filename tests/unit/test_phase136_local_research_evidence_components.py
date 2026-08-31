from app.research.final_evidence import build_local_fixture_evidence


def _fixture_returns(n: int = 90) -> list[float]:
    # Deterministic, non-random fixture with mixed signs and a small positive edge.
    pattern = [0.0030, -0.0010, 0.0020, -0.0005, 0.0015, 0.0002]
    return [pattern[i % len(pattern)] for i in range(n)]


def test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim():
    returns = _fixture_returns()
    benchmark = [x * 0.25 for x in returns]
    evidence = build_local_fixture_evidence(returns, benchmark_returns=benchmark)

    assert evidence.classification == "LOCAL_FIXTURE_ONLY_NOT_PRODUCTION_PROFITABILITY_EVIDENCE"
    assert evidence.in_sample_return != 0.0
    assert evidence.out_of_sample_return != 0.0
    assert 0.0 <= evidence.deflated_sharpe_ratio <= 1.0
    assert 0.0 < evidence.multiple_testing_adjusted_alpha < 0.05
    assert set(evidence.tail_stress_scenarios) == {
        "single_gap_shock",
        "liquidity_freeze",
        "volatility_shock",
    }
    assert evidence.benchmark_excess_return > 0.0
    low, high = evidence.confidence_interval_95
    assert low <= high
    assert set(evidence.strategy_regime_attribution) == {"bull", "bear", "range"}
    assert set(evidence.execution_attribution) == {
        "gross_oos_return",
        "fee_drag",
        "slippage_drag",
        "latency_drag",
        "funding_drag",
    }
    for key in ("fee_drag", "slippage_drag", "latency_drag", "funding_drag"):
        assert evidence.execution_attribution[key] < 0.0


def test_phase136_local_fixture_oos_and_tail_results_are_deterministic():
    returns = _fixture_returns()
    benchmark = [0.0] * len(returns)
    first = build_local_fixture_evidence(returns, benchmark_returns=benchmark)
    second = build_local_fixture_evidence(returns, benchmark_returns=benchmark)
    assert first == second


def test_phase136_local_fixture_evidence_generator_labels_report_non_production(tmp_path, monkeypatch):
    import scripts.generate_local_fixture_research_evidence as generator

    out = tmp_path / "fixture.json"
    monkeypatch.setattr(generator, "OUT", out)
    assert generator.main() == 0
    import json
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["classification"] == "LOCAL_FIXTURE_ONLY_NOT_PRODUCTION_PROFITABILITY_EVIDENCE"
    assert payload["fixture"]["real_market_data"] is False
    assert payload["fixture"]["credentialed_exchange"] is False
    assert "MUST NOT" in payload["truth_policy"]
    assert payload["evidence"]["benchmark_excess_return"] > 0.0
