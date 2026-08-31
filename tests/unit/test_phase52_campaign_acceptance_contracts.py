import json
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from backend.app.release.acceptance_challenge import create_challenge
from backend.app.release.campaign_acceptance import CLASSIFICATIONS, verify_campaign_evidence
from scripts.external_acceptance_runner import build_plan
from scripts.generate_release_manifest import acceptance_statuses
from scripts.verify_external_acceptance import GROUP_KEYS




def _git(root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase52@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase52"], cwd=root, check=True)
    (root / "seed").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _sha(p: Path) -> str:
    return sha256(p.read_bytes()).hexdigest()


def _base(tmp_path: Path, kind: str, metrics: dict) -> Path:
    git_sha = _git(tmp_path)
    reports = tmp_path / "reports/external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    challenge = create_challenge(tmp_path, reports / "release_challenge.json")
    raw = reports / "campaign-source.ndjson"
    raw.write_text('{"event":"real-evidence"}\n', encoding="utf-8")
    payload = {
        "schema_version": "1.0",
        "classification": CLASSIFICATIONS[kind],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "real_system": True,
        "executed": True,
        "release_challenge": {"challenge_id": challenge["challenge_id"], "sha256": challenge["sha256"]},
        "source_artifacts": [{"path": str(raw.relative_to(tmp_path)), "sha256": _sha(raw)}],
        "metrics": metrics,
    }
    p = reports / f"{kind}.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_private_stream_contract_requires_real_credentialed_lifecycle(tmp_path):
    metrics = {k: True for k in (
        "credentialed_testnet", "auth_lifecycle_passed", "reconnect_passed",
        "rest_reconciliation_passed", "duplicate_event_idempotency_passed",
        "out_of_order_protection_passed", "secrets_redacted",
    )}
    metrics["observed_events"] = 25
    p = _base(tmp_path, "private-stream", metrics)
    assert verify_campaign_evidence(p, kind="private-stream", root=tmp_path)["verified"]
    doc = json.loads(p.read_text()); doc["metrics"]["secrets_redacted"] = False; p.write_text(json.dumps(doc))
    assert not verify_campaign_evidence(p, kind="private-stream", root=tmp_path)["verified"]


def test_paper_contract_enforces_existing_promotion_policy(tmp_path):
    metrics = {
        "effective_sample_size": 120, "calendar_days": 31, "market_regimes": ["trend", "range"],
        "long_examples": 30, "exit_examples": 30, "short_examples": 0, "active_market_type": "SPOT",
        "cost_stress_passed": True, "latency_stress_passed": True, "independent_oos_passed": True,
        "execution_divergence_bps": 12.5, "real_market_data": True,
    }
    p = _base(tmp_path, "paper", metrics)
    assert verify_campaign_evidence(p, kind="paper", root=tmp_path)["verified"]
    doc = json.loads(p.read_text()); doc["metrics"]["calendar_days"] = 2; p.write_text(json.dumps(doc))
    assert "CALENDAR_DURATION_TOO_SHORT" in verify_campaign_evidence(p, kind="paper", root=tmp_path)["problems"]


def test_live_shadow_contract_forbids_any_submit(tmp_path):
    metrics = {"real_market_data": True, "calendar_days": 7, "observations": 150,
               "real_orders_submitted": 0, "exchange_submit_calls": 0,
               "kill_switch_tested": True, "reconciliation_passed": True}
    p = _base(tmp_path, "live-shadow", metrics)
    assert verify_campaign_evidence(p, kind="live-shadow", root=tmp_path)["verified"]
    doc = json.loads(p.read_text()); doc["metrics"]["exchange_submit_calls"] = 1; p.write_text(json.dumps(doc))
    assert "LIVE_SHADOW_UNINTENDED_ORDER_SUBMISSION" in verify_campaign_evidence(p, kind="live-shadow", root=tmp_path)["problems"]


def test_profitability_contract_requires_positive_cost_adjusted_confidence(tmp_path):
    metrics = {"real_point_in_time_data": True, "independent_oos": True, "leakage_checks_passed": True,
               "cost_stress_passed": True, "survivorship_controls_passed": True, "effective_sample_size": 180,
               "net_expectancy_bps": 6.0, "bootstrap_ci_lower_bps": 1.2, "probabilistic_sharpe_ratio": 0.97}
    p = _base(tmp_path, "profitability", metrics)
    assert verify_campaign_evidence(p, kind="profitability", root=tmp_path)["verified"]
    doc = json.loads(p.read_text()); doc["metrics"]["bootstrap_ci_lower_bps"] = -0.1; p.write_text(json.dumps(doc))
    assert "PIT_PROFITABILITY_NOT_POSITIVE_AFTER_COSTS" in verify_campaign_evidence(p, kind="profitability", root=tmp_path)["problems"]


def test_campaign_profile_and_release_mapping_are_complete():
    keys = {k for k, _, _ in build_plan("campaigns")}
    assert keys == {"private_stream_evidence", "paper_campaign_evidence", "live_shadow_evidence", "profitability_evidence"}
    for g in ("private_stream", "paper_campaign", "live_shadow", "profitability"):
        assert g in GROUP_KEYS
    statuses = acceptance_statuses({"groups": {g: "PASS" for g in ("private_stream", "paper_campaign", "live_shadow", "profitability")}})
    assert statuses["credentialed_private_stream"] == "PASS"
    assert statuses["real_market_paper_campaign"] == "PASS"
    assert statuses["live_shadow_campaign"] == "PASS"
    assert statuses["real_pit_profitability_evidence"] == "PASS"
