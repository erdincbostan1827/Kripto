from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
JOURNAL_CLASSIFICATION = "PHASE263_TAMPER_EVIDENT_CAMPAIGN_JOURNAL"
ZERO_HASH = "0" * 64
MAX_FUTURE_SKEW_SECONDS = 300
BOOTSTRAP_REPLICATES = 2000

EVENT_KINDS = frozenset(
    {
        "private_auth_lifecycle",
        "private_reconnect",
        "private_rest_reconciliation",
        "private_duplicate_idempotency",
        "private_out_of_order",
        "private_redaction",
        "private_event",
        "paper_sample",
        "paper_cost_stress_pass",
        "paper_latency_stress_pass",
        "paper_oos_pass",
        "live_shadow_observation",
        "live_shadow_kill_switch_pass",
        "live_shadow_reconciliation_pass",
        "live_shadow_order_submit_attempt",
        "live_shadow_exchange_submit_call",
        "profitability_sample",
        "profitability_oos_pass",
        "profitability_leakage_pass",
        "profitability_cost_stress_pass",
        "profitability_survivorship_pass",
    }
)
FORBIDDEN_PAYLOAD_KEY_FRAGMENTS = ("api_key", "api_secret", "authorization", "signature", "password", "token")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("journal timestamps must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _record_hash(payload: dict[str, Any]) -> str:
    row = dict(payload)
    row.pop("record_sha256", None)
    return hashlib.sha256(_canonical_bytes(row)).hexdigest()


def _binding(
    *,
    candidate_sha: str,
    challenge_id: str,
    challenge_sha256: str,
    acceptance_environment_id_hash: str,
    topology_hash: str,
) -> dict[str, Any]:
    values = {
        "candidate_sha": candidate_sha.lower(),
        "challenge_id": challenge_id,
        "challenge_sha256": challenge_sha256.lower(),
        "acceptance_environment_id_hash": acceptance_environment_id_hash.lower(),
        "topology_hash": topology_hash.lower(),
    }
    if len(values["candidate_sha"]) != 40 or any(c not in "0123456789abcdef" for c in values["candidate_sha"]):
        raise ValueError("candidate SHA must be exact 40-char lowercase hex")
    for field in ("challenge_sha256", "acceptance_environment_id_hash", "topology_hash"):
        value = values[field]
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"{field} must be exact 64-char lowercase hex")
    if not isinstance(challenge_id, str) or not challenge_id.strip():
        raise ValueError("challenge_id must be non-empty")
    return values


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if any(fragment in normalized for fragment in FORBIDDEN_PAYLOAD_KEY_FRAGMENTS):
                return True
            if _contains_sensitive_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _validate_event_payload(kind: str, payload: dict[str, Any]) -> None:
    if kind not in EVENT_KINDS:
        raise ValueError(f"unsupported campaign journal event kind: {kind}")
    if _contains_sensitive_key(payload):
        raise ValueError("campaign journal payload contains a secret-like key")
    if kind == "paper_sample":
        sample_id = str(payload.get("sample_id", "")).strip()
        decision = str(payload.get("decision", "")).strip().upper()
        regime = str(payload.get("market_regime", "")).strip()
        origin = str(payload.get("market_data_origin", "")).strip().upper()
        if not sample_id or decision not in {"LONG", "EXIT", "HOLD", "SHORT"} or not regime or origin != "REAL":
            raise ValueError("paper_sample requires sample_id, decision, market_regime, and REAL market_data_origin")
        divergence = float(str(payload.get("execution_divergence_bps")))
        if not math.isfinite(divergence) or divergence < 0:
            raise ValueError("paper_sample execution_divergence_bps must be finite and non-negative")
    elif kind == "live_shadow_observation":
        if str(payload.get("market_data_origin", "")).strip().upper() != "REAL":
            raise ValueError("live_shadow_observation requires REAL market_data_origin")
        if not str(payload.get("observation_id", "")).strip():
            raise ValueError("live_shadow_observation requires observation_id")
    elif kind == "profitability_sample":
        if str(payload.get("data_origin", "")).strip().upper() != "REAL_PIT":
            raise ValueError("profitability_sample requires REAL_PIT data_origin")
        if str(payload.get("split", "")).strip().upper() != "OOS":
            raise ValueError("profitability_sample requires OOS split")
        if not str(payload.get("sample_id", "")).strip():
            raise ValueError("profitability_sample requires sample_id")
        value = float(str(payload.get("net_return_bps")))
        if not math.isfinite(value):
            raise ValueError("profitability_sample net_return_bps must be finite")


def initialize_journal(
    path: Path,
    *,
    candidate_sha: str,
    challenge_id: str,
    challenge_sha256: str,
    acceptance_environment_id_hash: str,
    topology_hash: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    binding = _binding(
        candidate_sha=candidate_sha,
        challenge_id=challenge_id,
        challenge_sha256=challenge_sha256,
        acceptance_environment_id_hash=acceptance_environment_id_hash,
        topology_hash=topology_hash,
    )
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "classification": JOURNAL_CLASSIFICATION,
        "record_type": "header",
        "sequence": 0,
        "recorded_at": _iso(now or _utc_now()),
        "previous_sha256": ZERO_HASH,
        **binding,
        "collector_mode": "REAL_EXTERNAL",
        "synthetic": False,
    }
    record["record_sha256"] = _record_hash(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def load_journal(path: Path, *, now: datetime | None = None) -> list[dict[str, Any]]:
    reference_now = (now or _utc_now()).astimezone(timezone.utc)
    rows: list[dict[str, Any]] = []
    previous_hash = ZERO_HASH
    previous_time: datetime | None = None
    header_binding: dict[str, Any] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                raise ValueError("campaign journal contains a blank record")
            loaded = json.loads(line)
            if not isinstance(loaded, dict):
                raise ValueError("campaign journal record must be a JSON object")
            row = dict(loaded)
            if row.get("schema_version") != SCHEMA_VERSION or row.get("classification") != JOURNAL_CLASSIFICATION:
                raise ValueError("campaign journal schema/classification mismatch")
            if row.get("sequence") != index or row.get("previous_sha256") != previous_hash:
                raise ValueError("campaign journal sequence/hash chain is broken")
            if row.get("record_sha256") != _record_hash(row):
                raise ValueError("campaign journal record hash mismatch")
            timestamp = _parse_time(row.get("recorded_at"))
            if timestamp.timestamp() > reference_now.timestamp() + MAX_FUTURE_SKEW_SECONDS:
                raise ValueError("campaign journal contains a future record")
            if previous_time is not None and timestamp < previous_time:
                raise ValueError("campaign journal clock moved backwards")
            current_binding = {
                key: row.get(key)
                for key in (
                    "candidate_sha",
                    "challenge_id",
                    "challenge_sha256",
                    "acceptance_environment_id_hash",
                    "topology_hash",
                )
            }
            if index == 0:
                if row.get("record_type") != "header" or row.get("collector_mode") != "REAL_EXTERNAL":
                    raise ValueError("campaign journal header is invalid")
                if row.get("synthetic") is not False:
                    raise ValueError("synthetic campaign journal cannot be acceptance evidence")
                _binding(
                    candidate_sha=str(row.get("candidate_sha", "")),
                    challenge_id=str(row.get("challenge_id", "")),
                    challenge_sha256=str(row.get("challenge_sha256", "")),
                    acceptance_environment_id_hash=str(row.get("acceptance_environment_id_hash", "")),
                    topology_hash=str(row.get("topology_hash", "")),
                )
                header_binding = current_binding
            else:
                if row.get("record_type") != "event" or current_binding != header_binding:
                    raise ValueError("campaign journal event/binding is invalid")
                payload = row.get("payload")
                if not isinstance(payload, dict):
                    raise ValueError("campaign journal event payload must be an object")
                _validate_event_payload(str(row.get("kind", "")), payload)
            rows.append(row)
            previous_hash = str(row["record_sha256"])
            previous_time = timestamp
    if not rows:
        raise ValueError("campaign journal is empty")
    return rows


def append_event(path: Path, *, kind: str, payload: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    _validate_event_payload(kind, payload)
    reference_now = now or _utc_now()
    rows = load_journal(path, now=reference_now)
    header, last = rows[0], rows[-1]
    timestamp = reference_now.astimezone(timezone.utc)
    if timestamp < _parse_time(last["recorded_at"]):
        raise ValueError("system clock moved backwards; refusing campaign journal append")
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "classification": JOURNAL_CLASSIFICATION,
        "record_type": "event",
        "sequence": len(rows),
        "recorded_at": _iso(timestamp),
        "previous_sha256": last["record_sha256"],
        "candidate_sha": header["candidate_sha"],
        "challenge_id": header["challenge_id"],
        "challenge_sha256": header["challenge_sha256"],
        "acceptance_environment_id_hash": header["acceptance_environment_id_hash"],
        "topology_hash": header["topology_hash"],
        "kind": kind,
        "payload": payload,
    }
    record["record_sha256"] = _record_hash(record)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record


def _events(rows: Iterable[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("record_type") == "event" and row.get("kind") == kind]


def _elapsed_days(rows: list[dict[str, Any]]) -> int:
    if len(rows) < 2:
        return 0
    first = _parse_time(rows[0]["recorded_at"])
    last = _parse_time(rows[-1]["recorded_at"])
    return max(0, int((last - first).total_seconds() // 86400))


def _bootstrap_lower_mean(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    seed = hashlib.sha256(_canonical_bytes({"values": values})).digest()
    n = len(values)
    means: list[float] = []
    for replicate in range(BOOTSTRAP_REPLICATES):
        sample: list[float] = []
        for position in range(n):
            counter = replicate.to_bytes(8, "big") + position.to_bytes(8, "big")
            digest = hashlib.sha256(seed + counter).digest()
            sample.append(values[int.from_bytes(digest[:8], "big") % n])
        means.append(fmean(sample))
    means.sort()
    return float(means[max(0, int(0.025 * (len(means) - 1)))])


def _probabilistic_sharpe_ratio(values: list[float]) -> float:
    n = len(values)
    if n < 3:
        return 0.0
    mean, std = fmean(values), pstdev(values)
    if not math.isfinite(std) or std <= 0:
        return 0.0
    sharpe = mean / std
    centered = [(value - mean) / std for value in values]
    skew = fmean(value**3 for value in centered)
    kurtosis = fmean(value**4 for value in centered)
    variance_term = 1.0 - skew * sharpe + ((kurtosis - 1.0) / 4.0) * sharpe * sharpe
    if not math.isfinite(variance_term) or variance_term <= 0:
        return 0.0
    z_score = sharpe * math.sqrt(n - 1) / math.sqrt(variance_term)
    return 0.5 * (1.0 + math.erf(z_score / math.sqrt(2.0)))


def derive_metrics(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    paper_samples = _events(rows, "paper_sample")
    paper_ids = {str(row["payload"]["sample_id"]) for row in paper_samples}
    decisions = [str(row["payload"]["decision"]).upper() for row in paper_samples]
    regimes = sorted({str(row["payload"]["market_regime"]).strip().upper() for row in paper_samples})
    divergences = [float(row["payload"]["execution_divergence_bps"]) for row in paper_samples]
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
            "calendar_days": _elapsed_days(paper_samples),
            "market_regimes": regimes,
            "long_examples": decisions.count("LONG"),
            "exit_examples": decisions.count("EXIT"),
            "short_examples": decisions.count("SHORT"),
            "active_market_type": "SPOT",
            "cost_stress_passed": bool(_events(rows, "paper_cost_stress_pass")),
            "latency_stress_passed": bool(_events(rows, "paper_latency_stress_pass")),
            "independent_oos_passed": bool(_events(rows, "paper_oos_pass")),
            "execution_divergence_bps": max(divergences, default=-1.0),
            "real_market_data": bool(paper_samples)
            and all(str(row["payload"]["market_data_origin"]).upper() == "REAL" for row in paper_samples)
            and "SHORT" not in decisions,
        },
        "live-shadow": {
            "real_market_data": bool(shadow)
            and all(str(row["payload"]["market_data_origin"]).upper() == "REAL" for row in shadow),
            "calendar_days": _elapsed_days(shadow),
            "observations": len(shadow_ids),
            "real_orders_submitted": len(_events(rows, "live_shadow_order_submit_attempt")),
            "exchange_submit_calls": len(_events(rows, "live_shadow_exchange_submit_call")),
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


def build_receipts(journal_path: Path, *, root: Path, now: datetime | None = None) -> dict[str, dict[str, Any]]:
    rows = load_journal(journal_path, now=now)
    try:
        source_path = journal_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("campaign journal must be inside repository root for evidence bundling") from exc
    journal_bytes = journal_path.resolve().read_bytes()
    header = rows[0]
    metrics = derive_metrics(rows)
    common = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso(now or _utc_now()),
        "git_commit_sha": header["candidate_sha"],
        "real_system": True,
        "executed": len(rows) > 1,
        "release_challenge": {"challenge_id": header["challenge_id"], "sha256": header["challenge_sha256"]},
        "environment": {
            "acceptance_environment_id_hash": header["acceptance_environment_id_hash"],
            "topology_hash": header["topology_hash"],
        },
        "source_artifacts": [
            {
                "path": source_path,
                "sha256": hashlib.sha256(journal_bytes).hexdigest(),
                "bytes": len(journal_bytes),
                "classification": JOURNAL_CLASSIFICATION,
            }
        ],
    }
    classifications = {
        "private-stream": "CREDENTIALED_PRIVATE_STREAM_ACCEPTANCE",
        "paper": "REAL_MARKET_PAPER_CAMPAIGN_ACCEPTANCE",
        "live-shadow": "LIVE_SHADOW_CAMPAIGN_ACCEPTANCE",
        "profitability": "REAL_PIT_PROFITABILITY_ACCEPTANCE",
    }
    return {
        kind: {**common, "classification": classification, "metrics": metrics[kind]}
        for kind, classification in classifications.items()
    }


def write_receipts(
    journal_path: Path,
    *,
    root: Path,
    output_dir: Path,
    now: datetime | None = None,
) -> dict[str, Path]:
    receipts = build_receipts(journal_path, root=root, now=now)
    output_dir.mkdir(parents=True, exist_ok=True)
    names = {
        "private-stream": "private_stream.json",
        "paper": "paper_campaign.json",
        "live-shadow": "live_shadow.json",
        "profitability": "profitability.json",
    }
    written: dict[str, Path] = {}
    for kind, name in names.items():
        destination = output_dir / name
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(receipts[kind], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, destination)
        written[kind] = destination
    return written
