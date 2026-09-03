from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "run_phase250_final_production_acceptance.ps1"


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_phase250_dispatches_exact_current_main_and_correlates_run_identity():
    text = _text()
    assert 'FINAL_ACCEPTANCE_REQUIRES_CURRENT_REMOTE_MAIN' in text
    assert '"workflow", "run", "production-acceptance.yml"' in text
    assert '"-f", "acceptance_ref=$CandidateRef"' in text
    assert '$expectedTitle = "Production Acceptance $CandidateRef"' in text
    assert '"databaseId,createdAt,status,conclusion,displayTitle,headSha,url"' in text
    assert '($title -eq $expectedTitle)' in text
    assert '($headSha -eq $CandidateRef)' in text
    assert 'REMOTE_MAIN_MOVED_DURING_ACCEPTANCE' in text


def test_phase250_preserves_existing_evidence_and_results():
    text = _text()
    assert 'Refusing to overwrite existing Phase 250 evidence directory' in text
    assert 'Refusing to overwrite existing Phase 250 result' in text
    assert 'Join-Path $rootOutput "run-$runId"' in text
    assert 'Remove-Item -LiteralPath $runOutput' not in text
    assert 'Remove-Item -LiteralPath $rootOutput' not in text


def test_phase250_requires_real_target_trust_and_all_external_profiles():
    text = _text()
    for profile in (
        'locks', 'runtime', 'restart-drills', 'supply-chain', 'pitr',
        'ha', 'worm', 'testnet', 'provenance', 'campaigns',
    ):
        assert f'"{profile}"' in text
    assert '$preflight.verified -ne $true' in text
    assert '$orchestration.real_target_explicitly_confirmed -ne $true' in text
    assert '$orchestration.challenge_verification.trust_verified -ne $true' in text
    assert '$orchestration.merge.selected_all_pass -ne $true' in text
    assert '$orchestration.verification.selected_all_pass -ne $true' in text
    assert '$profileProperty.Value.selected_all_pass -ne $true' in text


def test_phase250_missing_exit_codes_fail_closed_instead_of_casting_null_to_zero():
    text = _text()
    assert '$releaseManifestExit = Get-PropertyValue -Object $releaseManifestResult -Name "exit_code"' in text
    assert '$null -eq $releaseManifestExit -or [int]$releaseManifestExit -ne 0' in text
    assert '$releaseGateExit = Get-PropertyValue -Object $releaseGateResult -Name "exit_code"' in text
    assert '$null -eq $releaseGateExit -or [int]$releaseGateExit -ne 0' in text
    assert '$ledgerCheckpointExit = Get-PropertyValue -Object $ledgerCheckpointResult -Name "exit_code"' in text
    assert '$null -eq $ledgerCheckpointExit -or [int]$ledgerCheckpointExit -ne 0' in text


def test_phase250_never_enables_live_and_stops_at_human_approval_boundary():
    text = _text()
    assert 'PROD_LIVE_RELEASE=ELIGIBLE_FOR_HUMAN_APPROVAL' in text
    assert '$releaseManifest.live_enabled -ne $false' in text
    assert '$releaseManifest.default_mode -ne "PAPER"' in text
    assert 'live_enabled = $false' in text
    assert 'default_mode = "PAPER"' in text
    assert 'EligibleForHumanApproval $true' in text
    assert 'LIVE remains disabled. Separate human approval is required before any LIVE enablement.' in text
