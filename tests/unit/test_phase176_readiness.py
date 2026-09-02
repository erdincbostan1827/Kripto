from __future__ import annotations

from pathlib import Path

import yaml

from scripts.phase176_readiness import build

ROOT = Path(__file__).resolve().parents[2]


def test_phase176_readiness_covers_every_open_requirement_without_promotion():
    payload = build()
    assert payload["classification"] == "PHASE176_READINESS_DIAGNOSTIC_NOT_ACCEPTANCE_EVIDENCE"
    matrix = yaml.safe_load((ROOT / "requirements_acceptance_matrix.yaml").read_text(encoding="utf-8"))
    open_rows = [row for row in matrix["requirements"] if row["status"] == "NOT_TESTED"]
    p0_open_rows = [row for row in open_rows if row["priority"] == "P0"]
    assert payload["open_requirement_count"] == len(open_rows)
    assert payload["p0_open_requirement_count"] == len(p0_open_rows)
    assert payload["unmapped_requirement_count"] == 0
    assert sum(row["open_requirement_count"] for row in payload["profiles"].values()) == len(open_rows)
    assert all(row["classification"] == "READINESS_PLAN_NOT_ACCEPTANCE_EVIDENCE" for row in payload["profiles"].values())


def test_phase176_readiness_has_specific_current_blocker_classes():
    payload = build()
    counts = payload["blocker_class_counts"]
    assert "REGISTRY_OR_LOCK_RESOLUTION" not in counts
    if "dependency-locks" in payload["profiles"]:
        assert payload["profiles"]["dependency-locks"]["blocker_classes"] == []
    else:
        assert payload["open_requirement_count"] > 0
    assert counts["HOST_RUNTIME_CAPABILITY"] >= 1
    assert counts["TRUSTED_CI"] >= 1
    assert counts["REAL_BROWSER_ENVIRONMENT"] >= 1
    assert payload["preflight"]["all_external_prerequisites_ready"] is False


def test_phase176_packaging_binds_readiness_snapshot():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    assert '"PHASE176_READINESS.json"' in (root / "scripts/package_release.py").read_text(encoding="utf-8")
    assert '"reports/PHASE176_READINESS.json"' in (root / "scripts/package_evidence.py").read_text(encoding="utf-8")
