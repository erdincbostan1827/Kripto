from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_release_consistency import verify


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_consistency_accepts_matching_test_coverage_git_and_release_state(tmp_path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/TEST_COUNT.txt").write_text("740 tests collected\n")
    _write_json(tmp_path / "RELEASE_MANIFEST.json", {
        "git_commit_sha": "a" * 40, "default_mode": "PAPER", "live_enabled": False, "prod_live_status": "BLOCKED",
        "test_evidence": {"test_count": 740, "coverage_percent": None, "coverage_fresh": False, "coverage_classification": "COVERAGE_NOT_FRESH_OR_INCOMPLETE"},
    })
    _write_json(tmp_path / "reports/PROJECT_STATUS.json", {
        "test_count": 740, "backend_coverage_percent": None, "coverage_fresh": False, "coverage_classification": "COVERAGE_NOT_FRESH_OR_INCOMPLETE",
        "default_mode": "PAPER", "live_enabled": False, "prod_live_status": "BLOCKED",
    })
    _write_json(tmp_path / "reports/LOCAL_SOURCE_PROVENANCE.json", {"git_commit_sha": "a" * 40})
    assert verify(tmp_path)["verified"] is True


def test_consistency_rejects_stale_status_coverage_and_test_count(tmp_path):
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/TEST_COUNT.txt").write_text("740 tests collected\n")
    _write_json(tmp_path / "RELEASE_MANIFEST.json", {
        "git_commit_sha": "a" * 40, "default_mode": "PAPER", "live_enabled": False, "prod_live_status": "BLOCKED",
        "test_evidence": {"test_count": 740, "coverage_percent": None, "coverage_fresh": False, "coverage_classification": "COVERAGE_NOT_FRESH_OR_INCOMPLETE"},
    })
    _write_json(tmp_path / "reports/PROJECT_STATUS.json", {
        "test_count": 699, "backend_coverage_percent": 93, "coverage_fresh": True, "coverage_classification": "FRESH",
        "default_mode": "PAPER", "live_enabled": False, "prod_live_status": "BLOCKED",
    })
    _write_json(tmp_path / "reports/LOCAL_SOURCE_PROVENANCE.json", {"git_commit_sha": "a" * 40})
    result = verify(tmp_path)
    assert result["verified"] is False
    assert "STATUS_TEST_COUNT_MISMATCH" in result["problems"]
    assert "STATUS_RELEASE_COVERAGE_PERCENT_MISMATCH" in result["problems"]


def test_release_consistency_report_is_canonical_packaging_evidence():
    from scripts import package_evidence, package_release
    assert "reports/RELEASE_CONSISTENCY.json" in package_evidence.CANONICAL_FILES
    assert "RELEASE_CONSISTENCY.json" in package_release.CANONICAL_REPORT_FILES
