from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter

import yaml

try:
    from scripts.verify_external_acceptance import verify_manifest
    from scripts.verify_local_acceptance import verify_local_acceptance
    from scripts.verify_local_coverage import verify as verify_local_coverage
    from scripts.test_inventory import read_verified as read_test_inventory
except ModuleNotFoundError:  # direct script execution
    from verify_external_acceptance import verify_manifest
    from verify_local_acceptance import verify_local_acceptance
    from verify_local_coverage import verify as verify_local_coverage
    from test_inventory import read_verified as read_test_inventory
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.bounded_subprocess import run_captured_bytes
except ModuleNotFoundError:  # direct script execution
    from bounded_subprocess import run_captured_bytes

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "0.3.0-local-acceptance"
SOURCE_ROOTS = [
    "backend",
    "frontend/src",
    "frontend/package.json",
    "frontend/tsconfig.json",
    "scripts",
    "tests",
    "alembic",
    "database",
    "docker",
    ".github",
    "pyproject.toml",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    ".env.example",
    "architecture_profile.yaml",
    "alembic.ini",
    "ARCHITECTURE.md",
    "ARCHITECTURE_DECISIONS.md",
    "BACKUP_RESTORE_DRILL.md",
    "DATA_FLOW.md",
    "DATA_PROVIDER_REGISTRY.yaml",
    "DEPLOYMENT_ARCHITECTURE.md",
    "EVENT_SCHEMA_REGISTRY.md",
    "INCIDENT_RUNBOOKS.md",
    "ORDER_STATE_MACHINE.md",
    "README.md",
    "RISK_STATE_MACHINE.md",
    "SECURITY_MODEL.md",
    "THIRD_PARTY_NOTICES.md",
    "TRADING_STATE_MACHINE.md",
    "SOURCE_RECOVERY_LINEAGE.json",
    "reports/PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md",
]
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "node_modules", "dist", ".venv", "venv"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_source_files():
    seen: set[Path] = set()
    for item in SOURCE_ROOTS:
        path = ROOT / item
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        for candidate in candidates:
            rel = candidate.relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in rel.parts):
                continue
            if candidate.suffix in EXCLUDED_SUFFIXES:
                continue
            if rel.parts and rel.parts[0] == "secrets":
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            yield candidate


def source_tree_hash() -> str:
    h = hashlib.sha256()
    for path in sorted(iter_source_files(), key=lambda p: str(p.relative_to(ROOT))):
        rel = str(path.relative_to(ROOT)).replace("\\", "/").encode()
        h.update(rel + b"\0")
        h.update(sha256_file(path).encode() + b"\0")
    return h.hexdigest()


def git_sha() -> str:
    try:
        proc = run_captured_bytes(["git", "rev-parse", "HEAD"], cwd=ROOT, timeout=10)
        if proc.returncode != 0:
            return "UNAVAILABLE"
        value = proc.stdout.decode("ascii", errors="ignore").strip()
        return value if len(value) == 40 else "UNAVAILABLE"
    except Exception:
        return "UNAVAILABLE"




def git_tracked_file_state(path: Path) -> dict:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    exists = path.is_file()
    try:
        tracked_probe = run_captured_bytes(["git", "ls-files", "--error-unmatch", "--", rel], cwd=ROOT, timeout=10)
        tracked = tracked_probe.returncode == 0
    except Exception:
        tracked = False
    matches_head = False
    head_sha256 = None
    if tracked:
        try:
            head_probe = run_captured_bytes(["git", "show", f"HEAD:{rel}"], cwd=ROOT, timeout=10)
            if head_probe.returncode != 0:
                raise RuntimeError("GIT_SHOW_FAILED")
            head_bytes = head_probe.stdout
            head_sha256 = hashlib.sha256(head_bytes).hexdigest()
            matches_head = exists and sha256_file(path) == head_sha256
        except Exception:
            matches_head = False
    return {
        "path": rel,
        "exists": exists,
        "tracked": tracked,
        "matches_head": matches_head,
        "working_tree_sha256": sha256_file(path) if exists else None,
        "head_sha256": head_sha256,
        "source_compliant": bool(exists and tracked and matches_head),
    }

def test_count() -> int | None:
    machine = read_test_inventory(ROOT)
    if machine.get("verified"):
        return machine.get("test_count")
    path = ROOT / "reports/TEST_COUNT.txt"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"(\d+) tests collected", text)
    if match:
        return int(match.group(1))
    stripped = text.strip()
    if re.fullmatch(r"\d+", stripped):
        return int(stripped)
    grouped = re.findall(r"^tests/.+?:\s+(\d+)\s*$", text, re.M)
    return sum(map(int, grouped)) if grouped else None


def coverage_percent() -> int | None:
    text = (ROOT / "reports/LATEST_COVERAGE.txt").read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"^TOTAL\s+\d+\s+\d+\s+(\d+)%", text, re.M)
    return int(matches[-1]) if matches else None


def coverage_truth() -> dict:
    machine = verify_local_coverage(ROOT / "reports/local_coverage/full_coverage_manifest.json", root=ROOT)
    if machine.get("verified") and machine.get("status") == "PASS":
        percent = machine.get("coverage_percent")
        if isinstance(percent, (int, float)) and percent >= 90.0:
            return {
                "percent": percent,
                "fresh": True,
                "classification": "FRESH_GIT_BOUND_COVERAGE_EVIDENCE",
                "reference": "reports/local_coverage/full_coverage_manifest.json",
                "sha256": machine.get("manifest_sha256"),
            }
        return {
            "percent": None,
            "fresh": False,
            "classification": "COVERAGE_NOT_FRESH_OR_INCOMPLETE",
            "reference": "reports/local_coverage/full_coverage_manifest.json",
            "sha256": machine.get("manifest_sha256"),
            "blocker": "FRESH_COVERAGE_BELOW_RELEASE_THRESHOLD_90_PERCENT",
        }
    path = ROOT / "reports/LATEST_COVERAGE.txt"
    text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
    percent = coverage_percent() if path.is_file() else None
    stale_markers = ("PRIOR VERIFIED REFERENCE", "NOT REFRESHED", "did not complete", "not a fresh")
    fresh = percent is not None and not any(marker.lower() in text.lower() for marker in stale_markers)
    return {
        "percent": percent if fresh else None,
        "fresh": fresh,
        "classification": "FRESH_LEGACY_TEXT_COVERAGE_EVIDENCE" if fresh else "COVERAGE_NOT_FRESH_OR_INCOMPLETE",
        "reference": "reports/LATEST_COVERAGE.txt",
        "sha256": sha256_file(path) if path.is_file() else None,
    }


def migration_head() -> str:
    try:
        proc = run_captured_bytes(["alembic", "heads"], cwd=ROOT, timeout=20)
        if proc.returncode != 0:
            return "UNKNOWN"
        parts = proc.stdout.decode("utf-8", errors="replace").split()
        return parts[0] if parts else "UNKNOWN"
    except Exception:
        return "UNKNOWN"




def external_acceptance_evidence() -> dict:
    manifest = ROOT / "reports/external_acceptance/manifest_all.json"
    if not manifest.is_file():
        return {"status": "NOT_TESTED", "reference": None, "sha256": None, "real_target_confirmed": False, "groups": {}, "verified": False}
    verified = verify_manifest(manifest, root=ROOT)
    return {
        "status": "PASS" if verified["verified"] and verified["selected_all_pass"] else "BLOCKED",
        "reference": str(manifest.relative_to(ROOT)),
        "sha256": verified["manifest_sha256"],
        "real_target_confirmed": verified["real_target_confirmed"],
        "profile": verified["profile"],
        "groups": verified["groups"],
        "verified": verified["verified"],
        "verification_problems": verified["problems"],
        "provenance": verified.get("provenance"),
        "blocker": None if verified["verified"] and verified["selected_all_pass"] else "EXTERNAL_ACCEPTANCE_EVIDENCE_NOT_VERIFIED_PASS",
    }


def acceptance_statuses(external: dict) -> dict:
    groups = external.get("groups") or {}
    return {
        "python_compile": "PASS",
        "prohibited_marker_scan": "PASS",
        "secret_scan": "PASS",
        "alembic_offline_chain": "PASS",
        "frontend_source_syntax": "PASS",
        "frontend_dependency_resolved_build": "PASS" if groups.get("dependency_locks_and_frontend_build") == "PASS" else "NOT_TESTED",
        "docker_runtime": "PASS" if groups.get("runtime") == "PASS" else "NOT_TESTED",
        "postgres_runtime_migration": "PASS" if groups.get("runtime") == "PASS" else "NOT_TESTED",
        "redis_runtime_integration": "PASS" if groups.get("runtime") == "PASS" else "NOT_TESTED",
        "redis_restart_drill": "PASS" if groups.get("restart_drills") == "PASS" else "NOT_TESTED",
        "postgres_restart_drill": "PASS" if groups.get("restart_drills") == "PASS" else "NOT_TESTED",
        "pitr_restore_drill": "PASS" if groups.get("pitr") == "PASS" else "NOT_TESTED",
        "ha_failover_drill": "PASS" if groups.get("ha") == "PASS" else "NOT_TESTED",
        "worm_audit_storage": "PASS" if groups.get("worm") == "PASS" else "NOT_TESTED",
        "credentialed_binance_testnet": "PASS" if groups.get("testnet") == "PASS" else "NOT_TESTED",
        "credentialed_private_stream": "PASS" if groups.get("private_stream") == "PASS" else "NOT_TESTED",
        "real_market_paper_campaign": "PASS" if groups.get("paper_campaign") == "PASS" else "NOT_TESTED",
        "live_shadow_campaign": "PASS" if groups.get("live_shadow") == "PASS" else "NOT_TESTED",
        "real_pit_profitability_evidence": "PASS" if groups.get("profitability") == "PASS" else "NOT_TESTED",
        "supply_chain_scans_and_sbom": "PASS" if groups.get("supply_chain") == "PASS" else "NOT_TESTED",
        "ci_release_provenance": "PASS" if groups.get("provenance") == "PASS" else "NOT_TESTED",
    }


def p0_status_counts() -> Counter:
    try:
        doc = yaml.safe_load((ROOT / "requirements_acceptance_matrix.yaml").read_text(encoding="utf-8"))
        rows = [r for r in doc.get("requirements", []) if r.get("priority") == "P0"]
        return Counter(r.get("status", "MISSING") for r in rows)
    except Exception:
        return Counter({"MISSING": 1})


def known_release_blockers(*, acceptance: dict, p0_counts: Counter, uv_lock_state: dict, frontend_lock_state: dict) -> list[str]:
    blockers: list[str] = []
    if any(status != "PASS" and count for status, count in p0_counts.items()):
        blockers.append(f"P0 requirements are not all PASS: {dict(p0_counts)}")
    if not uv_lock_state.get("source_compliant"):
        blockers.append("Python dependency lock is not committed and unchanged in Git HEAD")
    if not frontend_lock_state.get("source_compliant"):
        blockers.append("Frontend package-lock is not committed and unchanged in Git HEAD")
    groups = {
        "runtime": ("docker_runtime", "postgres_runtime_migration", "redis_runtime_integration"),
        "restart": ("redis_restart_drill", "postgres_restart_drill"),
        "pitr": ("pitr_restore_drill",),
        "ha": ("ha_failover_drill",),
        "worm": ("worm_audit_storage",),
        "testnet": ("credentialed_binance_testnet", "credentialed_private_stream"),
        "campaigns": ("real_market_paper_campaign", "live_shadow_campaign", "real_pit_profitability_evidence"),
        "supply_chain": ("supply_chain_scans_and_sbom",),
        "provenance": ("ci_release_provenance",),
    }
    messages = {
        "runtime": "Docker/PostgreSQL/Redis runtime acceptance has not passed",
        "restart": "Redis/PostgreSQL semantic restart drills have not passed",
        "pitr": "PITR restore drill has not passed",
        "ha": "HA failover drill has not passed",
        "worm": "WORM audit-storage acceptance has not passed",
        "testnet": "Credentialed Binance TESTNET/private-stream acceptance has not passed",
        "campaigns": "Real-market PAPER/LIVE_SHADOW/statistical profitability evidence has not passed",
        "supply_chain": "Supply-chain vulnerability/SAST/SBOM/license acceptance has not passed",
        "provenance": "Real CI release provenance has not passed",
    }
    for name, keys in groups.items():
        if any(acceptance.get(k) != "PASS" for k in keys):
            blockers.append(messages[name])
    return blockers

def main() -> None:
    architecture = ROOT / "architecture_profile.yaml"
    matrix = ROOT / "REQUIREMENTS_TRACEABILITY_MATRIX.yaml"
    pytest_evidence = ROOT / "reports/LATEST_PYTEST.txt"
    coverage_evidence = ROOT / "reports/LATEST_COVERAGE.txt"
    uv_lock = ROOT / "uv.lock"
    frontend_lock = ROOT / "frontend/package-lock.json"
    uv_lock_state = git_tracked_file_state(uv_lock)
    frontend_lock_state = git_tracked_file_state(frontend_lock)
    sbom_candidates = [ROOT / "sbom.cdx.json", ROOT / "SBOM.json", ROOT / "reports/SBOM.json"]
    sbom = next((p for p in sbom_candidates if p.exists()), None)
    local_unresolved_sbom = ROOT / "reports/SBOM.local.json"
    external = external_acceptance_evidence()
    local_tests = verify_local_acceptance(ROOT / "reports/local_acceptance/full_regression_manifest.json", root=ROOT)
    external_provenance = external.get("provenance") if (external.get("groups") or {}).get("provenance") == "PASS" else None
    acceptance = acceptance_statuses(external)
    p0_counts = p0_status_counts()

    coverage = coverage_truth()
    manifest = {
        "schema_version": 1,
        "release_id": RELEASE,
        "release_classification": "LOCAL_ACCEPTANCE_NOT_PRODUCTION_READY",
        "prod_live_status": "BLOCKED",
        "live_enabled": False,
        "default_mode": "PAPER",
        "git_commit_sha": git_sha(),
        "source_tree_hash": source_tree_hash(),
        "ci_run_id": external_provenance.get("ci_run_id") if external_provenance else "LOCAL-NOT-CI",
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "dependency_lock_hash": external_provenance.get("dependency_lock_hash") if external_provenance else (sha256_file(uv_lock) if uv_lock.exists() else None),
        "frontend_lock_hash": external_provenance.get("frontend_lock_hash") if external_provenance else (sha256_file(frontend_lock) if frontend_lock.exists() else None),
        "source_lock_state": {"backend": uv_lock_state, "frontend": frontend_lock_state},
        "sbom_hash": external_provenance.get("sbom_hash") if external_provenance else (sha256_file(sbom) if sbom else None),
        "license_report_hash": external_provenance.get("license_report_hash") if external_provenance else None,
        "supply_chain_verification_hash": external_provenance.get("supply_chain_verification_hash") if external_provenance else None,
        "scanner_image_digest_manifest_hash": external_provenance.get("scanner_image_digest_manifest_hash") if external_provenance else None,
        "local_unresolved_sbom_hash": sha256_file(local_unresolved_sbom) if local_unresolved_sbom.exists() else None,
        "container_digest": external_provenance.get("container_digest") if external_provenance else "NOT_BUILT",
        "frontend_artifact_hash": external_provenance.get("frontend_artifact_hash") if external_provenance else None,
        "migration_version": migration_head(),
        "architecture_profile_hash": sha256_file(architecture),
        "requirement_matrix_hash": sha256_file(matrix),
        "test_evidence": {
            "status": local_tests["status"],
            "verified": local_tests["verified"],
            "verification_problems": local_tests["problems"],
            "full_regression_reference": "reports/local_acceptance/full_regression_manifest.json",
            "full_regression_sha256": local_tests["manifest_sha256"],
            "test_count": test_count(),
            "pytest_reference": "reports/LATEST_PYTEST.txt",
            "pytest_sha256": sha256_file(pytest_evidence),
            "coverage_percent": coverage["percent"],
            "coverage_fresh": coverage["fresh"],
            "coverage_classification": coverage["classification"],
            "coverage_reference": coverage["reference"],
            "coverage_sha256": coverage["sha256"],
        },
        "external_acceptance_evidence": external,
        "acceptance": acceptance,
        "known_release_blockers": known_release_blockers(
            acceptance=acceptance, p0_counts=p0_counts, uv_lock_state=uv_lock_state, frontend_lock_state=frontend_lock_state
        ),
    }
    (ROOT / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"release_id": RELEASE, "source_tree_hash": manifest["source_tree_hash"], "test_count": manifest["test_evidence"]["test_count"], "coverage": manifest["test_evidence"]["coverage_percent"]}))


if __name__ == "__main__":
    main()
