from pathlib import Path


SCRIPT = Path("tools/run_phase231_production_readiness.ps1")
WORKFLOW = Path(".github/workflows/production-runner-readiness.yml")


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


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


def test_phase231_orchestrator_handles_windows_powershell_json_arrays_safely() -> None:
    text = _text()
    assert "$parsedRuns = $json | ConvertFrom-Json" in text
    assert "$parsedRuns -is [System.Array]" in text
    assert '$Run.PSObject.Properties["createdAt"]' in text
    assert '$candidateRuns[0].PSObject.Properties["databaseId"]' in text
    assert "[DateTimeOffset]$_.createdAt" not in text


def test_readiness_workflow_captures_identity_with_windows_native_shell() -> None:
    text = _workflow_text()
    identity_section = text.split("- name: Capture exact candidate identity", 1)[1].split(
        "- name: Prepare compose environment without production credentials", 1
    )[0]
    assert "shell: powershell" in identity_section
    assert "git rev-parse HEAD" in identity_section
    assert "Checked-out candidate SHA mismatch" in identity_section
    assert "$env:GITHUB_OUTPUT" in identity_section
    assert "shell: bash" not in identity_section


def test_readiness_workflow_prepares_compose_env_with_windows_native_shell() -> None:
    text = _workflow_text()
    prepare_section = text.split(
        "- name: Prepare compose environment without production credentials", 1
    )[1].split("- name: Secret-free production runner readiness", 1)[0]
    assert "shell: powershell" in prepare_section
    assert 'Test-Path -LiteralPath ".env.example" -PathType Leaf' in prepare_section
    assert 'Copy-Item -LiteralPath ".env.example" -Destination ".env" -Force' in prepare_section
    assert 'Test-Path -LiteralPath ".env" -PathType Leaf' in prepare_section
    assert "shell: bash" not in prepare_section
    assert "cp .env.example .env" not in prepare_section


def test_readiness_workflow_has_no_bash_dependency_on_windows_runner() -> None:
    text = _workflow_text()
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "shell: bash" not in text
