from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.release.campaign_collector import (
    ReadOnlyBinancePublicCollector,
    acceptance_blockers,
    append_attested_runtime_event,
    append_collection_event,
    collection_event_counts,
    collection_path,
    derive_collection_metrics,
    initialize_collection,
    load_collection,
    telemetry_key_id,
    write_sealed_source,
)

CANDIDATE = "a" * 40
ENV_HASH = "b" * 64
TOPOLOGY_HASH = "c" * 64
TELEMETRY_KEY = "phase265-test-telemetry-key-material-000000000000000000"
WRONG_KEY = "phase265-wrong-telemetry-key-material-11111111111111111"


def _collection(tmp_path: Path, now: datetime) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    state = tmp_path / "state"
    path = collection_path(state, repository_root=root, candidate_sha=CANDIDATE)
    initialize_collection(
        path,
        repository_root=root,
        candidate_sha=CANDIDATE,
        environment_hash=ENV_HASH,
        topology_hash=TOPOLOGY_HASH,
        now=now,
    )
    return root, path


def _paper_payload(sample_id: str = "p1") -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "decision": "LONG",
        "market_regime": "trend",
        "market_data_origin": "REAL",
        "execution_divergence_bps": 1.0,
    }


def test_state_must_live_outside_repository(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    with pytest.raises(ValueError, match="outside repository root"):
        collection_path(root / "runtime", repository_root=root, candidate_sha=CANDIDATE)


def test_unattested_relabelled_real_json_never_counts_toward_acceptance(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    append_collection_event(
        path,
        kind="paper_sample",
        payload=_paper_payload(),
        observed_at=now,
        now=now + timedelta(seconds=1),
    )
    rows = load_collection(path, now=now + timedelta(seconds=2))
    metrics = derive_collection_metrics(rows)

    assert collection_event_counts(rows) == {"total": 1, "acceptance_eligible": 0, "unattested_audit": 1}
    assert metrics["paper"]["effective_sample_size"] == 0.0
    assert metrics["paper"]["real_market_data"] is False
    assert "PRIVATE_STREAM_INCOMPLETE" in acceptance_blockers(metrics)


def test_attested_protected_runtime_event_counts_only_with_correct_key(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    append_attested_runtime_event(
        path,
        kind="paper_sample",
        payload=_paper_payload(),
        observed_at=now + timedelta(seconds=1),
        producer="PROTECTED_PAPER_RUNTIME",
        telemetry_key=TELEMETRY_KEY,
        now=now + timedelta(seconds=1),
    )
    rows = load_collection(path, telemetry_key=TELEMETRY_KEY, now=now + timedelta(seconds=2))
    assert collection_event_counts(rows) == {"total": 1, "acceptance_eligible": 1, "unattested_audit": 0}
    assert derive_collection_metrics(rows)["paper"]["effective_sample_size"] == 1.0

    with pytest.raises(ValueError, match="attestation verification failed"):
        load_collection(path, telemetry_key=WRONG_KEY, now=now + timedelta(seconds=2))


def test_attested_event_requires_allowlisted_producer_and_strong_key(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    with pytest.raises(ValueError, match="unsupported protected runtime producer"):
        append_attested_runtime_event(
            path,
            kind="paper_sample",
            payload=_paper_payload(),
            observed_at=now,
            producer="LOCAL_JSON_IMPORT",
            telemetry_key=TELEMETRY_KEY,
            now=now + timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="at least 32"):
        append_attested_runtime_event(
            path,
            kind="paper_sample",
            payload=_paper_payload(),
            observed_at=now,
            producer="PROTECTED_PAPER_RUNTIME",
            telemetry_key="too-short",
            now=now + timedelta(seconds=1),
        )


def test_live_shadow_submit_events_are_impossible_even_when_attested(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    with pytest.raises(ValueError, match="order submission evidence is forbidden"):
        append_attested_runtime_event(
            path,
            kind="live_shadow_exchange_submit_call",
            payload={"reason": "must-never-happen"},
            observed_at=now,
            producer="PROTECTED_LIVE_SHADOW_RUNTIME",
            telemetry_key=TELEMETRY_KEY,
            now=now + timedelta(seconds=1),
        )


def test_attested_realtime_campaign_event_cannot_be_backdated(tmp_path: Path) -> None:
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    with pytest.raises(ValueError, match="realtime protected-runtime observation"):
        append_attested_runtime_event(
            path,
            kind="paper_sample",
            payload=_paper_payload(),
            observed_at=now - timedelta(days=31),
            producer="PROTECTED_PAPER_RUNTIME",
            telemetry_key=TELEMETRY_KEY,
            now=now + timedelta(seconds=1),
        )


def test_profitability_pit_event_may_reference_historical_oos_time(tmp_path: Path) -> None:
    now = datetime(2026, 2, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    append_attested_runtime_event(
        path,
        kind="profitability_sample",
        payload={"sample_id": "oos-1", "data_origin": "REAL_PIT", "split": "OOS", "net_return_bps": 2.5},
        observed_at=now - timedelta(days=60),
        producer="PROTECTED_PIT_RUNTIME",
        telemetry_key=TELEMETRY_KEY,
        now=now + timedelta(seconds=1),
    )
    rows = load_collection(path, telemetry_key=TELEMETRY_KEY, now=now + timedelta(seconds=2))
    assert derive_collection_metrics(rows)["profitability"]["effective_sample_size"] == 1.0


def test_hash_chain_tamper_is_rejected_before_metrics(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    _, path = _collection(tmp_path, now)
    append_collection_event(
        path,
        kind="private_event",
        payload={"event_id": "1"},
        observed_at=now,
        now=now + timedelta(seconds=1),
    )
    lines = path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["payload"]["event_id"] = "tampered"
    lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="record hash mismatch"):
        load_collection(path, now=now + timedelta(seconds=2))


def test_public_collector_has_no_order_surface_and_kill_switch_refuses_before_network() -> None:
    collector = ReadOnlyBinancePublicCollector()
    assert not hasattr(collector, "submit_order")
    assert not hasattr(collector, "cancel_order")
    assert not hasattr(collector, "place_order")
    collector.halt()
    with pytest.raises(RuntimeError, match="kill-switch"):
        collector.snapshot("BTCUSDT")


def test_sealed_source_binds_verified_attestation_key_without_exposing_secret(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    root, path = _collection(tmp_path, now)
    append_attested_runtime_event(
        path,
        kind="paper_sample",
        payload=_paper_payload(),
        observed_at=now + timedelta(seconds=1),
        producer="PROTECTED_PAPER_RUNTIME",
        telemetry_key=TELEMETRY_KEY,
        now=now + timedelta(seconds=1),
    )
    destination = root / "reports/external_acceptance/campaign/source/phase265_collection.json"
    digest, size = write_sealed_source(
        path,
        repository_root=root,
        destination=destination,
        telemetry_key=TELEMETRY_KEY,
    )
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert len(digest) == 64 and size > 0
    assert payload["telemetry_key_id"] == telemetry_key_id(TELEMETRY_KEY)
    assert TELEMETRY_KEY not in destination.read_text(encoding="utf-8")
    assert payload["event_counts"]["acceptance_eligible"] == 1
    assert payload["live_enabled"] is False
    assert payload["production_ready"] is False
