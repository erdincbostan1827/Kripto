from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FIELDS = {
    "pitr": ("PITR_RESTORE", (
        "isolated_environment", "backup_or_pitr_restored", "schema_validated",
        "referential_integrity_validated", "checksum_validated", "read_only_smoke_passed", "result_reported",
    )),
    "ha": ("HA_FAILOVER", (
        "active_process_kill_passed", "stale_leader_fencing_passed", "private_stream_reconciliation_passed",
        "host_loss_simulation_passed", "db_failover_passed", "network_partition_passed",
    )),
    "worm": ("WORM_STORAGE", (
        "append_only_verified", "retention_lock_verified", "delete_before_retention_denied", "overwrite_denied", "readback_verified",
    )),
}


def template(kind: str) -> dict:
    drill_kind, fields = FIELDS[kind]
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    challenge_path = ROOT / "reports" / "external_acceptance" / "release_challenge.json"
    try:
        challenge_raw = json.loads(challenge_path.read_text(encoding="utf-8"))
        challenge = {"challenge_id": challenge_raw.get("challenge_id"), "sha256": hashlib.sha256(challenge_path.read_bytes()).hexdigest()}
    except Exception:
        challenge = {"challenge_id": "REPLACE_WITH_RELEASE_CHALLENGE_ID", "sha256": "REPLACE_WITH_RELEASE_CHALLENGE_SHA256"}
    env_id = os.getenv("ACCEPTANCE_ENVIRONMENT_ID", "")
    topology = os.getenv("ACCEPTANCE_TOPOLOGY_HASH", "").lower()
    payload = {
        "schema_version": "2.0",
        "classification": "REAL_EXTERNAL_ACCEPTANCE_DRILL",
        "drill_kind": drill_kind,
        "real_system": False,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "git_commit_sha": sha,
        "release_challenge": challenge,
        "environment": {
            "acceptance_environment_id_hash": hashlib.sha256(env_id.encode()).hexdigest() if env_id else "REPLACE_WITH_ACCEPTANCE_ENVIRONMENT_ID_HASH",
            "topology_hash": topology if len(topology) == 64 and all(c in "0123456789abcdef" for c in topology) else "REPLACE_WITH_TOPOLOGY_HASH",
        },
        "artifacts": [{"path": "REPLACE_WITH_REAL_ARTIFACT", "sha256": "REPLACE_WITH_REAL_SHA256"}],
    }
    payload.update({field: False for field in fields})
    if kind == "ha":
        payload.update(redis_ha_applicable=False, redis_failover_passed=False)
    if kind == "worm":
        payload.update(provider="REPLACE_WITH_PROVIDER", retention_policy_reference="REPLACE_WITH_POLICY_REFERENCE")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fail-closed external drill evidence template")
    parser.add_argument("kind", choices=tuple(FIELDS))
    parser.add_argument("--output")
    args = parser.parse_args()
    out = Path(args.output) if args.output else ROOT / "reports" / "external_acceptance" / f"{args.kind}_evidence.template.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(template(args.kind), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
