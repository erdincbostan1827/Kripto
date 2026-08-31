from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.release.blocker_dossier import build_requirement_blockers
from scripts.external.execution_map import classify as classify_execution_profile

MATRIX = ROOT / "REQUIREMENTS_TRACEABILITY_MATRIX.yaml"
OUT = ROOT / "reports" / "EXTERNAL_EXECUTION_PLAN_VERIFICATION.json"

CATEGORY_TO_PROFILES = {
    "RUNTIME_INTEGRATION": {"runtime"},
    "CONTAINER_RUNTIME": {"runtime"},
    "RUNTIME_FAULT_DRILL": {"restart-drills"},
    "SUPPLY_CHAIN_PROVENANCE": {"supply-chain", "provenance", "signing"},
    "RECOVERY_HA_RUNTIME": {"pitr", "ha"},
    "MARKET_CAMPAIGN": {"testnet-campaigns"},
    "EXTERNAL_IMMUTABLE_STORAGE": {"worm"},
}


def build() -> dict:
    doc = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    open_rows = [r for r in doc.get("requirements", []) if r.get("status") == "NOT_TESTED"]
    p0_open = [r for r in open_rows if r.get("priority") == "P0"]
    blockers = {b.requirement_id: b for b in build_requirement_blockers(MATRIX, matrix_doc=doc)}

    mappings = []
    problems: list[str] = []
    ambiguous: list[str] = []
    profile_counts: Counter[str] = Counter()

    for row in open_rows:
        rid = str(row["requirement_id"])
        section = int(row["section"])
        desc = str(row.get("description", ""))
        try:
            profile = classify_execution_profile(section, desc)
        except Exception as exc:  # fail closed for newly introduced sections
            problems.append(f"{rid}:UNMAPPED:{exc}")
            continue
        profile_counts[profile] += 1
        item = {
            "requirement_id": rid,
            "priority": row.get("priority"),
            "section": section,
            "profile": profile,
        }
        blocker = blockers.get(rid)
        if blocker is not None:
            item["blocker_category"] = blocker.category
            item["external_required"] = blocker.external_required
            if blocker.category == "LOCAL_OR_AMBIGUOUS":
                ambiguous.append(rid)
            allowed = CATEGORY_TO_PROFILES.get(blocker.category)
            if not allowed:
                problems.append(f"{rid}:NO_PROFILE_CONTRACT_FOR_CATEGORY:{blocker.category}")
            elif profile not in allowed:
                problems.append(
                    f"{rid}:PROFILE_CATEGORY_MISMATCH:{blocker.category}:{profile}:allowed={','.join(sorted(allowed))}"
                )
            if not blocker.external_required:
                problems.append(f"{rid}:P0_BLOCKER_NOT_MARKED_EXTERNAL")
        mappings.append(item)

    mapped_ids = {m["requirement_id"] for m in mappings}
    p0_ids = {str(r["requirement_id"]) for r in p0_open}
    missing_p0 = sorted(p0_ids - mapped_ids)
    if missing_p0:
        problems.extend(f"{rid}:P0_UNMAPPED" for rid in missing_p0)

    verified = not problems and not ambiguous and len(mapped_ids) == len(open_rows)
    return {
        "schema_version": "1.0",
        "classification": "EXTERNAL_EXECUTION_PLAN_CONSISTENCY_NOT_ACCEPTANCE_EVIDENCE",
        "truth_policy": "This verifies that every unresolved requirement has one non-ambiguous execution profile and that P0 blocker categories agree with that profile. It does not satisfy any requirement or production release gate.",
        "open_requirement_count": len(open_rows),
        "mapped_requirement_count": len(mapped_ids),
        "p0_open_requirement_count": len(p0_open),
        "ambiguous_p0_requirement_ids": sorted(ambiguous),
        "profile_counts": dict(sorted(profile_counts.items())),
        "problems": sorted(problems),
        "verified": verified,
        "mappings": mappings,
    }


def main() -> int:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
