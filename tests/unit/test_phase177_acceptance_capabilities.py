from __future__ import annotations

from scripts.phase177_acceptance_capabilities import build


def test_phase177_capability_report_never_promotes_acceptance():
    payload = build(probe_dns=False)
    assert payload["classification"].endswith("NOT_ACCEPTANCE_EVIDENCE")
    assert payload["open_requirement_count"] == 100
    assert payload["p0_open_requirement_count"] == 42
    assert "acceptance_complete" in payload["profiles"]["dependency-locks"]
    assert payload["profiles"]["supply-chain"]["trusted_ci_still_required"] is True


def test_phase177_browser_capability_requires_locks_even_with_host_browser():
    payload = build(probe_dns=False)
    row = payload["profiles"]["frontend-browser"]
    if not row["dependency_locks_ready"]:
        assert row["runnable_now"] is False
