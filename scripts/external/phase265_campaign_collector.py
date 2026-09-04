#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.release.acceptance_challenge import verify_challenge
from app.release.campaign_acceptance import verify_campaign_evidence
from app.release.campaign_collector import (
    COLLECTION_CLASSIFICATION,
    ReadOnlyBinancePublicCollector,
    acceptance_blockers,
    append_collection_event,
    collection_event_counts,
    collection_path,
    derive_collection_metrics,
    environment_id_hash,
    initialize_collection,
    load_collection,
    write_sealed_source,
)

RECEIPT_CLASSIFICATIONS = {
    "private-stream": "CREDENTIALED_PRIVATE_STREAM_ACCEPTANCE",
    "paper": "REAL_MARKET_PAPER_CAMPAIGN_ACCEPTANCE",
    "live-shadow": "LIVE_SHADOW_CAMPAIGN_ACCEPTANCE",
    "profitability": "REAL_PIT_PROFITABILITY_ACCEPTANCE",
}
RECEIPT_NAMES = {
    "private-stream": "private_stream.json",
    "paper": "paper_campaign.json",
    "live-shadow": "live_shadow.json",
    "profitability": "profitability.json",
}
TELEMETRY_KEY_ENV = "PHASE265_TELEMETRY_HMAC_KEY"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(args: argparse.Namespace) -> tuple[str, str, str]:
    environment_id = str(args.environment_id).strip()
    topology_hash = str(args.topology_hash).strip().lower()
    candidate = str(args.candidate).strip().lower()
    return candidate, environment_id_hash(environment_id), topology_hash


def _telemetry_key(*, required: bool = False) -> str | None:
    value = os.getenv(TELEMETRY_KEY_ENV, "")
    if value:
        if len(value.encode("utf-8")) < 32:
            raise ValueError(f"{TELEMETRY_KEY_ENV} must contain at least 32 UTF-8 bytes")
        return value
    if required:
        raise ValueError(f"{TELEMETRY_KEY_ENV} is required to verify/seal protected runtime telemetry")
    return None


def _git_sha() -> str:
    git_dir = ROOT / ".git"
    if not git_dir.is_dir():
        raise RuntimeError("Phase265 requires a regular Git checkout")
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref: "):
        return head.lower()
    ref = head[5:].strip()
    loose = git_dir / Path(*ref.split("/"))
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip().lower()
    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1].strip() == ref:
                return parts[0].strip().lower()
    raise RuntimeError("git HEAD ref could not be resolved")


def _state_path(args: argparse.Namespace) -> Path:
    return collection_path(Path(args.state_dir), repository_root=ROOT, candidate_sha=str(args.candidate))


def _ensure_collection(args: argparse.Namespace) -> Path:
    candidate, env_hash, topology_hash = _binding(args)
    if _git_sha() != candidate:
        raise PermissionError("Phase265 candidate must equal exact current git HEAD")
    path = _state_path(args)
    if not path.exists():
        initialize_collection(
            path,
            repository_root=ROOT,
            candidate_sha=candidate,
            environment_hash=env_hash,
            topology_hash=topology_hash,
        )
    load_collection(
        path,
        candidate_sha=candidate,
        environment_hash=env_hash,
        topology_hash=topology_hash,
        telemetry_key=_telemetry_key(),
    )
    return path


def _collect_market_audit(args: argparse.Namespace) -> int:
    """Capture real public quotes for audit/debug only; never count them as shadow acceptance."""
    path = _ensure_collection(args)
    collector = ReadOnlyBinancePublicCollector(timeout_seconds=float(args.timeout_seconds))
    count = int(args.count)
    interval = float(args.interval_seconds)
    if count < 1 or count > 100:
        raise ValueError("count must be in [1, 100]")
    if interval < 0 or interval > 300:
        raise ValueError("interval_seconds must be in [0, 300]")
    for index in range(count):
        observed_at = _utc_now()
        payload = collector.snapshot(str(args.symbol))
        append_collection_event(path, kind="live_shadow_observation", payload=payload, observed_at=observed_at)
        if interval and index + 1 < count:
            time.sleep(interval)
    rows = load_collection(path, telemetry_key=_telemetry_key())
    metrics = derive_collection_metrics(rows)
    print(
        json.dumps(
            {
                "classification": "PHASE265_PUBLIC_MARKET_AUDIT_NOT_ACCEPTANCE_EVIDENCE",
                "acceptance_eligible": False,
                "event_counts": collection_event_counts(rows),
                "metrics": metrics,
                "blockers": acceptance_blockers(metrics),
                "live_enabled": False,
                "production_ready": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _kill_switch_audit(args: argparse.Namespace) -> int:
    path = _ensure_collection(args)
    collector = ReadOnlyBinancePublicCollector(timeout_seconds=float(args.timeout_seconds))
    collector.halt()
    refused = False
    try:
        collector.snapshot(str(args.symbol))
    except RuntimeError:
        refused = True
    if not refused:
        raise RuntimeError("kill-switch did not refuse public-market collection")
    append_collection_event(
        path,
        kind="live_shadow_kill_switch_pass",
        payload={"tested": True, "submit_capability_present": False, "network_call_refused_while_halted": True},
        observed_at=_utc_now(),
    )
    print("PHASE265_COLLECTOR_KILL_SWITCH_AUDIT=PASS_NOT_ACCEPTANCE_EVIDENCE")
    return 0


def _ingest_audit(args: argparse.Namespace) -> int:
    """Preserve imported telemetry for audit only. Imported labels can never affect acceptance metrics."""
    path = _ensure_collection(args)
    source = Path(args.source).resolve()
    if not source.is_absolute() or not source.is_file():
        raise ValueError("audit ingest source must be an existing absolute regular file")
    try:
        source.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("audit ingest source must be outside repository root")
    digest = _sha256(source)
    rows_added = 0
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank audit ingest record at line {line_number}")
            loaded = json.loads(line)
            if not isinstance(loaded, dict):
                raise ValueError(f"audit ingest record {line_number} must be an object")
            kind = str(loaded.get("kind", ""))
            payload = loaded.get("payload")
            if not isinstance(payload, dict):
                raise ValueError(f"audit ingest record {line_number} payload must be an object")
            enriched = dict(payload)
            enriched["source_artifact_sha256"] = digest
            enriched["source_line_number"] = line_number
            enriched["phase265_import_disposition"] = "UNATTESTED_AUDIT_ONLY"
            append_collection_event(
                path,
                kind=kind,
                payload=enriched,
                observed_at=_parse_time(loaded.get("observed_at")),
            )
            rows_added += 1
    rows = load_collection(path, telemetry_key=_telemetry_key())
    print(
        json.dumps(
            {
                "classification": "PHASE265_IMPORTED_TELEMETRY_AUDIT_NOT_ACCEPTANCE_EVIDENCE",
                "ingested_rows": rows_added,
                "source_sha256": digest,
                "acceptance_eligible": False,
                "event_counts": collection_event_counts(rows),
            },
            sort_keys=True,
        )
    )
    return 0


def _status(args: argparse.Namespace) -> int:
    path = _ensure_collection(args)
    rows = load_collection(path, telemetry_key=_telemetry_key())
    metrics = derive_collection_metrics(rows)
    status = {
        "schema_version": "1.0",
        "classification": "PHASE265_CAMPAIGN_COLLECTION_STATUS_NOT_ACCEPTANCE_EVIDENCE",
        "candidate_sha": rows[0]["candidate_sha"],
        "collection_path": str(path.resolve()),
        "event_counts": collection_event_counts(rows),
        "last_record_sha256": rows[-1]["record_sha256"],
        "metrics": metrics,
        "blockers": acceptance_blockers(metrics),
        "live_enabled": False,
        "production_ready": False,
    }
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


def _seal(args: argparse.Namespace) -> int:
    path = _ensure_collection(args)
    telemetry_key = _telemetry_key(required=True)
    assert telemetry_key is not None
    rows = load_collection(path, telemetry_key=telemetry_key)
    metrics = derive_collection_metrics(rows)
    blockers = acceptance_blockers(metrics)
    if blockers:
        raise RuntimeError("campaign collection is not acceptance-ready: " + ",".join(blockers))

    challenge_path = (ROOT / "reports/external_acceptance/release_challenge.json").resolve()
    challenge = verify_challenge(challenge_path, root=ROOT, max_age_hours=24, require_trust=True)
    if challenge.get("verified") is not True or challenge.get("trust_verified") is not True:
        raise RuntimeError("fresh release challenge/trust verification failed: " + ",".join(challenge.get("problems") or []))
    candidate, env_hash, topology_hash = _binding(args)
    if challenge.get("git_commit_sha") != candidate:
        raise RuntimeError("release challenge candidate SHA mismatch")
    header = rows[0]
    if header["candidate_sha"] != candidate or header["acceptance_environment_id_hash"] != env_hash or header["topology_hash"] != topology_hash:
        raise RuntimeError("campaign collection binding changed before seal")

    source_path = ROOT / "reports/external_acceptance/campaign/source/phase265_collection.json"
    source_sha, source_bytes = write_sealed_source(
        path,
        repository_root=ROOT,
        destination=source_path,
        telemetry_key=telemetry_key,
    )
    source_rel = source_path.relative_to(ROOT).as_posix()
    output_dir = ROOT / "reports/external_acceptance/campaign"
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = _iso(_utc_now())
    challenge_id = str(challenge.get("challenge_id") or "")
    challenge_sha = str(challenge.get("sha256") or "")
    written: dict[str, str] = {}
    for kind, classification in RECEIPT_CLASSIFICATIONS.items():
        payload = {
            "schema_version": "1.0",
            "classification": classification,
            "generated_at": generated_at,
            "git_commit_sha": candidate,
            "real_system": True,
            "executed": True,
            "release_challenge": {"challenge_id": challenge_id, "sha256": challenge_sha},
            "environment": {"acceptance_environment_id_hash": env_hash, "topology_hash": topology_hash},
            "source_artifacts": [
                {
                    "path": source_rel,
                    "sha256": source_sha,
                    "bytes": source_bytes,
                    "classification": "PHASE265_SEALED_REAL_CAMPAIGN_SOURCE",
                }
            ],
            "metrics": metrics[kind],
            "live_enabled": False,
            "production_ready": False,
        }
        destination = output_dir / RECEIPT_NAMES[kind]
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, destination)
        written[kind] = destination.relative_to(ROOT).as_posix()

    expected_environment = {"acceptance_environment_id_hash": env_hash, "topology_hash": topology_hash}
    verification: dict[str, Any] = {}
    for kind, relative in written.items():
        result = verify_campaign_evidence(
            ROOT / relative,
            kind=kind,
            root=ROOT,
            max_age_hours=24,
            strict_external=True,
            expected_environment=expected_environment,
        )
        verification[kind] = result
        if result.get("verified") is not True:
            raise RuntimeError(f"sealed {kind} receipt failed strict verification: {result.get('problems')}")
    print(
        json.dumps(
            {
                "classification": "PHASE265_FRESH_CHALLENGE_CAMPAIGN_SEAL",
                "candidate_sha": candidate,
                "release_challenge_id": challenge_id,
                "release_challenge_sha256": challenge_sha,
                "source_sha256": source_sha,
                "event_counts": collection_event_counts(rows),
                "receipts": written,
                "verification": verification,
                "live_enabled": False,
                "production_ready": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase265 attested campaign collector and fresh-challenge sealer")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--environment-id", required=True)
    parser.add_argument("--topology-hash", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    market = sub.add_parser(
        "collect-market-audit",
        help="Collect read-only Binance public-market telemetry; explicitly not live-shadow acceptance evidence",
    )
    market.add_argument("--symbol", default="BTCUSDT")
    market.add_argument("--count", type=int, default=5)
    market.add_argument("--interval-seconds", type=float, default=1.0)
    market.add_argument("--timeout-seconds", type=float, default=10.0)
    market.set_defaults(func=_collect_market_audit)

    kill = sub.add_parser("kill-switch-audit", help="Test collector halt behavior; explicitly not campaign acceptance")
    kill.add_argument("--symbol", default="BTCUSDT")
    kill.add_argument("--timeout-seconds", type=float, default=10.0)
    kill.set_defaults(func=_kill_switch_audit)

    ingest = sub.add_parser(
        "ingest-audit",
        help="Preserve externally captured JSONL for audit only; imported rows never contribute to acceptance metrics",
    )
    ingest.add_argument("--source", required=True)
    ingest.set_defaults(func=_ingest_audit)

    status = sub.add_parser("status", help="Report progress without claiming acceptance")
    status.set_defaults(func=_status)

    seal = sub.add_parser("seal", help="Seal only HMAC-attested protected-runtime evidence with a fresh trusted challenge")
    seal.set_defaults(func=_seal)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        return int(args.func(args))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc), "production_ready": False, "live_enabled": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
