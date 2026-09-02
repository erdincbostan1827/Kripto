from __future__ import annotations

import json
from pathlib import Path

from scripts.acceptance_closure_status import PROFILE_PREREQUISITES, build
from scripts.external.execution_map import COMMANDS

ROOT = Path(__file__).resolve().parents[2]


def test_phase175_every_open_requirement_has_one_profile_command_and_prerequisite_set():
    payload = build()
    assert payload["classification"] == "ACCEPTANCE_CLOSURE_STATUS_NOT_ACCEPTANCE_EVIDENCE"
    matrix = json.loads(json.dumps(__import__("yaml").safe_load((ROOT / "requirements_acceptance_matrix.yaml").read_text(encoding="utf-8"))))
    open_rows = [row for row in matrix["requirements"] if row["status"] == "NOT_TESTED"]
    p0_open_rows = [row for row in open_rows if row["priority"] == "P0"]
    assert payload["open_requirement_count"] == len(open_rows)
    assert payload["p0_open_requirement_count"] == len(p0_open_rows)
    assert payload["unmapped_requirement_count"] == 0
    assert len(payload["requirements"]) == len(open_rows)
    assert sum(payload["profile_counts"].values()) == len(open_rows)
    for row in payload["requirements"]:
        assert row["profile"] in COMMANDS
        assert row["profile"] in PROFILE_PREREQUISITES
        assert row["command"] == COMMANDS[row["profile"]]
        assert row["prerequisites"]
        assert row["classification"] == "CLOSURE_PLAN_NOT_ACCEPTANCE_EVIDENCE"


def test_phase175_external_requirements_never_become_pass_from_preflight():
    payload = build()
    encoded = json.dumps(payload)
    assert "NOT_ACCEPTANCE_EVIDENCE" in encoded
    assert "PASS" not in {row.get("status") for row in payload["requirements"]}
    ready = [row for row in payload["requirements"] if not row["blocked"]]
    for row in ready:
        assert all(item["ready"] for item in row["prerequisites"])
    # Once dependency-lock requirements themselves are closed they must disappear
    # from the open closure plan instead of lingering as a permanently-ready row.
    if payload["profile_counts"].get("dependency-locks", 0) == 0:
        assert "dependency-locks" not in {row["profile"] for row in ready}
    assert payload["blocked_requirement_count"] == payload["open_requirement_count"] - len(ready)


def test_phase175_current_environment_exposes_known_hard_blockers():
    payload = build()
    reasons = payload["blocking_reason_counts"]
    assert "group:dependency_locks" not in reasons
    assert reasons["group:container_runtime"] >= 1
    assert reasons["external:real_browser_matrix"] >= 1
    assert reasons["external:trusted_ci_supply_chain_evidence"] >= 1
    assert reasons["external:trusted_ci_provenance"] >= 1
    assert payload["preflight_all_external_prerequisites_ready"] is False


def test_phase175_release_packaging_whitelists_only_canonical_closure_snapshot():
    text = (ROOT / "scripts/package_release.py").read_text(encoding="utf-8")
    assert '"ACCEPTANCE_CLOSURE_STATUS.json"' in text
    runbook = (ROOT / "ACCEPTANCE_CLOSURE_RUNBOOK.md").read_text(encoding="utf-8")
    assert "Preflight `READY`" in runbook
    assert "Keep production LIVE blocked" in runbook


def test_phase175_evidence_bundle_includes_closure_status():
    text = (ROOT / "scripts/package_evidence.py").read_text(encoding="utf-8")
    assert '"reports/ACCEPTANCE_CLOSURE_STATUS.json"' in text
