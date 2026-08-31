from datetime import datetime, timezone

import pytest

from app.release.execution_divergence import ExecutionSample, TestnetPaperDivergenceEvidence as DivergenceEvidence
from app.release.final_evidence import FinalEvidenceBundle


def _sample(*, fill=0.95, slip=3.0, latency=80.0, reject=0.01):
    return ExecutionSample(
        fills=120,
        fill_ratio=fill,
        mean_slippage_bps=slip,
        p95_ack_latency_ms=latency,
        reject_rate=reject,
    )


def test_phase27_testnet_vs_paper_execution_difference_is_explicit_and_bounded():
    evidence = DivergenceEvidence(
        paper=_sample(),
        testnet=_sample(fill=0.90, slip=5.0, latency=120.0, reject=0.03),
        observed_at=datetime.now(timezone.utc),
        executed=True,
        real_testnet=True,
        evidence_reference="evidence/testnet-paper-run.json",
    )
    d = evidence.differences()
    assert d["fill_ratio_delta"] == pytest.approx(-0.05)
    assert d["mean_slippage_bps_delta"] == pytest.approx(2.0)
    assert d["p95_ack_latency_ms_delta"] == pytest.approx(40.0)
    assert d["reject_rate_delta"] == pytest.approx(0.02)
    assert evidence.production_eligible()


def test_phase27_local_fixture_cannot_fake_real_testnet_acceptance():
    evidence = DivergenceEvidence(
        paper=_sample(),
        testnet=_sample(),
        observed_at=datetime.now(timezone.utc),
        executed=True,
        real_testnet=False,
        evidence_reference="tests/local-fixture",
    )
    payload = evidence.to_final_evidence()
    assert payload["executed"] is True
    assert payload["real_testnet"] is False
    assert not evidence.production_eligible()

    final = FinalEvidenceBundle(
        benchmark_buy_hold={"return": 0.01},
        fee_slippage_stress={"return": -0.01},
        paper_vs_backtest={"delta_bps": 2.0},
        testnet_vs_paper=payload,
        unresolved_known_issues=(),
        dataset_fingerprint="abc",
        release_id="0.3.0-local-acceptance",
    )
    # Existing final gate still rejects non-real TESTNET evidence.
    assert "TESTNET_EVIDENCE_INVALID" in final.blockers()
