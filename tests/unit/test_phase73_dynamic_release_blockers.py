from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts.generate_release_manifest import acceptance_statuses, known_release_blockers
from scripts.release_gate import REQUIRED_EXTERNAL_ACCEPTANCE


def _all_pass_acceptance() -> dict[str, str]:
    groups = {
        "dependency_locks_and_frontend_build": "PASS", "runtime": "PASS", "restart_drills": "PASS",
        "pitr": "PASS", "ha": "PASS", "worm": "PASS", "testnet": "PASS", "private_stream": "PASS",
        "paper_campaign": "PASS", "live_shadow": "PASS", "profitability": "PASS", "supply_chain": "PASS",
        "provenance": "PASS",
    }
    return acceptance_statuses({"groups": groups})


def test_release_gate_explicitly_requires_ci_release_provenance():
    assert "ci_release_provenance" in REQUIRED_EXTERNAL_ACCEPTANCE
    assert acceptance_statuses({"groups": {}})["ci_release_provenance"] == "NOT_TESTED"
    assert acceptance_statuses({"groups": {"provenance": "PASS"}})["ci_release_provenance"] == "PASS"


def test_known_release_blockers_are_evidence_driven(tmp_path: Path):
    blockers = known_release_blockers(
        acceptance=_all_pass_acceptance(), p0_counts=Counter({"PASS": 1511}),
        uv_lock_state={"source_compliant": True}, frontend_lock_state={"source_compliant": True}
    )
    assert blockers == []


def test_known_release_blockers_report_only_current_failures(tmp_path: Path):
    acceptance = _all_pass_acceptance()
    acceptance["ci_release_provenance"] = "NOT_TESTED"
    blockers = known_release_blockers(
        acceptance=acceptance, p0_counts=Counter({"PASS": 1500, "NOT_TESTED": 11}),
        uv_lock_state={"source_compliant": False}, frontend_lock_state={"source_compliant": False}
    )
    assert any("P0 requirements" in b for b in blockers)
    assert "Python dependency lock is not committed and unchanged in Git HEAD" in blockers
    assert "Frontend package-lock is not committed and unchanged in Git HEAD" in blockers
    assert "Real CI release provenance has not passed" in blockers
    assert all("PITR" not in b for b in blockers)
