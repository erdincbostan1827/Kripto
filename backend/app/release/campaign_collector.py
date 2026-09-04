from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

import httpx

from app.release.campaign_evidence_recorder import (
    EVENT_KINDS,
    _bootstrap_lower_mean,
    _probabilistic_sharpe_ratio,
    _validate_event_payload,
)
from app.release.paper_campaign import PaperCampaignEvidence, PaperCampaignPolicy

SCHEMA_VERSION = "1.1"
COLLECTION_CLASSIFICATION = "PHASE265_REAL_CAMPAIGN_COLLECTION"
SEALED_SOURCE_CLASSIFICATION = "PHASE265_SEALED_REAL_CAMPAIGN_SOURCE"
ZERO_HASH = "0" * 64
MAX_FUTURE_SKEW_SECONDS = 300
MAX_REALTIME_ATTESTATION_SKEW_SECONDS = 300
FORBIDDEN_RAW_KINDS = frozenset({"live_shadow_order_submit_attempt", "live_shadow_exchange_submit_call"})
PUBLIC_BINANCE_ORIGIN = "https://api.binance.com"
UNATTESTED_PRODUCER = "EXTERNAL_UNATTESTED_AUDIT"
TRUSTED_RUNTIME_PRODUCERS = frozenset(
    {
        "PROTECTED_PRIVATE_STREAM_RUNTIME",
        "PROTECTED_PAPER_RUNTIME",
        "PROTECTED_LIVE_SHADOW_RUNTIME",
        "PROTECTED_PIT_RUNTIME",
    }
)
ATTESTATION_SCHEME = "HMAC-SHA256"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("campaign timestamps must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _record_hash(payload: dict[str, Any]) -> str:
    row = dict(payload)
    row.pop("record_sha256", None)
    row.pop("_phase265_attestation_verified", None)
    return hashlib.sha256(_canonical_bytes(row)).hexdigest()


def _exact_hex(value: str, length: int, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != length or any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError(f"{field} must be exact {length}-character lowercase hex")
    return normalized


def environment_id_hash(environment_id: str) -> str:
    value = environment_id.strip()
    if not value:
        raise ValueError("acceptance environment id must be non-empty")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _binding(*, candidate_sha: str, environment_hash: str, topology_hash: str) -> dict[str, str]:
    return {
        "candidate_sha": _exact_hex(candidate_sha, 40, field="candidate SHA"),
        "acceptance_environment_id_hash": _exact_hex(environment_hash, 64, field="acceptance environment id hash"),
        "topology_hash": _exact_hex(topology_hash, 64, field="topology hash"),
    }


def _attestation_key_bytes(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) < 32:
        raise ValueError("Phase265 telemetry attestation key must contain at least 32 UTF-8 bytes")
    return raw


def telemetry_key_id(value: str) -> str:
    return hashlib.sha256(_attestation_key_bytes(value)).hexdigest()


def _attestation_message(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": record["schema_version"],
        "classification": record["classification"],
        "candidate_sha": record["candidate_sha"],
        "acceptance_environment_id_hash": record["acceptance_environment_id_hash"],
        "topology_hash": record["topology_hash"],
        "sequence": record["sequence"],
        "observed_at": record["observed_at"],
        "kind": record["kind"],
        "producer": record["producer"],
        "payload": record["payload"],
    }


def _attest(record: dict[str, Any], *, telemetry_key: str) -> dict[str, str]:
    key = _attestation_key_bytes(telemetry_key)
    digest = hmac.new(key, _canonical_bytes(_attestation_message(record)), hashlib.sha256).hexdigest()
    return {"scheme": ATTESTATION_SCHEME, "key_id": hashlib.sha256(key).hexdigest(), "sha256": digest}


def _verify_attestation(record: dict[str, Any], *, telemetry_key: str) -> bool:
    attestation = record.get("attestation")
    if not isinstance(attestation, dict) or attestation.get("scheme") != ATTESTATION_SCHEME:
        return False
    expected = _attest(record, telemetry_key=telemetry_key)
    return (
        attestation.get("key_id") == expected["key_id"]
        and isinstance(attestation.get("sha256"), str)
        and hmac.compare_digest(str(attestation["sha256"]), expected["sha256"])
    )


def collection_path(state_dir: Path, *, repository_root: Path, candidate_sha: str) -> Path:
    if not state_dir.is_absolute():
        raise ValueError("campaign state directory must be absolute")
    resolved_state = state_dir.resolve()
    resolved_root = repository_root.resolve()
    if resolved_state == resolved_root or resolved_root in resolved_state.parents:
        raise ValueError("campaign state directory must be outside repository root")
    candidate = _exact_hex(candidate_sha, 40, field="candidate SHA")
    return resolved_state / candidate / "phase265_collection.jsonl"


def initialize_collection(
    path: Path,
    *,
    repository_root: Path,
    candidate_sha: str,
    environment_hash: str,
    topology_hash: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    expected = collection_path(path.parent.parent, repository_root=repository_root, candidate_sha=candidate_sha)
    if path.resolve() != expected.resolve():
        raise ValueError("campaign collection path is not the canonical candidate-specific state path")
    binding = _binding(candidate_sha=candidate_sha, environment_hash=environment_hash, topology_hash=topology_hash)
    timestamp = (now or _utc_now()).astimezone(timezone.utc)
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "classification": COLLECTION_CLASSIFICATION,
        "record_type": "header",
        "sequence": 0,
        "recorded_at": _iso(timestamp),
        "previous_sha256": ZERO_HASH,
        **binding,
        "collector_mode": "ATTESTED_PROTECTED_RUNTIME_APPEND_ONLY",
        "synthetic": False,
        "live_enabled": False,
        "production_ready": False,
    }
    record["record_sha256"] = _record_hash(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def load_collection(
    path: Path,
    *,
    candidate_sha: str | None = None,
    environment_hash: str | None = None,
    topology_hash: str | None = None,
    telemetry_key: str | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    reference_now = (now or _utc_now()).astimezone(timezone.utc)
    rows: list[dict[str, Any]] = []
    previous_hash = ZERO_HASH
    previous_recorded_at: datetime | None = None
    header_binding: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                raise ValueError("campaign collection contains a blank record")
            loaded = json.loads(line)
            if not isinstance(loaded, dict):
                raise ValueError("campaign collection record must be a JSON object")
            row = dict(loaded)
            if row.get("schema_version") != SCHEMA_VERSION or row.get("classification") != COLLECTION_CLASSIFICATION:
                raise ValueError("campaign collection schema/classification mismatch")
            if row.get("sequence") != index or row.get("previous_sha256") != previous_hash:
                raise ValueError("campaign collection sequence/hash chain is broken")
            if row.get("record_sha256") != _record_hash(row):
                raise ValueError("campaign collection record hash mismatch")
            recorded_at = _parse_time(row.get("recorded_at"))
            if recorded_at.timestamp() > reference_now.timestamp() + MAX_FUTURE_SKEW_SECONDS:
                raise ValueError("campaign collection contains a future record")
            if previous_recorded_at is not None and recorded_at < previous_recorded_at:
                raise ValueError("campaign collection clock moved backwards")
            current_binding = {
                "candidate_sha": row.get("candidate_sha"),
                "acceptance_environment_id_hash": row.get("acceptance_environment_id_hash"),
                "topology_hash": row.get("topology_hash"),
            }
            if index == 0:
                if row.get("record_type") != "header" or row.get("collector_mode") != "ATTESTED_PROTECTED_RUNTIME_APPEND_ONLY":
                    raise ValueError("campaign collection header is invalid")
                if row.get("synthetic") is not False or row.get("live_enabled") is not False or row.get("production_ready") is not False:
                    raise ValueError("campaign collection safety boundary is invalid")
                _binding(
                    candidate_sha=str(row.get("candidate_sha", "")),
                    environment_hash=str(row.get("acceptance_environment_id_hash", "")),
                    topology_hash=str(row.get("topology_hash", "")),
                )
                header_binding = current_binding
            else:
                if row.get("record_type") != "event" or current_binding != header_binding:
                    raise ValueError("campaign collection event/binding is invalid")
                kind = str(row.get("kind", ""))
                if kind not in EVENT_KINDS or kind in FORBIDDEN_RAW_KINDS:
                    raise ValueError("campaign collection contains an unsafe or unsupported event kind")
                payload = row.get("payload")
                if not isinstance(payload, dict):
                    raise ValueError("campaign collection payload must be an object")
                _validate_event_payload(kind, payload)
                observed_at = _parse_time(row.get("observed_at"))
                if observed_at.timestamp() > reference_now.timestamp() + MAX_FUTURE_SKEW_SECONDS:
                    raise ValueError("campaign collection contains a future observation")
                eligible = row.get("acceptance_eligible") is True
                producer = str(row.get("producer", ""))
                if eligible:
                    if producer not in TRUSTED_RUNTIME_PRODUCERS:
                        raise ValueError("acceptance-eligible campaign event has an untrusted producer")
                    if telemetry_key is None:
                        raise ValueError("telemetry attestation key is required to load acceptance-eligible events")
                    if not _verify_attestation(row, telemetry_key=telemetry_key):
                        raise ValueError("campaign telemetry attestation verification failed")
                    if not kind.startswith("profitability_"):
                        skew = abs((recorded_at - observed_at).total_seconds())
                        if skew > MAX_REALTIME_ATTESTATION_SKEW_SECONDS:
                            raise ValueError("attested realtime protected-runtime observation is backdated or future-skewed")
                    row["_phase265_attestation_verified"] = True
                else:
                    if producer != UNATTESTED_PRODUCER or "attestation" in row:
                        raise ValueError("unattested audit event provenance is invalid")
                    row["_phase265_attestation_verified"] = False
            rows.append(row)
            previous_hash = str(row["record_sha256"])
            previous_recorded_at = recorded_at
    if not rows or header_binding is None:
        raise ValueError("campaign collection is empty")
    if candidate_sha is not None and header_binding["candidate_sha"] != _exact_hex(candidate_sha, 40, field="candidate SHA"):
        raise ValueError("campaign collection candidate SHA mismatch")
    if environment_hash is not None and header_binding["acceptance_environment_id_hash"] != _exact_hex(
        environment_hash, 64, field="acceptance environment id hash"
    ):
        raise ValueError("campaign collection environment mismatch")
    if topology_hash is not None and header_binding["topology_hash"] != _exact_hex(topology_hash, 64, field="topology hash"):
        raise ValueError("campaign collection topology mismatch")
    return rows


def _base_event_record(
    rows: list[dict[str, Any]], *, kind: str, payload: dict[str, Any], observed_at: datetime, now: datetime, producer: str
) -> dict[str, Any]:
    if kind in FORBIDDEN_RAW_KINDS:
        raise ValueError("live-shadow order submission evidence is forbidden by Phase265")
    _validate_event_payload(kind, payload)
    observed = observed_at.astimezone(timezone.utc)
    if observed.timestamp() > now.timestamp() + MAX_FUTURE_SKEW_SECONDS:
        raise ValueError("future observed_at is not accepted")
    header, last = rows[0], rows[-1]
    if now < _parse_time(last["recorded_at"]):
        raise ValueError("system clock moved backwards; refusing campaign collection append")
    return {
        "schema_version": SCHEMA_VERSION,
        "classification": COLLECTION_CLASSIFICATION,
        "record_type": "event",
        "sequence": len(rows),
        "recorded_at": _iso(now),
        "observed_at": _iso(observed),
        "previous_sha256": last["record_sha256"],
        "candidate_sha": header["candidate_sha"],
        "acceptance_environment_id_hash": header["acceptance_environment_id_hash"],
        "topology_hash": header["topology_hash"],
        "kind": kind,
        "producer": producer,
        "payload": dict(payload),
    }


def _persist_event(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    record["record_sha256"] = _record_hash(record)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def append_collection_event(
    path: Path,
    *,
    kind: str,
    payload: dict[str, Any],
    observed_at: datetime,
    telemetry_key: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append audit-only telemetry. It can never contribute to acceptance metrics."""
    reference_now = (now or _utc_now()).astimezone(timezone.utc)
    rows = load_collection(path, telemetry_key=telemetry_key, now=reference_now)
    record = _base_event_record(
        rows,
        kind=kind,
        payload=payload,
        observed_at=observed_at,
        now=reference_now,
        producer=UNATTESTED_PRODUCER,
    )
    record["acceptance_eligible"] = False
    return _persist_event(path, record)


def append_attested_runtime_event(
    path: Path,
    *,
    kind: str,
    payload: dict[str, Any],
    observed_at: datetime,
    producer: str,
    telemetry_key: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Append a protected-runtime event authenticated by a runner-only telemetry key."""
    if producer not in TRUSTED_RUNTIME_PRODUCERS:
        raise ValueError("unsupported protected runtime producer")
    reference_now = (now or _utc_now()).astimezone(timezone.utc)
    observed = observed_at.astimezone(timezone.utc)
    if not kind.startswith("profitability_"):
        skew = abs((reference_now - observed).total_seconds())
        if skew > MAX_REALTIME_ATTESTATION_SKEW_SECONDS:
            raise ValueError("attested realtime protected-runtime observation is backdated or future-skewed")
    rows = load_collection(path, telemetry_key=telemetry_key, now=reference_now)
    record = _base_event_record(
        rows,
        kind=kind,
        payload=payload,
        observed_at=observed,
        now=reference_now,
        producer=producer,
    )
    record["acceptance_eligible"] = True
    record["attestation"] = _attest(record, telemetry_key=telemetry_key)
    return _persist_event(path, record)


def _events(rows: Iterable[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("record_type") == "event"
        and row.get("kind") == kind
        and row.get("acceptance_eligible") is True
        and row.get("_phase265_attestation_verified") is True
    ]


def _elapsed_observed_days(rows: list[dict[str, Any]]) -> int:
    if len(rows) < 2:
        return 0
    observed = [_parse_time(row["observed_at"]) for row in rows]
    return max(0, int((max(observed) - min(observed)).total_seconds() // 86400))


def derive_collection_metrics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    paper = _events(rows, "paper_sample")
    paper_ids = {str(row["payload"]["sample_id"]) for row in paper}
    decisions = [str(row["payload"]["decision"]).upper() for row in paper]
    regimes = sorted({str(row["payload"]["market_regime"]).strip().upper() for row in paper})
    divergences = [float(row["payload"]["execution_divergence_bps"]) for row in paper]
    shadow = _events(rows, "live_shadow_observation")
    shadow_ids = {str(row["payload"]["observation_id"]) for row in shadow}
    profitability = _events(rows, "profitability_sample")
    profitability_by_id = {
        str(row["payload"]["sample_id"]): float(row["payload"]["net_return_bps"]) for row in profitability
    }
    returns = list(profitability_by_id.values())
    return {
        "private-stream": {
            "credentialed_testnet": bool(_events(rows, "private_auth_lifecycle")),
            "auth_lifecycle_passed": bool(_events(rows, "private_auth_lifecycle")),
            "reconnect_passed": bool(_events(rows, "private_reconnect")),
            "rest_reconciliation_passed": bool(_events(rows, "private_rest_reconciliation")),
            "duplicate_event_idempotency_passed": bool(_events(rows, "private_duplicate_idempotency")),
            "out_of_order_protection_passed": bool(_events(rows, "private_out_of_order")),
            "secrets_redacted": bool(_events(rows, "private_redaction")),
            "observed_events": len(_events(rows, "private_event")),
        },
        "paper": {
            "effective_sample_size": float(len(paper_ids)),
            "calendar_days": _elapsed_observed_days(paper),
            "market_regimes": regimes,
            "long_examples": decisions.count("LONG"),
            "exit_examples": decisions.count("EXIT"),
            "short_examples": decisions.count("SHORT"),
            "active_market_type": "SPOT",
            "cost_stress_passed": bool(_events(rows, "paper_cost_stress_pass")),
            "latency_stress_passed": bool(_events(rows, "paper_latency_stress_pass")),
            "independent_oos_passed": bool(_events(rows, "paper_oos_pass")),
            "execution_divergence_bps": max(divergences, default=-1.0),
            "real_market_data": bool(paper)
            and all(str(row["payload"]["market_data_origin"]).upper() == "REAL" for row in paper)
            and "SHORT" not in decisions,
        },
        "live-shadow": {
            "real_market_data": bool(shadow)
            and all(str(row["payload"]["market_data_origin"]).upper() == "REAL" for row in shadow),
            "calendar_days": _elapsed_observed_days(shadow),
            "observations": len(shadow_ids),
            "real_orders_submitted": 0,
            "exchange_submit_calls": 0,
            "kill_switch_tested": bool(_events(rows, "live_shadow_kill_switch_pass")),
            "reconciliation_passed": bool(_events(rows, "live_shadow_reconciliation_pass")),
        },
        "profitability": {
            "real_point_in_time_data": bool(profitability)
            and all(str(row["payload"]["data_origin"]).upper() == "REAL_PIT" for row in profitability),
            "independent_oos": bool(profitability)
            and all(str(row["payload"]["split"]).upper() == "OOS" for row in profitability)
            and bool(_events(rows, "profitability_oos_pass")),
            "leakage_checks_passed": bool(_events(rows, "profitability_leakage_pass")),
            "cost_stress_passed": bool(_events(rows, "profitability_cost_stress_pass")),
            "survivorship_controls_passed": bool(_events(rows, "profitability_survivorship_pass")),
            "effective_sample_size": float(len(profitability_by_id)),
            "net_expectancy_bps": fmean(returns) if returns else 0.0,
            "bootstrap_ci_lower_bps": _bootstrap_lower_mean(returns),
            "probabilistic_sharpe_ratio": _probabilistic_sharpe_ratio(returns),
        },
    }


def acceptance_blockers(metrics: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    private = metrics["private-stream"]
    if any(
        private.get(field) is not True
        for field in (
            "credentialed_testnet",
            "auth_lifecycle_passed",
            "reconnect_passed",
            "rest_reconciliation_passed",
            "duplicate_event_idempotency_passed",
            "out_of_order_protection_passed",
            "secrets_redacted",
        )
    ) or int(private.get("observed_events", 0)) <= 0:
        blockers.append("PRIVATE_STREAM_INCOMPLETE")
    paper = metrics["paper"]
    paper_evidence = PaperCampaignEvidence(
        effective_sample_size=float(paper["effective_sample_size"]),
        calendar_days=int(paper["calendar_days"]),
        market_regimes=tuple(str(value) for value in paper["market_regimes"]),
        long_examples=int(paper["long_examples"]),
        exit_examples=int(paper["exit_examples"]),
        short_examples=int(paper["short_examples"]),
        active_market_type=str(paper["active_market_type"]),
        cost_stress_passed=paper["cost_stress_passed"] is True,
        latency_stress_passed=paper["latency_stress_passed"] is True,
        independent_oos_passed=paper["independent_oos_passed"] is True,
        execution_divergence_bps=float(paper["execution_divergence_bps"]),
        executed=True,
        real_market_data=paper["real_market_data"] is True,
    )
    blockers.extend(f"PAPER:{problem}" for problem in paper_evidence.blockers(PaperCampaignPolicy()))
    shadow = metrics["live-shadow"]
    if (
        shadow.get("real_market_data") is not True
        or int(shadow.get("calendar_days", 0)) < 7
        or int(shadow.get("observations", 0)) < 100
        or int(shadow.get("real_orders_submitted", -1)) != 0
        or int(shadow.get("exchange_submit_calls", -1)) != 0
        or shadow.get("kill_switch_tested") is not True
        or shadow.get("reconciliation_passed") is not True
    ):
        blockers.append("LIVE_SHADOW_INCOMPLETE")
    profitability_metrics = metrics["profitability"]
    if (
        profitability_metrics.get("real_point_in_time_data") is not True
        or profitability_metrics.get("independent_oos") is not True
        or profitability_metrics.get("leakage_checks_passed") is not True
        or profitability_metrics.get("cost_stress_passed") is not True
        or profitability_metrics.get("survivorship_controls_passed") is not True
        or float(profitability_metrics.get("effective_sample_size", 0.0)) < 100.0
        or float(profitability_metrics.get("net_expectancy_bps", 0.0)) <= 0.0
        or float(profitability_metrics.get("bootstrap_ci_lower_bps", 0.0)) <= 0.0
        or float(profitability_metrics.get("probabilistic_sharpe_ratio", 0.0)) < 0.95
    ):
        blockers.append("PROFITABILITY_INCOMPLETE")
    return blockers


class ReadOnlyBinancePublicCollector:
    """Public-market collector with no authenticated/order API surface by construction."""

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 30:
            raise ValueError("timeout_seconds must be in (0, 30]")
        self._timeout_seconds = timeout_seconds
        self._halted = False

    @property
    def halted(self) -> bool:
        return self._halted

    def halt(self) -> None:
        self._halted = True

    def snapshot(self, symbol: str) -> dict[str, Any]:
        if self._halted:
            raise RuntimeError("campaign collector kill-switch is active")
        normalized = symbol.strip().upper()
        if not normalized or not normalized.isalnum() or len(normalized) > 20:
            raise ValueError("invalid Binance public-market symbol")
        with httpx.Client(base_url=PUBLIC_BINANCE_ORIGIN, timeout=self._timeout_seconds, follow_redirects=False) as client:
            response = client.get("/api/v3/ticker/bookTicker", params={"symbol": normalized})
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Binance public-market response must be an object")
        bid = float(str(payload.get("bidPrice")))
        ask = float(str(payload.get("askPrice")))
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask <= 0 or ask < bid:
            raise ValueError("invalid Binance public-market bid/ask snapshot")
        observed = _iso(_utc_now())
        return {
            "observation_id": hashlib.sha256(f"{normalized}|{observed}|{bid}|{ask}".encode()).hexdigest(),
            "symbol": normalized,
            "bid_price": bid,
            "ask_price": ask,
            "market_data_origin": "REAL",
            "public_origin": PUBLIC_BINANCE_ORIGIN,
        }


def collection_event_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    events = [row for row in rows if row.get("record_type") == "event"]
    eligible = [row for row in events if row.get("_phase265_attestation_verified") is True]
    return {"total": len(events), "acceptance_eligible": len(eligible), "unattested_audit": len(events) - len(eligible)}


def write_sealed_source(
    raw_path: Path,
    *,
    repository_root: Path,
    destination: Path,
    telemetry_key: str,
) -> tuple[str, int]:
    rows = load_collection(raw_path, telemetry_key=telemetry_key)
    try:
        destination.resolve().relative_to(repository_root.resolve())
    except ValueError as exc:
        raise ValueError("sealed campaign source must be inside repository root") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw_bytes = raw_path.read_bytes()
    serialized_rows = [
        {key: value for key, value in row.items() if key != "_phase265_attestation_verified"}
        for row in rows
    ]
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "classification": SEALED_SOURCE_CLASSIFICATION,
        "source_collection_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "source_collection_bytes": len(raw_bytes),
        "source_collection_last_record_sha256": rows[-1]["record_sha256"],
        "candidate_sha": rows[0]["candidate_sha"],
        "acceptance_environment_id_hash": rows[0]["acceptance_environment_id_hash"],
        "topology_hash": rows[0]["topology_hash"],
        "telemetry_key_id": telemetry_key_id(telemetry_key),
        "event_counts": collection_event_counts(rows),
        "rows": serialized_rows,
        "live_enabled": False,
        "production_ready": False,
    }
    encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, destination)
    return hashlib.sha256(encoded).hexdigest(), len(encoded)
