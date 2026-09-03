from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.release.acceptance_challenge import verify_challenge
from app.release.path_integrity import PathIntegrityError, strict_regular_file

CLASSIFICATION = "REAL_RUNTIME_RESTART_ACCEPTANCE"
SCHEMA_VERSION = "1.0"
REQUIRED_TRUE = (
    "redis_restart_executed",
    "postgres_restart_executed",
    "state_persisted_before_restart",
    "state_persisted_after_restart",
    "services_reconnected",
    "application_reconciliation_passed",
    "no_duplicate_orders",
    "risk_fail_closed_during_outage",
    "healthy_recovery",
)


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def _env_binding() -> tuple[str | None, str | None]:
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "")
    env_hash = sha256(env_id.encode()).hexdigest() if env_id else None
    topology = topology.lower()
    topology_hash = topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else None
    return env_hash, topology_hash


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def verify_restart_evidence(path: Path, *, root: Path, max_age_hours: int = 24, expected_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"INVALID_JSON:{type(exc).__name__}"]}

    problems: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        problems.append("SCHEMA_VERSION_UNSUPPORTED")
    if payload.get("classification") != CLASSIFICATION:
        problems.append("INVALID_CLASSIFICATION")
    if payload.get("real_system") is not True or payload.get("executed") is not True:
        problems.append("REAL_EXECUTION_NOT_CONFIRMED")

    current_git = _git_sha(root)
    if current_git != "UNAVAILABLE" and payload.get("git_commit_sha") != current_git:
        problems.append("GIT_COMMIT_MISMATCH")

    challenge = verify_challenge(root / "reports/external_acceptance/release_challenge.json", root=root, require_trust=True)
    bound = payload.get("release_challenge") if isinstance(payload.get("release_challenge"), dict) else {}
    if not challenge.get("verified"):
        problems.append("RELEASE_CHALLENGE_NOT_VERIFIED")
    elif bound.get("challenge_id") != challenge.get("challenge_id") or bound.get("sha256") != challenge.get("sha256"):
        problems.append("RELEASE_CHALLENGE_BINDING_MISMATCH")

    environment = payload.get("environment") if isinstance(payload.get("environment"), dict) else {}
    if expected_environment is not None:
        expected_env_hash = expected_environment.get("acceptance_environment_id_hash")
        expected_topology = expected_environment.get("topology_hash")
    else:
        expected_env_hash, expected_topology = _env_binding()
    if not expected_env_hash or not expected_topology:
        problems.append("ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING")
    else:
        if environment.get("acceptance_environment_id_hash") != expected_env_hash:
            problems.append("ACCEPTANCE_ENVIRONMENT_ID_MISMATCH")
        if environment.get("topology_hash") != expected_topology:
            problems.append("ACCEPTANCE_TOPOLOGY_MISMATCH")

    generated = _time(payload.get("generated_at"))
    if generated is None:
        problems.append("INVALID_GENERATED_AT")
    else:
        age = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1:
            problems.append("GENERATED_AT_IN_FUTURE")
        elif age > max_age_hours:
            problems.append("EVIDENCE_STALE")

    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    missing = [key for key in REQUIRED_TRUE if metrics.get(key) is not True]
    if missing:
        problems.append("RESTART_REQUIRED_CHECK_FAILED:" + ",".join(missing))
    if int(metrics.get("reconciled_records", 0) or 0) < 1:
        problems.append("RECONCILIATION_SAMPLE_MISSING")
    if int(metrics.get("duplicate_orders_detected", -1) or 0) != 0:
        problems.append("DUPLICATE_ORDERS_DETECTED")

    artifacts = payload.get("source_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        problems.append("SOURCE_ARTIFACTS_MISSING")
    else:
        for idx, row in enumerate(artifacts):
            if not isinstance(row, dict):
                problems.append(f"SOURCE_ARTIFACT_INVALID:{idx}")
                continue
            rel, expected = row.get("path"), row.get("sha256")
            try:
                source = strict_regular_file(root, str(rel))
            except PathIntegrityError:
                problems.append(f"SOURCE_ARTIFACT_PATH_INTEGRITY_INVALID:{idx}")
                continue
            if not isinstance(expected, str) or _sha(source) != expected.lower():
                problems.append(f"SOURCE_ARTIFACT_HASH_MISMATCH:{idx}")

    return {
        "verified": not problems,
        "problems": problems,
        "sha256": _sha(path),
        "metrics": metrics,
    }
