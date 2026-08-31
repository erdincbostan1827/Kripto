from pathlib import Path

from scripts.external.frontend_browser_acceptance import VIEWPORTS, run
from scripts.production_acceptance_orchestrator import PROFILES

ROOT = Path(__file__).resolve().parents[2]


def test_frontend_browser_readiness_tool_is_fail_closed_and_kept_outside_canonical_real_evidence_profiles():
    assert "frontend-browser" not in PROFILES
    assert VIEWPORTS == ((1920,1080),(1366,768),(1024,768),(390,844))
    source = (ROOT / "scripts/external/frontend_browser_acceptance.py").read_text(encoding="utf-8")
    for required in ("npm", "ci", "Vitest", "production build", "Chromium", "package-lock.json", "REAL_DEPENDENCY_RESOLVED_FRONTEND_BROWSER_ACCEPTANCE"):
        assert required in source
    assert "Edge/Firefox/WebKit" in source


def test_frontend_browser_acceptance_blocks_without_source_lock():
    # Current source package intentionally has no dependency lock; the external acceptance must never promote this to PASS.
    result = run(timeout=1)
    assert result["verified"] is False
    assert "FRONTEND_LOCK_MISSING" in result["blockers"]
    assert "REAL_TARGET_NOT_EXPLICITLY_CONFIRMED" in result["blockers"]
    assert result["real_target_explicitly_confirmed"] is False
    assert result["classification"] == "REAL_DEPENDENCY_RESOLVED_FRONTEND_BROWSER_ACCEPTANCE"
