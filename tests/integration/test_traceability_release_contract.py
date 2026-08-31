from __future__ import annotations

import ast
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {"PASS", "FAIL", "NOT_TESTED", "MOCK", "UNSUPPORTED"}
RELEASE = "0.3.0-local-acceptance"


def _test_names() -> set[str]:
    names: set[str] = set()
    for path in ROOT.joinpath("tests").rglob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                names.add(node.name)
    return names


def _matrix(path: str):
    return yaml.safe_load(ROOT.joinpath(path).read_text(encoding="utf-8"))


def test_machine_readable_traceability_is_evidence_bound_and_consistent():
    a = _matrix("REQUIREMENTS_TRACEABILITY_MATRIX.yaml")
    b = _matrix("requirements_acceptance_matrix.yaml")
    assert a["allowed_status"] == ["PASS", "FAIL", "NOT_TESTED", "MOCK", "UNSUPPORTED"]
    assert b["allowed_status"] == a["allowed_status"]
    assert len(a["requirements"]) == len(b["requirements"]) == 2691
    tests = _test_names()
    a_status = {r["requirement_id"]: r["status"] for r in a["requirements"]}
    b_status = {r["requirement_id"]: r["status"] for r in b["requirements"]}
    assert a_status == b_status
    for row in a["requirements"]:
        assert row["status"] in ALLOWED
        if row["status"] == "PASS":
            assert row.get("test_ids")
            assert row.get("evidence_refs")
            assert row.get("last_verified_release") == RELEASE
            assert set(row["test_ids"]).issubset(tests)
        if row["status"] == "UNSUPPORTED":
            assert row.get("evidence_refs")
            assert row.get("last_verified_release") == RELEASE


def test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity():
    manifest = json.loads(ROOT.joinpath("RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["release_id"] == RELEASE
    assert manifest["release_classification"] == "LOCAL_ACCEPTANCE_NOT_PRODUCTION_READY"
    assert manifest["prod_live_status"] == "BLOCKED"
    assert manifest["live_enabled"] is False
    assert manifest["default_mode"] == "PAPER"
    status = manifest["test_evidence"]["status"]
    assert status in {"PASS", "NOT_TESTED"}
    if status == "PASS":
        assert manifest["test_evidence"]["verified"] is True
    else:
        assert manifest["test_evidence"]["verified"] is False
        assert manifest["test_evidence"]["verification_problems"]
    assert manifest["test_evidence"]["test_count"] >= 268
    coverage = manifest["test_evidence"]["coverage_percent"]
    if coverage is None:
        assert manifest["test_evidence"]["coverage_fresh"] is False
        assert manifest["test_evidence"]["coverage_classification"] == "COVERAGE_NOT_FRESH_OR_INCOMPLETE"
    else:
        assert manifest["test_evidence"]["coverage_fresh"] is True
        assert coverage >= 90
    assert manifest["acceptance"]["frontend_dependency_resolved_build"] == "NOT_TESTED"
    assert manifest["acceptance"]["docker_runtime"] == "NOT_TESTED"
    assert manifest["acceptance"]["credentialed_binance_testnet"] == "NOT_TESTED"
    assert manifest["source_tree_hash"] and len(manifest["source_tree_hash"]) == 64
    assert manifest["migration_version"] == "0003_dead_letter_forensics"
    assert manifest["architecture_profile_hash"] and len(manifest["architecture_profile_hash"]) == 64
    assert manifest["requirement_matrix_hash"] and len(manifest["requirement_matrix_hash"]) == 64
    assert manifest["test_evidence"]["pytest_sha256"] and len(manifest["test_evidence"]["pytest_sha256"]) == 64
    assert manifest["known_release_blockers"]


def test_v51_mandatory_traceability_and_runbook_artifacts_exist():
    required = [
        "ARCHITECTURE_DECISIONS.md",
        "architecture_profile.yaml",
        "REQUIREMENTS_TRACEABILITY.md",
        "requirements_acceptance_matrix.yaml",
        "INCIDENT_RUNBOOKS.md",
        "BACKUP_RESTORE_DRILL.md",
        "RELEASE_MANIFEST.json",
        "DATA_PROVIDER_REGISTRY.yaml",
        "EVENT_SCHEMA_REGISTRY.md",
    ]
    for rel in required:
        path = ROOT / rel
        assert path.is_file() and path.stat().st_size > 0, rel
