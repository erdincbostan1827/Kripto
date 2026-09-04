from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.release.campaign_evidence_recorder import (
    append_event,
    build_receipts,
    derive_metrics,
    initialize_journal,
    load_journal,
)

CANDIDATE = "a" * 40
CHALLENGE_SHA = "b" * 64
ENV_HASH = "c" * 64
TOPOLOGY_HASH = "d" * 64


def _init(path: Path, at: datetime) -> None:
    initialize_journal(
        path,
        candidate_sha=CANDIDATE,
        challenge_id="phase263-test-challenge",
        challenge_sha256=CHALLENGE_SHA,
        acceptance_environment_id_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        now=at,
    )


def test_hash_chain_rejects_tampered_campaign_observation(tmp_path: Path) -> None:
    journal = tmp_path / "campaign.jsonl"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _init(journal, now)
    append_event(journal, kind="private_event", payload={"event_id": "1"}, now=now + timedelta(seconds=1))

    lines = journal.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["payload"]["event_id"] = "tampered"
    lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
    journal.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="record hash mismatch"):
        load_journal(journal, now=now + timedelta(seconds=2))


def test_recorder_rejects_secret_like_payload_keys(tmp_path: Path) -> None:
    journal = tmp_path / "campaign.jsonl"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _init(journal, now)

    with pytest.raises(ValueError, match="secret-like key"):
        append_event(
            journal,
            kind="private_event",
            payload={"event_id": "1", "api_secret": "must-never-be-recorded"},
            now=now + timedelta(seconds=1),
        )


def test_campaign_durations_are_derived_from_recorded_wall_clock_span(tmp_path: Path) -> None:
    journal = tmp_path / "campaign.jsonl"
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _init(journal, start)
    append_event(
        journal,
        kind="paper_sample",
        payload={
            "sample_id": "paper-1",
            "decision": "LONG",
            "market_regime": "trend",
            "market_data_origin": "REAL",
            "execution_divergence_bps": 1.0,
        },
        now=start + timedelta(hours=1),
    )
    append_event(
        journal,
        kind="paper_sample",
        payload={
            "sample_id": "paper-2",
            "decision": "EXIT",
            "market_regime": "range",
            "market_data_origin": "REAL",
            "execution_divergence_bps": 2.0,
        },
        now=start + timedelta(days=31, hours=1),
    )
    append_event(
        journal,
        kind="live_shadow_observation",
        payload={"observation_id": "shadow-1", "market_data_origin": "REAL"},
        now=start + timedelta(days=31, hours=2),
    )
    append_event(
        journal,
        kind="live_shadow_observation",
        payload={"observation_id": "shadow-2", "market_data_origin": "REAL"},
        now=start + timedelta(days=39, hours=2),
    )
    rows = load_journal(journal, now=start + timedelta(days=40))
    metrics = derive_metrics(rows)

    assert metrics["paper"]["calendar_days"] == 31
    assert metrics["live-shadow"]["calendar_days"] == 8
    assert metrics["paper"]["effective_sample_size"] == 2.0
    assert metrics["live-shadow"]["observations"] == 2


def test_spot_short_and_submit_attempts_fail_closed_in_derived_metrics(tmp_path: Path) -> None:
    journal = tmp_path / "campaign.jsonl"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _init(journal, now)
    append_event(
        journal,
        kind="paper_sample",
        payload={
            "sample_id": "paper-short",
            "decision": "SHORT",
            "market_regime": "downtrend",
            "market_data_origin": "REAL",
            "execution_divergence_bps": 1.0,
        },
        now=now + timedelta(seconds=1),
    )
    append_event(
        journal,
        kind="live_shadow_order_submit_attempt",
        payload={"reason": "audit-observed-attempt"},
        now=now + timedelta(seconds=2),
    )
    append_event(
        journal,
        kind="live_shadow_exchange_submit_call",
        payload={"reason": "audit-observed-call"},
        now=now + timedelta(seconds=3),
    )
    metrics = derive_metrics(load_journal(journal, now=now + timedelta(seconds=4)))

    assert metrics["paper"]["active_market_type"] == "SPOT"
    assert metrics["paper"]["real_market_data"] is False
    assert metrics["live-shadow"]["real_orders_submitted"] == 1
    assert metrics["live-shadow"]["exchange_submit_calls"] == 1


def test_receipts_are_exact_candidate_environment_and_journal_hash_bound(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    journal = root / "reports/external_acceptance/campaign/source/campaign.jsonl"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _init(journal, now)
    append_event(journal, kind="private_event", payload={"event_id": "1"}, now=now + timedelta(seconds=1))

    receipts = build_receipts(journal, root=root, now=now + timedelta(seconds=2))
    private = receipts["private-stream"]
    source = private["source_artifacts"][0]

    assert private["git_commit_sha"] == CANDIDATE
    assert private["release_challenge"] == {
        "challenge_id": "phase263-test-challenge",
        "sha256": CHALLENGE_SHA,
    }
    assert private["environment"] == {
        "acceptance_environment_id_hash": ENV_HASH,
        "topology_hash": TOPOLOGY_HASH,
    }
    assert source["path"] == "reports/external_acceptance/campaign/source/campaign.jsonl"
    assert len(source["sha256"]) == 64
    assert private["real_system"] is True
    assert private["executed"] is True
