from __future__ import annotations

import pytest

from backend.app.release.paper_campaign import PaperCampaignEvidence, PaperCampaignPolicy


def good_evidence(**overrides):
    payload = dict(
        effective_sample_size=120.0,
        calendar_days=45,
        market_regimes=("bull", "range", "bear"),
        long_examples=40,
        exit_examples=40,
        short_examples=30,
        active_market_type="PERPETUAL",
        cost_stress_passed=True,
        latency_stress_passed=True,
        independent_oos_passed=True,
        execution_divergence_bps=10.0,
        executed=True,
        real_market_data=True,
    )
    payload.update(overrides)
    return PaperCampaignEvidence(**payload)


def test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence():
    policy = PaperCampaignPolicy(min_short_examples=20, max_execution_divergence_bps=20.0)
    assert good_evidence().blockers(policy) == ()
    blockers = good_evidence(
        calendar_days=3,
        market_regimes=("bull",),
        long_examples=2,
        exit_examples=3,
        short_examples=1,
        cost_stress_passed=False,
        latency_stress_passed=False,
        independent_oos_passed=False,
        execution_divergence_bps=99.0,
    ).blockers(policy)
    assert {
        "CALENDAR_DURATION_TOO_SHORT",
        "INSUFFICIENT_MARKET_REGIMES",
        "INSUFFICIENT_LONG_EXAMPLES",
        "INSUFFICIENT_EXIT_EXAMPLES",
        "INSUFFICIENT_SHORT_EXAMPLES",
        "COST_STRESS_MISSING_OR_FAILED",
        "LATENCY_STRESS_MISSING_OR_FAILED",
        "INDEPENDENT_OOS_MISSING_OR_FAILED",
        "EXECUTION_DIVERGENCE_EXCEEDED",
    } <= set(blockers)


def test_phase26_hundred_correlated_trades_are_not_treated_as_independent_live_evidence():
    policy = PaperCampaignPolicy(min_effective_sample_size=100)
    e = good_evidence(effective_sample_size=12.5)
    assert "EFFECTIVE_SAMPLE_TOO_SMALL" in e.blockers(policy)
    with pytest.raises(PermissionError):
        e.assert_eligible(policy)


def test_phase26_local_or_unexecuted_campaign_can_never_be_promoted_as_real_market_acceptance():
    policy = PaperCampaignPolicy()
    blockers = good_evidence(executed=False, real_market_data=False).blockers(policy)
    assert "PAPER_CAMPAIGN_NOT_EXECUTED" in blockers
    assert "REAL_MARKET_PAPER_EVIDENCE_MISSING" in blockers
