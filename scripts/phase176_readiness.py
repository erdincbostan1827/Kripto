from __future__ import annotations

import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.acceptance_closure_status import build as build_closure
from scripts.external.toolchain_readiness import evaluate as evaluate_toolchain
from scripts.external_acceptance_preflight import evaluate as evaluate_preflight

OUT = ROOT / "reports" / "PHASE176_READINESS.json"

_REASON_CLASS = {
    "group:dependency_locks": "REGISTRY_OR_LOCK_RESOLUTION",
    "group:container_runtime": "HOST_RUNTIME_CAPABILITY",
    "group:credentialed_testnet": "EXTERNAL_CREDENTIALS",
    "group:environment_identity": "EXTERNAL_ENVIRONMENT_IDENTITY",
    "group:challenge_trust_contract": "TRUST_CONTRACT",
    "group:pitr_contract": "EXTERNAL_RECOVERY_DRILL_CONTRACT",
    "group:ha_contract": "EXTERNAL_HA_DRILL_CONTRACT",
    "group:worm_contract": "EXTERNAL_IMMUTABLE_STORAGE_CONTRACT",
    "group:restart_contract": "EXTERNAL_RESTART_DRILL_CONTRACT",
    "group:signing_tooling": "TRUSTED_SIGNING_CONTRACT",
    "group:provenance_sign_verify_contract": "TRUSTED_SIGNING_CONTRACT",
    "group:ledger_checkpoint_contract": "TRUSTED_LEDGER_CONTRACT",
    "external:trusted_ci_supply_chain_evidence": "TRUSTED_CI",
    "external:trusted_ci_provenance": "TRUSTED_CI",
    "external:real_browser_matrix": "REAL_BROWSER_ENVIRONMENT",
    "external:desktop_build_or_signing_runner": "DESKTOP_BUILD_ENVIRONMENT",
    "external:trusted_signing_identity": "TRUSTED_SIGNING_IDENTITY",
    "tool:cargo": "HOST_TOOLING",
}

_REMEDIATION = {
    "REGISTRY_OR_LOCK_RESOLUTION": "python scripts/bootstrap_dependency_locks.py && python scripts/verify_source_locks.py",
    "HOST_RUNTIME_CAPABILITY": "Provide Docker on the isolated acceptance host, then run the mapped runtime profile.",
    "EXTERNAL_CREDENTIALS": "Provide isolated Binance testnet credentials through environment variables; never copy values into evidence.",
    "EXTERNAL_ENVIRONMENT_IDENTITY": "Set ACCEPTANCE_ENVIRONMENT_ID and a 64-hex ACCEPTANCE_TOPOLOGY_HASH on the real acceptance host.",
    "TRUST_CONTRACT": "Generate and verify a current release challenge using the configured external trust verifier.",
    "EXTERNAL_RECOVERY_DRILL_CONTRACT": "Configure PITR_DRILL_COMMAND and PITR_EVIDENCE_JSON on the real recovery environment.",
    "EXTERNAL_HA_DRILL_CONTRACT": "Configure HA_DRILL_COMMAND and HA_EVIDENCE_JSON on the real HA environment.",
    "EXTERNAL_IMMUTABLE_STORAGE_CONTRACT": "Configure WORM acceptance command/evidence against real immutable storage.",
    "EXTERNAL_RESTART_DRILL_CONTRACT": "Configure restart drill command/evidence against real Redis/PostgreSQL services.",
    "TRUSTED_SIGNING_CONTRACT": "Provide the trusted provenance/signing verification contract outside the source package.",
    "TRUSTED_LEDGER_CONTRACT": "Provide ledger checkpoint signing and verification commands with trusted identity.",
    "TRUSTED_CI": "Run the canonical CI supply-chain/provenance workflow and transfer checksum-bound evidence.",
    "REAL_BROWSER_ENVIRONMENT": "Run the canonical browser acceptance matrix in a real supported browser environment.",
    "DESKTOP_BUILD_ENVIRONMENT": "Run the desktop build/signing acceptance on a supported desktop build runner.",
    "TRUSTED_SIGNING_IDENTITY": "Provide a trusted signing identity and verify signatures through the canonical contract.",
    "HOST_TOOLING": "Install the required build tool on the isolated acceptance host and re-run preflight.",
}


def _classify_reason(reason: str) -> str:
    return _REASON_CLASS.get(reason, "EXTERNAL_OR_HOST_PREREQUISITE")


def build() -> dict:
    closure = build_closure()
    preflight = evaluate_preflight()
    toolchain = evaluate_toolchain()
    class_counts: Counter[str] = Counter()
    profiles: dict[str, dict] = {}
    grouped: dict[str, list[dict]] = defaultdict(list)

    for row in closure["requirements"]:
        classes = sorted({_classify_reason(reason) for reason in row["blocking_reasons"]})
        for cls in classes:
            class_counts[cls] += 1
        grouped[row["profile"]].append(row)

    for profile, rows in sorted(grouped.items()):
        reasons = sorted({reason for row in rows for reason in row["blocking_reasons"]})
        classes = sorted({_classify_reason(reason) for reason in reasons})
        profiles[profile] = {
            "open_requirement_count": len(rows),
            "p0_open_requirement_count": sum(1 for row in rows if row["priority"] == "P0"),
            "blocking_reasons": reasons,
            "blocker_classes": classes,
            "commands": sorted({row["command"] for row in rows}),
            "remediation": sorted({_REMEDIATION.get(cls, "Use the mapped acceptance profile on the required external host.") for cls in classes}),
            "classification": "READINESS_PLAN_NOT_ACCEPTANCE_EVIDENCE",
        }

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "PHASE176_READINESS_DIAGNOSTIC_NOT_ACCEPTANCE_EVIDENCE",
        "truth_policy": "This report prioritizes blockers and remediation only. It cannot promote requirements, acceptance profiles, or release gates to PASS.",
        "open_requirement_count": closure["open_requirement_count"],
        "p0_open_requirement_count": closure["p0_open_requirement_count"],
        "unmapped_requirement_count": closure["unmapped_requirement_count"],
        "blocker_class_counts": dict(sorted(class_counts.items())),
        "profiles": profiles,
        "preflight": {
            "classification": preflight["classification"],
            "all_external_prerequisites_ready": preflight["all_external_prerequisites_ready"],
            "groups": preflight["groups"],
        },
        "toolchain": {
            "classification": toolchain["classification"],
            "groups": toolchain["groups"],
            "available_tools": sorted(row["name"] for row in toolchain["tools"] if row["status"] == "READY"),
            "unavailable_tools": sorted(row["name"] for row in toolchain["tools"] if row["status"] != "READY"),
        },
        "current_host": {
            "git_available": bool(shutil.which("git")),
            "python_available": bool(shutil.which("python")),
        },
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["unmapped_requirement_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
