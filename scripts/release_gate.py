from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

try:
    from scripts.verify_source_locks import verify_source_locks
except ModuleNotFoundError:
    from verify_source_locks import verify_source_locks

MATRIX = Path("requirements_acceptance_matrix.yaml")
MANIFEST = Path("RELEASE_MANIFEST.json")
REQUIRED_LOCAL_EVIDENCE = [
    Path("reports/LATEST_PYTEST.txt"),
    Path("reports/LATEST_COVERAGE.txt"),
    Path("reports/ALEMBIC_OFFLINE_SQL.txt"),
    Path("reports/SECRET_SCAN.txt"),
    Path("reports/PROHIBITED_SCAN.txt"),
    Path("reports/DEPENDENCY_POLICY.txt"),
]
REQUIRED_EXTERNAL_ACCEPTANCE = [
    "frontend_dependency_resolved_build",
    "docker_runtime",
    "postgres_runtime_migration",
    "redis_runtime_integration",
    "redis_restart_drill",
    "postgres_restart_drill",
    "pitr_restore_drill",
    "ha_failover_drill",
    "worm_audit_storage",
    "credentialed_binance_testnet",
    "credentialed_private_stream",
    "real_market_paper_campaign",
    "live_shadow_campaign",
    "real_pit_profitability_evidence",
    "supply_chain_scans_and_sbom",
    "ci_release_provenance",
]


def _git_lock_is_source_compliant(root: Path, rel: str) -> tuple[bool, str]:
    """Compatibility wrapper around the canonical source-lock verifier."""
    result = verify_source_locks(root)
    row = next((item for item in result["locks"] if item["path"] == rel), None)
    if row and row["source_compliant"]:
        return True, "PASS"
    if row is None:
        return False, f"{rel} is not part of the canonical source-lock set"
    if not row["exists"]:
        return False, f"{rel} missing"
    if not result.get("identity_verified"):
        return False, f"{rel} source identity is not verifiable"
    if result.get("identity_mode") == "PACKAGE_MANIFEST":
        return False, f"{rel} is not bound to PACKAGE_MANIFEST.json"
    if not row["tracked"]:
        return False, f"{rel} is not tracked in Git HEAD"
    return False, f"{rel} differs from Git HEAD"


def evaluate_release_gate(root: Path = Path(".")) -> list[str]:
    matrix_path = root / MATRIX
    manifest_path = root / MANIFEST
    blockers: list[str] = []

    if not matrix_path.exists():
        blockers.append(f"requirement matrix missing: {MATRIX}")
        return blockers
    if not manifest_path.exists():
        blockers.append(f"release manifest missing: {MANIFEST}")
        return blockers

    doc = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    requirements = doc["requirements"]
    p0 = [row for row in requirements if row.get("priority") == "P0"]
    counts = Counter(row.get("status") for row in p0)
    if any(row.get("status") != "PASS" for row in p0):
        blockers.append(f"P0 requirements are not all PASS: {dict(counts)}")

    source_locks = verify_source_locks(root)
    for rel in ("uv.lock", "frontend/package-lock.json"):
        ok, reason = _git_lock_is_source_compliant(root, rel)
        if not ok:
            blockers.append(reason)
    if not source_locks.get("identity_verified"):
        blockers.append("source repository identity is not verifiable")

    for path in REQUIRED_LOCAL_EVIDENCE:
        if not (root / path).exists():
            blockers.append(f"required local evidence missing: {path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    test_evidence = manifest.get("test_evidence", {})
    if test_evidence.get("status") != "PASS" or test_evidence.get("verified") is not True:
        blockers.append(f"local full regression evidence not PASS/verified: {test_evidence.get('status', 'MISSING')}")
    acceptance = manifest.get("acceptance", {})
    for key in REQUIRED_EXTERNAL_ACCEPTANCE:
        status = acceptance.get(key, "MISSING")
        if status != "PASS":
            blockers.append(f"external acceptance not PASS: {key}={status}")

    if manifest.get("prod_live_status") not in {"ELIGIBLE_FOR_HUMAN_APPROVAL", "APPROVED"}:
        blockers.append(f"manifest prod_live_status is fail-closed: {manifest.get('prod_live_status', 'MISSING')}")
    if manifest.get("live_enabled") is not False:
        blockers.append("manifest live_enabled must remain false until post-gate human approval")
    if manifest.get("default_mode") != "PAPER":
        blockers.append(f"default mode must be PAPER: {manifest.get('default_mode', 'MISSING')}")

    return blockers


def main() -> int:
    blockers = evaluate_release_gate()
    if blockers:
        print("PROD_LIVE_RELEASE=BLOCKED")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1
    print("PROD_LIVE_RELEASE=ELIGIBLE_FOR_HUMAN_APPROVAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
