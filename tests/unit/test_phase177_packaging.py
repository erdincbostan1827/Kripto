from pathlib import Path


def test_phase177_reports_are_bound_into_delivery_packages():
    root = Path(__file__).resolve().parents[2]
    evidence = (root / "scripts/package_evidence.py").read_text(encoding="utf-8")
    release = (root / "scripts/package_release.py").read_text(encoding="utf-8")
    assert '"reports/PHASE177_ACCEPTANCE_CAPABILITIES.json"' in evidence
    assert '"reports/PHASE177_EXTERNAL_ACCEPTANCE_HANDOFF.zip"' in evidence
    assert '"PHASE177_ACCEPTANCE_CAPABILITIES.json"' in release
