from __future__ import annotations

from pathlib import Path

import yaml

from scripts.phase177_acceptance_capabilities import build

ROOT = Path(__file__).resolve().parents[2]


def test_phase177_capability_report_never_promotes_acceptance():
    payload = build(probe_dns=False)
    assert payload["classification"].endswith("NOT_ACCEPTANCE_EVIDENCE")
    matrix = yaml.safe_load((ROOT / "requirements_acceptance_matrix.yaml").read_text(encoding="utf-8"))
    open_rows = [row for row in matrix["requirements"] if row["status"] == "NOT_TESTED"]
    assert payload["open_requirement_count"] == len(open_rows)
    assert payload["p0_open_requirement_count"] == sum(row["priority"] == "P0" for row in open_rows)
    assert "acceptance_complete" in payload["profiles"]["dependency-locks"]
    assert payload["profiles"]["supply-chain"]["trusted_ci_still_required"] is True


def test_phase177_browser_capability_requires_locks_even_with_host_browser():
    payload = build(probe_dns=False)
    row = payload["profiles"]["frontend-browser"]
    if not row["dependency_locks_ready"]:
        assert row["runnable_now"] is False
