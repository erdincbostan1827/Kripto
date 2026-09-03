from pathlib import Path


SCRIPT = Path("tools/run_phase231_production_readiness.ps1")


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_phase231_orchestrator_is_fail_closed_and_exact_sha_bound() -> None:
    text = _text()
    assert "Set-StrictMode -Version Latest" in text
    assert "$ErrorActionPreference = \"Stop\"" in text
    assert "^[0-9a-fA-F]{40}$" in text
    assert "candidate_ref=$CandidateRef" in text
    assert "production-runner-readiness-$CandidateRef" in text
    assert "$report.checks.GIT_HEAD.detail -ne $CandidateRef" in text


def test_phase231_orchestrator_requires_pinned_python_and_windows_runner() -> None:
    text = _text()
    assert "resolve_python312_windows.ps1" in text
    assert "Pinned Python 3.12.10 resolver failed" in text
    assert '$report.runner_context.os -ne "Windows"' in text


def test_phase231_orchestrator_never_claims_production_ready() -> None:
    text = _text()
    assert "production_ready = $false" in text
    assert "No production-ready/LIVE claim is made by this phase." in text
    assert "Readiness PASS proves runner prerequisites only" in text


def test_phase231_orchestrator_waits_for_workflow_exit_status() -> None:
    text = _text()
    assert "gh run watch $runId --repo $Repository --exit-status" in text
    assert "Production Runner Readiness workflow did not PASS" in text
    assert "PHASE231_READINESS=PASS" in text
    assert "PHASE231_READINESS=FAIL" in text
