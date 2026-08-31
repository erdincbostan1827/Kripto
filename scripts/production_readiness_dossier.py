from __future__ import annotations

import json
import sys
from collections import defaultdict
from functools import lru_cache
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.blocker_dossier import build_requirement_blockers
from scripts.external_acceptance_preflight import evaluate as evaluate_preflight

PROFILE_BY_CATEGORY = {
    "RUNTIME_INTEGRATION": "runtime",
    "CONTAINER_RUNTIME": "runtime",
    "RUNTIME_FAULT_DRILL": "restart-drills",
    "SUPPLY_CHAIN_PROVENANCE": "supply-chain",
    "RECOVERY_HA_RUNTIME": "pitr_or_ha",
    "MARKET_CAMPAIGN": "testnet_or_campaign",
    "EXTERNAL_IMMUTABLE_STORAGE": "worm",
    "LOCAL_OR_AMBIGUOUS": "manual_review",
}

COMMANDS = {
    "run-all-external": "python scripts/external/run_all_external_requirements.py --confirm-real-target",
    "execution-map": "python scripts/external/execution_map.py",
    "verify-execution-plan": "python scripts/verify_external_execution_plan.py",
    "toolchain-readiness": "python scripts/external/toolchain_readiness.py",
    "challenge": "python scripts/generate_acceptance_challenge.py",
    "locks": "python scripts/external_acceptance_runner.py --profile locks --confirm-real-target",
    "frontend-browser": "python scripts/external/frontend_browser_acceptance.py --confirm-real-target",
    "desktop-build": "python scripts/external/tauri_build_readiness.py --confirm-real-target",
    "runtime": "python scripts/external_acceptance_runner.py --profile runtime --confirm-real-target",
    "restart-drills": "python scripts/external_acceptance_runner.py --profile restart-drills --confirm-real-target",
    "supply-chain": "python scripts/external_acceptance_runner.py --profile supply-chain --confirm-real-target",
    "pitr": "python scripts/external_acceptance_runner.py --profile pitr --confirm-real-target",
    "ha": "python scripts/external_acceptance_runner.py --profile ha --confirm-real-target",
    "worm": "python scripts/external_acceptance_runner.py --profile worm --confirm-real-target",
    "testnet": "python scripts/external_acceptance_runner.py --profile testnet --confirm-real-target",
    "provenance": "python scripts/external_acceptance_runner.py --profile provenance --confirm-real-target",
    "campaign_templates": "python scripts/external/generate_campaign_evidence_templates.py",
    "campaigns": "python scripts/external_acceptance_runner.py --profile campaigns --confirm-real-target",
    "merge": "python scripts/merge_external_acceptance.py",
    "verify": "python scripts/verify_external_acceptance.py reports/external_acceptance/manifest_all.json",
    "release_gate": "python scripts/generate_release_manifest.py && python scripts/release_gate.py",
}


@lru_cache(maxsize=2)
def _load_matrix_cached(path_text: str, mtime_ns: int, size: int) -> dict:
    del mtime_ns, size
    return yaml.safe_load(Path(path_text).read_text(encoding="utf-8"))


def _matrix_doc(path: Path) -> dict:
    stat = path.stat()
    return _load_matrix_cached(str(path.resolve()), stat.st_mtime_ns, stat.st_size)


def build() -> dict:
    matrix_path = ROOT / "REQUIREMENTS_TRACEABILITY_MATRIX.yaml"
    blockers = build_requirement_blockers(matrix_path, matrix_doc=_matrix_doc(matrix_path))
    by_category: dict[str, list[str]] = defaultdict(list)
    for b in blockers:
        by_category[b.category].append(b.requirement_id)
    preflight = evaluate_preflight()
    return {
        "schema_version": "1.0",
        "classification": "PRODUCTION_READINESS_DOSSIER_NOT_ACCEPTANCE_EVIDENCE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "truth_policy": "This dossier is an execution plan only. It cannot promote a requirement or release gate to PASS.",
        "p0_blocker_count": len(blockers),
        "external_required_count": sum(1 for b in blockers if b.external_required),
        "blockers_by_category": {k: {"count": len(v), "requirement_ids": sorted(v), "recommended_profile": PROFILE_BY_CATEGORY.get(k, "manual_review")} for k, v in sorted(by_category.items())},
        "preflight_groups": preflight["groups"],
        "master_command": {"name": "master_all_external_requirements", "command": COMMANDS["run-all-external"], "classification": "coordinator_not_acceptance_evidence"},
        "workflow": [
            {"step": 1, "name": "create_release_challenge", "command": COMMANDS["challenge"]},
            {"step": 2, "name": "dependency_locks", "command": COMMANDS["locks"]},
            {"step": 3, "name": "frontend_browser", "command": COMMANDS["frontend-browser"], "classification": "standalone_readiness_not_canonical_external_profile"},
            {"step": 4, "name": "runtime", "command": COMMANDS["runtime"]},
            {"step": 5, "name": "restart_drills", "command": COMMANDS["restart-drills"]},
            {"step": 6, "name": "supply_chain", "command": COMMANDS["supply-chain"]},
            {"step": 7, "name": "pitr", "command": COMMANDS["pitr"]},
            {"step": 8, "name": "ha", "command": COMMANDS["ha"]},
            {"step": 9, "name": "worm", "command": COMMANDS["worm"]},
            {"step": 10, "name": "testnet", "command": COMMANDS["testnet"]},
            {"step": 11, "name": "map_all_open_requirements", "command": COMMANDS["execution-map"], "classification": "execution_plan_not_acceptance_evidence"},
            {"step": 12, "name": "verify_external_execution_plan", "command": COMMANDS["verify-execution-plan"], "classification": "execution_plan_consistency_not_acceptance_evidence"},
            {"step": 13, "name": "inventory_external_toolchain", "command": COMMANDS["toolchain-readiness"], "classification": "standalone_readiness_not_acceptance_evidence"},
            {"step": 14, "name": "desktop_build", "command": COMMANDS["desktop-build"], "classification": "standalone_readiness_not_signing_evidence"},
            {"step": 15, "name": "provenance", "command": COMMANDS["provenance"]},
            {"step": 16, "name": "generate_campaign_evidence_templates", "command": COMMANDS["campaign_templates"]},
            {"step": 17, "name": "validate_campaign_evidence", "command": COMMANDS["campaigns"]},
            {"step": 18, "name": "merge_external_profiles", "command": COMMANDS["merge"]},
            {"step": 19, "name": "verify_external_bundle", "command": COMMANDS["verify"]},
            {"step": 20, "name": "release_gate", "command": COMMANDS["release_gate"]},
        ],
        "manual_external_evidence_still_required": [
            "credentialed private user-data stream lifecycle/reconciliation evidence must be produced externally",
            "real-market PAPER campaign duration and regime coverage evidence must be produced externally",
            "LIVE-shadow campaign with zero unintended submissions evidence must be produced externally",
            "real point-in-time profitability/statistical evidence must be produced externally",
            "templates and validators validate evidence; they do not create or substitute for real evidence",
            "credential values must never be copied into evidence artifacts",
        ],
    }


def main() -> int:
    payload = build()
    out = ROOT / "reports" / "PRODUCTION_READINESS_DOSSIER.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
