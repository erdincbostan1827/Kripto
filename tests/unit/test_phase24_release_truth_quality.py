from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import random

import pytest

from backend.app.core.retry import RetryPolicy
from backend.app.exchange.capability_policy import SymbolCapabilityProfile
from backend.app.execution.quality import ExecutionQuality, execution_quality_score
from backend.app.release.blocker_dossier import ExternalEvidence, build_requirement_blockers, render_blocker_dossier


def test_phase24_rate_limit_retry_uses_bounded_exponential_backoff_retry_and_jitter():
    p = RetryPolicy(max_attempts=4, base_seconds=1.0, max_seconds=8.0, jitter_fraction=0.25)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    delays = []
    for attempt in (1, 2, 3):
        d = p.decide(TimeoutError('rate limit'), attempt=attempt, now=now, rng=random.Random(7))
        assert d.retryable and d.reason == 'RETRYABLE'
        delay = (d.next_attempt_at - now).total_seconds()
        base = 2 ** (attempt - 1)
        assert base <= delay <= base * 1.25
        delays.append(delay)
    assert delays[0] < delays[1] < delays[2]
    exhausted = p.decide(TimeoutError('rate limit'), attempt=4, now=now)
    assert not exhausted.retryable and exhausted.reason == 'RETRY_BUDGET_EXHAUSTED'


def _profile() -> SymbolCapabilityProfile:
    return SymbolCapabilityProfile(
        symbol='BTCUSDT', order_types=('MARKET','LIMIT'), oco_or_order_list=True,
        order_book_depth_supported=True, cancel_replace_supported=True,
        precision_mode='TICK_STEP_FILTERS', min_price=Decimal('0.01'), max_price=Decimal('1000000'),
        min_qty=Decimal('0.00001'), max_qty=Decimal('100'), min_notional=Decimal('5'),
        max_notional=Decimal('1000000'), max_open_orders=200,
        exchange_rate_limits=({'rateLimitType':'REQUEST_WEIGHT','limit':6000},),
    )


def test_phase24_capability_filters_are_all_consistency_checked_fail_closed():
    p = _profile(); p.assert_pretrade_supported()
    for broken in (
        replace(p, symbol=''), replace(p, max_price=Decimal('0.001')),
        replace(p, max_qty=Decimal('0.000001')), replace(p, min_notional=Decimal('-1')),
        replace(p, max_notional=Decimal('1')), replace(p, max_open_orders=0),
        replace(p, exchange_rate_limits=({'limit':0},)),
    ):
        with pytest.raises(RuntimeError):
            broken.assert_pretrade_supported()


def _quality(**overrides) -> ExecutionQuality:
    base = dict(quoted_spread_bps=2.0, effective_spread_bps=2.0, realized_slippage_bps=1.0,
        expected_slippage_bps=1.0, fill_ratio=1.0, partial_fill_ratio=0.0, cancel_ratio=0.0,
        reject_ratio=0.0, avg_ack_ms=80.0, avg_fill_ms=300.0, market_impact_bps=1.0,
        adverse_selection_bps=1.0, maker_ratio=0.5)
    base.update(overrides); return ExecutionQuality(**base)


def test_phase24_execution_quality_score_is_bounded_and_penalizes_cost_liquidity_rejects():
    good = execution_quality_score(_quality(), available_liquidity_ratio=1.0)
    poor = execution_quality_score(_quality(quoted_spread_bps=40, realized_slippage_bps=30,
        fill_ratio=.4, reject_ratio=.4, avg_ack_ms=2000, market_impact_bps=30), available_liquidity_ratio=.2)
    assert 0 <= poor < good <= 100
    with pytest.raises(ValueError): execution_quality_score(_quality(), available_liquidity_ratio=1.1)


def test_phase24_external_acceptance_rejects_mock_missing_checksum_or_nonzero_exit(tmp_path: Path):
    artifact = tmp_path / 'testnet.log'; artifact.write_text('credentialed testnet evidence\n')
    digest = sha256(artifact.read_bytes()).hexdigest()
    base = ExternalEvidence('credentialed_binance_testnet','PASS','TESTNET','testnet.log',digest,True,0,datetime.now(timezone.utc))
    assert base.validate(tmp_path) == (True, 'PASS')
    assert not replace(base, real_system=False).validate(tmp_path)[0]
    assert not replace(base, exit_code=1).validate(tmp_path)[0]
    assert not replace(base, evidence_sha256='0'*64).validate(tmp_path)[0]
    assert not replace(base, evidence_path='missing.log').validate(tmp_path)[0]


def test_phase24_blocker_dossier_classifies_remaining_p0_without_promoting_external_evidence(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    blockers = build_requirement_blockers(root / 'requirements_acceptance_matrix.yaml')
    assert blockers
    ids = {b.requirement_id: b for b in blockers}
    assert 'REQ-V51-096-002' not in ids
    assert ids['REQ-V51-096-005'].external_required and ids['REQ-V51-096-005'].category == 'SUPPLY_CHAIN_PROVENANCE'
    assert ids['REQ-V51-178-014'].external_required and ids['REQ-V51-178-014'].category == 'RECOVERY_HA_RUNTIME'
    assert ids['REQ-V51-043-002'].external_required and ids['REQ-V51-043-002'].category == 'MARKET_CAMPAIGN'
    out = tmp_path/'dossier.json'; payload = render_blocker_dossier(root/'requirements_acceptance_matrix.yaml', out)
    assert payload['p0_blocker_count'] == len(blockers) and out.exists()


def test_phase24_external_evidence_requires_timezone_aware_observation(tmp_path: Path):
    artifact = tmp_path/'x'; artifact.write_text('x')
    e = ExternalEvidence('x','PASS','TEST','x',sha256(b'x').hexdigest(),True,0,datetime(2026,1,1))
    ok, reason = e.validate(tmp_path)
    assert not ok and 'timezone-aware' in reason
