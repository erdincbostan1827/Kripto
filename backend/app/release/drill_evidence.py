from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, cast

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.path_integrity import PathIntegrityError, strict_regular_file


class DrillEvidenceError(ValueError):
    """Raised when real external drill evidence fails verification."""


SCHEMA_VERSION = "2.0"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _fresh(value: str, max_age_hours: int) -> bool:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise DrillEvidenceError("invalid observed_at timestamp") from exc
    if dt.tzinfo is None:
        raise DrillEvidenceError("observed_at must be timezone-aware")
    age = datetime.now(timezone.utc) - dt.astimezone(timezone.utc)
    return 0 <= age.total_seconds() <= max_age_hours * 3600


def _verify_artifacts(root: Path, artifacts: Iterable[dict]) -> None:
    rows = list(artifacts)
    if not rows:
        raise DrillEvidenceError("at least one hashed drill artifact is required")
    for row in rows:
        rel = row.get("path")
        expected = row.get("sha256")
        if not isinstance(rel, str) or not rel or not isinstance(expected, str) or len(expected) != 64:
            raise DrillEvidenceError("artifact path and sha256 are required")
        try:
            path = strict_regular_file(root, rel)
        except PathIntegrityError as exc:
            raise DrillEvidenceError(f"artifact path integrity invalid: {rel}") from exc
        if _sha256(path) != expected.lower():
            raise DrillEvidenceError(f"artifact hash mismatch: {rel}")


def _environment_binding() -> dict[str, str | None]:
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    return {
        "acceptance_environment_id_hash": hashlib.sha256(env_id.encode()).hexdigest() if env_id else None,
        "topology_hash": topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else None,
    }


def _verify_release_binding(
    data: dict[str, Any], *, root: Path, expected_environment: dict[str, Any] | None
) -> None:
    if data.get("schema_version") != SCHEMA_VERSION:
        raise DrillEvidenceError(f"drill evidence schema_version={SCHEMA_VERSION} is required")

    challenge_path = root / "reports" / "external_acceptance" / "release_challenge.json"
    challenge = verify_challenge(challenge_path, root=root, require_trust=True)
    if not challenge.get("verified"):
        raise DrillEvidenceError("release challenge is not verified")
    raw_bound = data.get("release_challenge")
    bound: dict[str, Any] = raw_bound if isinstance(raw_bound, dict) else {}
    if bound.get("challenge_id") != challenge.get("challenge_id") or bound.get("sha256") != challenge.get("sha256"):
        raise DrillEvidenceError("drill evidence release challenge binding mismatch")

    expected = expected_environment if isinstance(expected_environment, dict) else _environment_binding()
    expected_env = expected.get("acceptance_environment_id_hash")
    expected_topology = expected.get("topology_hash")
    if not isinstance(expected_env, str) or len(expected_env) != 64:
        raise DrillEvidenceError("acceptance environment identity is required")
    if not isinstance(expected_topology, str) or len(expected_topology) != 64:
        raise DrillEvidenceError("acceptance topology hash is required")
    raw_environment = data.get("environment")
    environment: dict[str, Any] = raw_environment if isinstance(raw_environment, dict) else {}
    if environment.get("acceptance_environment_id_hash") != expected_env:
        raise DrillEvidenceError("drill evidence acceptance environment mismatch")
    if environment.get("topology_hash") != expected_topology:
        raise DrillEvidenceError("drill evidence acceptance topology mismatch")


def _load_and_verify_common(
    path: Path, *, root: Path, kind: str, max_age_hours: int = 24,
    expected_environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        loaded: Any = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DrillEvidenceError("evidence must be valid JSON") from exc
    if not isinstance(loaded, dict):
        raise DrillEvidenceError("evidence JSON root must be an object")
    data = cast(dict[str, Any], loaded)
    if data.get("classification") != "REAL_EXTERNAL_ACCEPTANCE_DRILL":
        raise DrillEvidenceError("invalid drill classification")
    if data.get("drill_kind") != kind:
        raise DrillEvidenceError(f"expected drill_kind={kind}")
    if data.get("real_system") is not True:
        raise DrillEvidenceError("real_system=true is required")
    if not _fresh(str(data.get("observed_at", "")), max_age_hours):
        raise DrillEvidenceError("drill evidence is stale or future-dated")
    actual_sha = _git_sha(root)
    if data.get("git_commit_sha") != actual_sha:
        raise DrillEvidenceError("drill evidence git commit does not match source")
    _verify_release_binding(data, root=root, expected_environment=expected_environment)
    _verify_artifacts(root, data.get("artifacts") or [])
    return data


RESTORE_REQUIRED = (
    "isolated_environment",
    "backup_or_pitr_restored",
    "schema_validated",
    "referential_integrity_validated",
    "checksum_validated",
    "read_only_smoke_passed",
    "result_reported",
)

HA_REQUIRED = (
    "active_process_kill_passed",
    "stale_leader_fencing_passed",
    "private_stream_reconciliation_passed",
    "host_loss_simulation_passed",
    "db_failover_passed",
    "network_partition_passed",
)

WORM_REQUIRED = (
    "append_only_verified",
    "retention_lock_verified",
    "delete_before_retention_denied",
    "overwrite_denied",
    "readback_verified",
)


def _require_true(data: dict, keys: Iterable[str]) -> None:
    missing = [key for key in keys if data.get(key) is not True]
    if missing:
        raise DrillEvidenceError("incomplete drill evidence: " + ",".join(missing))


def verify_restore_evidence(path: Path, *, root: Path, max_age_hours: int = 24, expected_environment: dict[str, Any] | None = None) -> dict:
    data = _load_and_verify_common(path, root=root, kind="PITR_RESTORE", max_age_hours=max_age_hours, expected_environment=expected_environment)
    _require_true(data, RESTORE_REQUIRED)
    return data


def verify_ha_evidence(path: Path, *, root: Path, max_age_hours: int = 24, expected_environment: dict[str, Any] | None = None) -> dict:
    data = _load_and_verify_common(path, root=root, kind="HA_FAILOVER", max_age_hours=max_age_hours, expected_environment=expected_environment)
    _require_true(data, HA_REQUIRED)
    if data.get("redis_ha_applicable") is True and data.get("redis_failover_passed") is not True:
        raise DrillEvidenceError("redis failover evidence required for this HA profile")
    return data


def verify_worm_evidence(path: Path, *, root: Path, max_age_hours: int = 24, expected_environment: dict[str, Any] | None = None) -> dict:
    data = _load_and_verify_common(path, root=root, kind="WORM_STORAGE", max_age_hours=max_age_hours, expected_environment=expected_environment)
    _require_true(data, WORM_REQUIRED)
    if not data.get("provider") or not data.get("retention_policy_reference"):
        raise DrillEvidenceError("WORM provider and retention policy reference are required")
    return data
