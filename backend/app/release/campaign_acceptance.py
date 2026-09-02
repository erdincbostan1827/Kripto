from __future__ import annotations

import json
import math
import os
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, cast

from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.path_integrity import PathIntegrityError, strict_regular_file
from backend.app.release.paper_campaign import PaperCampaignEvidence, PaperCampaignPolicy

CLASSIFICATIONS = {
    "private-stream": "CREDENTIALED_PRIVATE_STREAM_ACCEPTANCE",
    "paper": "REAL_MARKET_PAPER_CAMPAIGN_ACCEPTANCE",
    "live-shadow": "LIVE_SHADOW_CAMPAIGN_ACCEPTANCE",
    "profitability": "REAL_PIT_PROFITABILITY_ACCEPTANCE",
}


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git_sha(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _finite_number(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError("boolean/null is not an acceptance metric number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("acceptance metric must be finite")
    return number


def _strict_int(value: Any) -> int:
    number = _finite_number(value)
    if not number.is_integer():
        raise ValueError("acceptance count metric must be an integer")
    return int(number)


def _numeric_metrics_are_valid(metrics: dict[str, Any], *, kind: str) -> bool:
    numeric_fields = {
        "private-stream": (("observed_events", "int"),),
        "paper": (
            ("effective_sample_size", "float"), ("calendar_days", "int"),
            ("long_examples", "int"), ("exit_examples", "int"),
            ("short_examples", "int"), ("execution_divergence_bps", "float"),
        ),
        "live-shadow": (
            ("calendar_days", "int"), ("observations", "int"),
            ("real_orders_submitted", "int"), ("exchange_submit_calls", "int"),
        ),
        "profitability": (
            ("effective_sample_size", "float"), ("net_expectancy_bps", "float"),
            ("bootstrap_ci_lower_bps", "float"), ("probabilistic_sharpe_ratio", "float"),
        ),
    }[kind]
    try:
        for field, metric_type in numeric_fields:
            value = metrics.get(field)
            _strict_int(value) if metric_type == "int" else _finite_number(value)
    except (TypeError, ValueError, OverflowError):
        return False
    return True


def _environment_binding() -> dict[str, Any]:
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    return {
        "acceptance_environment_id_hash": sha256(env_id.encode()).hexdigest() if env_id else None,
        "topology_hash": topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else None,
    }


def _common_problems(payload: dict[str, Any], *, kind: str, root: Path, max_age_hours: int, strict_external: bool = False, expected_environment: dict[str, Any] | None = None) -> list[str]:
    problems: list[str] = []
    if payload.get("schema_version") != "1.0":
        problems.append("CAMPAIGN_SCHEMA_UNSUPPORTED")
    if payload.get("classification") != CLASSIFICATIONS[kind]:
        problems.append("INVALID_CLASSIFICATION")
    if payload.get("real_system") is not True or payload.get("executed") is not True:
        problems.append("REAL_EXECUTION_NOT_CONFIRMED")
    current_git = _git_sha(root)
    if current_git != "UNAVAILABLE" and payload.get("git_commit_sha") != current_git:
        problems.append("GIT_COMMIT_MISMATCH")
    challenge = verify_challenge(root / "reports/external_acceptance/release_challenge.json", root=root, require_trust=True if strict_external else None)
    raw_bound = payload.get("release_challenge")
    bound: dict[str, Any] = raw_bound if isinstance(raw_bound, dict) else {}
    if not challenge.get("verified"):
        problems.append("RELEASE_CHALLENGE_NOT_VERIFIED")
    elif bound.get("challenge_id") != challenge.get("challenge_id") or bound.get("sha256") != challenge.get("sha256"):
        problems.append("RELEASE_CHALLENGE_BINDING_MISMATCH")
    if strict_external:
        expected_binding = expected_environment if isinstance(expected_environment, dict) else _environment_binding()
        expected_env = expected_binding.get("acceptance_environment_id_hash")
        expected_topology = expected_binding.get("topology_hash")
        if not isinstance(expected_env, str) or len(expected_env) != 64:
            problems.append("ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING")
        if not isinstance(expected_topology, str) or len(expected_topology) != 64:
            problems.append("ACCEPTANCE_TOPOLOGY_HASH_MISSING")
        raw_environment = payload.get("environment")
        environment: dict[str, Any] = raw_environment if isinstance(raw_environment, dict) else {}
        if isinstance(expected_env, str) and environment.get("acceptance_environment_id_hash") != expected_env:
            problems.append("ACCEPTANCE_ENVIRONMENT_ID_MISMATCH")
        if isinstance(expected_topology, str) and environment.get("topology_hash") != expected_topology:
            problems.append("ACCEPTANCE_TOPOLOGY_MISMATCH")
    generated = _time(payload.get("generated_at"))
    if generated is None:
        problems.append("INVALID_GENERATED_AT")
    else:
        age = (datetime.now(timezone.utc) - generated.astimezone(timezone.utc)).total_seconds() / 3600
        if age < -1:
            problems.append("GENERATED_AT_IN_FUTURE")
        elif age > max_age_hours:
            problems.append("EVIDENCE_RECEIPT_STALE")
    artifacts = payload.get("source_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        problems.append("SOURCE_ARTIFACTS_MISSING")
    else:
        for idx, row in enumerate(artifacts):
            if not isinstance(row, dict):
                problems.append(f"SOURCE_ARTIFACT_INVALID:{idx}")
                continue
            rel, expected_sha = row.get("path"), row.get("sha256")
            try:
                if strict_external:
                    p = strict_regular_file(root, str(rel))
                else:
                    p = (root / str(rel)).resolve()
                    p.relative_to(root.resolve())
            except (PathIntegrityError, ValueError):
                problems.append(f"SOURCE_ARTIFACT_PATH_INTEGRITY_INVALID:{idx}" if strict_external else f"SOURCE_ARTIFACT_OUTSIDE_ROOT:{idx}")
                continue
            if not p.is_file():
                problems.append(f"SOURCE_ARTIFACT_MISSING:{idx}")
            elif not isinstance(expected_sha, str) or _sha(p) != expected_sha:
                problems.append(f"SOURCE_ARTIFACT_HASH_MISMATCH:{idx}")
    return problems


def verify_campaign_evidence(path: Path, *, kind: str, root: Path, max_age_hours: int = 168, strict_external: bool = False, expected_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    if kind not in CLASSIFICATIONS:
        raise ValueError(f"unsupported campaign evidence kind: {kind}")
    try:
        loaded: Any = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"verified": False, "problems": [f"INVALID_JSON:{type(exc).__name__}"], "kind": kind}
    if not isinstance(loaded, dict):
        return {"verified": False, "problems": ["INVALID_JSON_ROOT"], "kind": kind}
    payload = cast(dict[str, Any], loaded)
    problems = _common_problems(payload, kind=kind, root=root, max_age_hours=max_age_hours, strict_external=strict_external, expected_environment=expected_environment)
    raw_metrics = payload.get("metrics")
    metrics: dict[str, Any] = raw_metrics if isinstance(raw_metrics, dict) else {}
    numeric_valid = _numeric_metrics_are_valid(metrics, kind=kind)
    if not numeric_valid:
        problems.append("NON_FINITE_OR_INVALID_NUMERIC_METRIC")

    if kind == "private-stream":
        private_required_true = (
            "credentialed_testnet", "auth_lifecycle_passed", "reconnect_passed",
            "rest_reconciliation_passed", "duplicate_event_idempotency_passed",
            "out_of_order_protection_passed", "secrets_redacted",
        )
        if any(metrics.get(k) is not True for k in private_required_true):
            problems.append("PRIVATE_STREAM_REQUIRED_CHECK_FAILED")
        if numeric_valid and _strict_int(metrics.get("observed_events")) <= 0:
            problems.append("PRIVATE_STREAM_NO_EVENTS")
    elif kind == "paper":
        try:
            evidence = PaperCampaignEvidence(
                effective_sample_size=_finite_number(metrics.get("effective_sample_size")),
                calendar_days=_strict_int(metrics.get("calendar_days")),
                market_regimes=tuple(metrics.get("market_regimes") or ()),
                long_examples=_strict_int(metrics.get("long_examples")),
                exit_examples=_strict_int(metrics.get("exit_examples")),
                short_examples=_strict_int(metrics.get("short_examples")),
                active_market_type=str(metrics.get("active_market_type", "")),
                cost_stress_passed=metrics.get("cost_stress_passed") is True,
                latency_stress_passed=metrics.get("latency_stress_passed") is True,
                independent_oos_passed=metrics.get("independent_oos_passed") is True,
                execution_divergence_bps=_finite_number(metrics.get("execution_divergence_bps")),
                executed=payload.get("executed") is True,
                real_market_data=metrics.get("real_market_data") is True,
            )
            problems.extend(evidence.blockers(PaperCampaignPolicy()))
        except Exception as exc:
            problems.append(f"PAPER_METRICS_INVALID:{type(exc).__name__}")
    elif kind == "live-shadow":
        if metrics.get("real_market_data") is not True:
            problems.append("LIVE_SHADOW_REAL_MARKET_DATA_MISSING")
        if numeric_valid and (_strict_int(metrics.get("calendar_days")) < 7 or _strict_int(metrics.get("observations")) < 100):
            problems.append("LIVE_SHADOW_SAMPLE_INSUFFICIENT")
        if numeric_valid and (_strict_int(metrics.get("real_orders_submitted")) != 0 or _strict_int(metrics.get("exchange_submit_calls")) != 0):
            problems.append("LIVE_SHADOW_UNINTENDED_ORDER_SUBMISSION")
        if metrics.get("kill_switch_tested") is not True or metrics.get("reconciliation_passed") is not True:
            problems.append("LIVE_SHADOW_SAFETY_CHECK_FAILED")
    elif kind == "profitability":
        profitability_required_true = ("real_point_in_time_data", "independent_oos", "leakage_checks_passed", "cost_stress_passed", "survivorship_controls_passed")
        if any(metrics.get(k) is not True for k in profitability_required_true):
            problems.append("PIT_PROFITABILITY_INTEGRITY_CHECK_FAILED")
        if numeric_valid and _finite_number(metrics.get("effective_sample_size")) < 100:
            problems.append("PIT_PROFITABILITY_SAMPLE_TOO_SMALL")
        if numeric_valid and (_finite_number(metrics.get("net_expectancy_bps")) <= 0 or _finite_number(metrics.get("bootstrap_ci_lower_bps")) <= 0):
            problems.append("PIT_PROFITABILITY_NOT_POSITIVE_AFTER_COSTS")
        if numeric_valid and _finite_number(metrics.get("probabilistic_sharpe_ratio")) < 0.95:
            problems.append("PIT_PROFITABILITY_STATISTICAL_CONFIDENCE_LOW")

    return {"verified": not problems, "problems": problems, "kind": kind, "sha256": _sha(path), "metrics": metrics}
