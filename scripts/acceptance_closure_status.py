from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.external.execution_map import COMMANDS, classify
from scripts.external_acceptance_preflight import evaluate as evaluate_preflight

MATRIX = ROOT / "REQUIREMENTS_TRACEABILITY_MATRIX.yaml"
OUT = ROOT / "reports" / "ACCEPTANCE_CLOSURE_STATUS.json"

# Profiles intentionally distinguish prerequisite readiness from acceptance
# evidence. A READY prerequisite never promotes a requirement to PASS.
PROFILE_PREREQUISITES: dict[str, tuple[str, ...]] = {
    "dependency-locks": ("group:dependency_locks",),
    "runtime": ("group:container_runtime",),
    "restart-drills": ("group:container_runtime", "group:restart_contract"),
    "supply-chain": ("external:trusted_ci_supply_chain_evidence",),
    "pitr": ("group:pitr_contract", "group:environment_identity", "group:challenge_trust_contract"),
    "ha": ("group:ha_contract", "group:environment_identity", "group:challenge_trust_contract"),
    "worm": ("group:worm_contract", "group:environment_identity", "group:challenge_trust_contract"),
    "testnet-campaigns": ("group:credentialed_testnet", "group:environment_identity", "group:challenge_trust_contract"),
    "provenance": ("group:provenance_sign_verify_contract", "group:ledger_checkpoint_contract", "external:trusted_ci_provenance"),
    "frontend-browser": ("group:dependency_locks", "external:real_browser_matrix"),
    "desktop-build": ("group:dependency_locks", "tool:cargo", "external:desktop_build_or_signing_runner"),
    "signing": ("group:signing_tooling", "external:trusted_signing_identity"),
}


def _requirement_rows() -> list[dict]:
    doc = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    return [row for row in doc.get("requirements", []) if row.get("status") == "NOT_TESTED"]


def _resolve_prerequisite(key: str, preflight: dict) -> dict:
    if key.startswith("group:"):
        name = key.split(":", 1)[1]
        ready = bool(preflight.get("groups", {}).get(name, False))
        return {"key": key, "ready": ready, "detail": "PREFLIGHT_READY" if ready else "PREFLIGHT_BLOCKED"}
    if key.startswith("tool:"):
        name = key.split(":", 1)[1]
        path = shutil.which(name)
        return {"key": key, "ready": bool(path), "detail": path or f"TOOL_UNAVAILABLE:{name}"}
    if key.startswith("external:"):
        return {"key": key, "ready": False, "detail": "REAL_EXTERNAL_EVIDENCE_REQUIRED"}
    raise ValueError(f"UNKNOWN_PREREQUISITE:{key}")


def build() -> dict:
    rows = _requirement_rows()
    preflight = evaluate_preflight()
    requirements: list[dict] = []
    profile_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()

    for row in rows:
        profile = classify(int(row["section"]), str(row.get("description", "")))
        profile_counts[profile] += 1
        prerequisites = [_resolve_prerequisite(key, preflight) for key in PROFILE_PREREQUISITES[profile]]
        blocking = [item for item in prerequisites if not item["ready"]]
        for item in blocking:
            reason_counts[item["key"]] += 1
        requirements.append(
            {
                "requirement_id": row["requirement_id"],
                "priority": row["priority"],
                "section": int(row["section"]),
                "description": row.get("description", ""),
                "profile": profile,
                "command": COMMANDS[profile],
                "prerequisites": prerequisites,
                "blocked": bool(blocking),
                "blocking_reasons": [item["key"] for item in blocking],
                "classification": "CLOSURE_PLAN_NOT_ACCEPTANCE_EVIDENCE",
            }
        )

    p0 = [row for row in requirements if row["priority"] == "P0"]
    blocked = [row for row in requirements if row["blocked"]]
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "ACCEPTANCE_CLOSURE_STATUS_NOT_ACCEPTANCE_EVIDENCE",
        "truth_policy": (
            "This report explains unresolved acceptance work and prerequisite blockers only. "
            "It cannot promote requirements to PASS; PASS requires the repository's checksum-bound trusted acceptance evidence path."
        ),
        "open_requirement_count": len(requirements),
        "p0_open_requirement_count": len(p0),
        "blocked_requirement_count": len(blocked),
        "unmapped_requirement_count": 0,
        "profile_counts": dict(sorted(profile_counts.items())),
        "blocking_reason_counts": dict(sorted(reason_counts.items())),
        "preflight_classification": preflight.get("classification"),
        "preflight_all_external_prerequisites_ready": bool(preflight.get("all_external_prerequisites_ready")),
        "requirements": requirements,
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["unmapped_requirement_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
