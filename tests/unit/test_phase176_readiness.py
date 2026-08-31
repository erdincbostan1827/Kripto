from __future__ import annotations

from scripts.phase176_readiness import build


def test_phase176_readiness_covers_every_open_requirement_without_promotion():
    payload = build()
    assert payload["classification"] == "PHASE176_READINESS_DIAGNOSTIC_NOT_ACCEPTANCE_EVIDENCE"
    assert payload["open_requirement_count"] == 100
    assert payload["p0_open_requirement_count"] == 42
    assert payload["unmapped_requirement_count"] == 0
    assert sum(row["open_requirement_count"] for row in payload["profiles"].values()) == 100
    assert all(row["classification"] == "READINESS_PLAN_NOT_ACCEPTANCE_EVIDENCE" for row in payload["profiles"].values())


def test_phase176_readiness_has_specific_current_blocker_classes():
    payload = build()
    counts = payload["blocker_class_counts"]
    assert counts["REGISTRY_OR_LOCK_RESOLUTION"] >= 2
    assert counts["HOST_RUNTIME_CAPABILITY"] >= 1
    assert counts["TRUSTED_CI"] >= 1
    assert counts["REAL_BROWSER_ENVIRONMENT"] >= 1
    assert payload["preflight"]["all_external_prerequisites_ready"] is False


def test_phase176_packaging_binds_readiness_snapshot():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    assert '"PHASE176_READINESS.json"' in (root / "scripts/package_release.py").read_text(encoding="utf-8")
    assert '"reports/PHASE176_READINESS.json"' in (root / "scripts/package_evidence.py").read_text(encoding="utf-8")
