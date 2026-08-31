from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.app.release.acceptance_challenge import verify_challenge
from backend.app.release.campaign_acceptance import CLASSIFICATIONS


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "UNAVAILABLE"


def templates() -> dict[str, dict]:
    challenge = verify_challenge(ROOT / "reports/external_acceptance/release_challenge.json", root=ROOT)
    binding = {"challenge_id": challenge.get("challenge_id"), "sha256": challenge.get("sha256")}
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    environment = {
        "acceptance_environment_id_hash": hashlib.sha256(env_id.encode()).hexdigest() if env_id else None,
        "topology_hash": topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else None,
    }
    common = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha(),
        "real_system": False,
        "executed": False,
        "release_challenge": binding,
        "environment": environment,
        "source_artifacts": [],
    }
    return {
        "private_stream.json": {**common, "classification": CLASSIFICATIONS["private-stream"], "metrics": {
            "credentialed_testnet": False, "auth_lifecycle_passed": False, "reconnect_passed": False,
            "rest_reconciliation_passed": False, "duplicate_event_idempotency_passed": False,
            "out_of_order_protection_passed": False, "secrets_redacted": False, "observed_events": 0}},
        "paper_campaign.json": {**common, "classification": CLASSIFICATIONS["paper"], "metrics": {
            "effective_sample_size": 0, "calendar_days": 0, "market_regimes": [], "long_examples": 0,
            "exit_examples": 0, "short_examples": 0, "active_market_type": "SPOT",
            "cost_stress_passed": False, "latency_stress_passed": False, "independent_oos_passed": False,
            "execution_divergence_bps": -1, "real_market_data": False}},
        "live_shadow.json": {**common, "classification": CLASSIFICATIONS["live-shadow"], "metrics": {
            "real_market_data": False, "calendar_days": 0, "observations": 0, "real_orders_submitted": 0,
            "exchange_submit_calls": 0, "kill_switch_tested": False, "reconciliation_passed": False}},
        "profitability.json": {**common, "classification": CLASSIFICATIONS["profitability"], "metrics": {
            "real_point_in_time_data": False, "independent_oos": False, "leakage_checks_passed": False,
            "cost_stress_passed": False, "survivorship_controls_passed": False, "effective_sample_size": 0,
            "net_expectancy_bps": 0, "bootstrap_ci_lower_bps": 0, "probabilistic_sharpe_ratio": 0}},
    }


def main() -> int:
    out = ROOT / "reports/external_acceptance/campaign"
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in templates().items():
        p = out / (name + ".template")
        p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
