from pathlib import Path

from scripts.verify_source_locks import verify_source_locks
from scripts.verify_workflow_action_pins import verify_workflow_action_pins

ROOT = Path(__file__).resolve().parents[2]


def test_production_acceptance_consumes_committed_locks_only():
    text = (ROOT / ".github/workflows/production-acceptance.yml").read_text()
    assert "python scripts/verify_source_locks.py" in text
    assert "uv lock --locked" in text
    assert "npm ci --ignore-scripts" in text
    assert "run: uv lock\n" not in text
    assert "npm install --package-lock-only" not in text


def test_lock_promotion_is_review_only_and_never_commits_or_pushes():
    text = (ROOT / ".github/workflows/lock-promotion.yml").read_text()
    assert "uv lock" in text
    assert "npm install --package-lock-only" in text
    assert "REVIEW EVIDENCE only" in text
    assert "git push" not in text
    assert "git commit" not in text
    assert "contents: read" in text


def test_all_workflows_stay_immutably_pinned():
    result = verify_workflow_action_pins(ROOT)
    assert result["verified"], result["problems"]


def test_current_source_correctly_reports_missing_committed_locks():
    result = verify_source_locks(ROOT)
    assert not result["verified"]
    assert any(problem.startswith("uv.lock:") for problem in result["problems"])
    assert any(problem.startswith("frontend/package-lock.json:") for problem in result["problems"])
