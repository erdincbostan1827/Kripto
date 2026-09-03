from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase241-restart-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase241_restart_acceptance.ps1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase241_workflow_is_exact_sha_runtime_plus_restart_and_fail_closed() -> None:
    text = _text(WORKFLOW)

    assert "name: Phase 241 Restart Acceptance" in text
    assert "run-name: Phase 241 Restart Acceptance ${{ inputs.candidate_ref }}" in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "candidate_ref must be an exact 40-character commit SHA" in text
    assert "python scripts/verify_source_locks.py" in text

    assert "ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: '1'" in text
    assert "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND: ${{ secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND }}" in text
    assert "RESTART_DRILL_COMMAND: ${{ secrets.RESTART_DRILL_COMMAND }}" in text
    assert "RESTART_EVIDENCE_JSON: ${{ secrets.RESTART_EVIDENCE_JSON }}" in text
    assert "python scripts/generate_acceptance_challenge.py" in text
    assert "--profile runtime --confirm-real-target" in text
    assert "--profile restart-drills --confirm-real-target" in text
    assert text.index("--profile runtime --confirm-real-target") < text.index("--profile restart-drills --confirm-real-target")

    assert "manifest_runtime.json" in text
    assert "manifest_restart-drills.json" in text
    assert "restart_drills" in text
    assert "phase241-restart-acceptance-${{ inputs.candidate_ref }}" in text
    assert "production_ready = $false" in text
    assert "It does not authorize LIVE trading" in text


def test_phase241_workflow_secret_scope_is_restart_only() -> None:
    text = _text(WORKFLOW)
    required = {
        "secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
        "secrets.RESTART_DRILL_COMMAND",
        "secrets.RESTART_EVIDENCE_JSON",
    }
    for marker in required:
        assert marker in text

    forbidden = (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "PITR_DRILL_COMMAND",
        "PITR_EVIDENCE_JSON",
        "HA_DRILL_COMMAND",
        "HA_EVIDENCE_JSON",
        "WORM_ACCEPTANCE_COMMAND",
        "WORM_EVIDENCE_JSON",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    )
    for marker in forbidden:
        assert marker not in text


def test_phase241_workflow_is_windows_native_and_isolated() -> None:
    text = _text(WORKFLOW)

    assert "shell: pwsh" in text
    assert "shell: bash" not in text
    assert "reports/external_acceptance/phase241_runtime.env" in text
    assert "Copy-Item -LiteralPath '.env.example' -Destination $runtimeEnv -Force" in text
    assert "Pre-existing secrets directory detected after clean checkout" in text
    assert "python scripts/bootstrap_secrets.py" in text
    assert '"kripto_phase241_$shortSha"' in text
    assert "$env:COMPOSE_PROJECT_NAME = $projectName" in text
    assert "$env:APP_ENV_FILE = 'reports/external_acceptance/phase241_runtime.env'" in text
    assert "ACCEPTANCE_ENVIRONMENT_ID" in text
    assert "ACCEPTANCE_TOPOLOGY_HASH" in text
    assert "docker compose down -v --remove-orphans" in text
    assert "Remove-Item -LiteralPath 'secrets' -Recurse -Force" in text


def test_phase241_orchestrator_correlates_exact_run_and_verifies_both_manifests() -> None:
    text = _text(ORCHESTRATOR)

    assert "CandidateRef -notmatch '^[0-9a-fA-F]{40}$'" in text
    assert '$expectedRunTitle = "Phase 241 Restart Acceptance $CandidateRef"' in text
    assert '"--json", "databaseId,createdAt,status,conclusion,displayTitle"' in text
    assert '($displayTitle -eq $expectedRunTitle)' in text
    assert '"workflow", "run", "Phase 241 Restart Acceptance"' in text
    assert '"-f", "candidate_ref=$CandidateRef"' in text
    assert '& gh run watch $runId --repo $Repository --exit-status' in text
    assert '$artifactName = "phase241-restart-acceptance-$CandidateRef"' in text
    assert '"PHASE241_RESTART_RESULT.json"' in text
    assert '"manifest_runtime.json"' in text
    assert '"manifest_restart-drills.json"' in text
    assert '$runtime.profile -ne "runtime"' in text
    assert '$restart.profile -ne "restart-drills"' in text
    assert '$runtime.environment.git_commit_sha -ne $CandidateRef' in text
    assert '$manifest.environment.git_commit_sha -ne $CandidateRef' in text
    assert '$runtime.challenge.verified -eq $true' in text
    assert '$restart.challenge.verified -eq $true' in text
    assert '$runtime.challenge.trust_verified -eq $true' in text
    assert '$restart.challenge.trust_verified -eq $true' in text
    assert '$runtimeStatus -eq "PASS"' in text
    assert '$restartStatus -eq "PASS"' in text
    assert 'PHASE241_RESTART_ACCEPTANCE=PASS' in text
    assert 'PHASE241_RESTART_ACCEPTANCE=FAIL' in text
    assert 'production_ready = $false' in text
