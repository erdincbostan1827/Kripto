from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/external_acceptance/restart_evidence.template.json"


def main() -> int:
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    challenge_path = ROOT / "reports/external_acceptance/release_challenge.json"
    challenge = {}
    if challenge_path.is_file():
        try:
            raw = json.loads(challenge_path.read_text(encoding="utf-8"))
            challenge = {
                "challenge_id": raw.get("challenge_id"),
                "sha256": sha256(challenge_path.read_bytes()).hexdigest(),
            }
        except Exception:
            challenge = {}
    metrics = {
        "redis_restart_executed": False,
        "postgres_restart_executed": False,
        "state_persisted_before_restart": False,
        "state_persisted_after_restart": False,
        "services_reconnected": False,
        "application_reconciliation_passed": False,
        "no_duplicate_orders": False,
        "risk_fail_closed_during_outage": False,
        "healthy_recovery": False,
        "reconciled_records": 0,
        "duplicate_orders_detected": 0,
    }
    payload = {
        "schema_version": "1.0",
        "classification": "REAL_RUNTIME_RESTART_ACCEPTANCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": git_sha,
        "real_system": False,
        "executed": False,
        "release_challenge": challenge,
        "environment": {
            "acceptance_environment_id_hash": sha256(env_id.encode()).hexdigest() if env_id else None,
            "topology_hash": topology if len(topology) == 64 else None,
        },
        "source_artifacts": [{"path": "REPLACE_WITH_REAL_RESTART_LOG", "sha256": "REPLACE_WITH_REAL_SHA256"}],
        "metrics": metrics,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
