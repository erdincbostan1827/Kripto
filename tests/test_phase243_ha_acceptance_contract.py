from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase243-ha-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase243_ha_acceptance.ps1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase243_workflow_is_exact_sha_runtime_plus_ha_and_fail_closed() -> None:
    text = _text(WORKFLOW)
    assert "name: Phase 243 HA Acceptance" in text
    assert "run-name: Phase 243 HA Acceptance ${{ inputs.candidate_ref }}" in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "candidate_ref must be an exact 40-character commit SHA" in text
    assert "python scripts/verify_source_locks.py" in text
    assert "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND: ${{ secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND }}" in text
    assert "HA_DRILL_COMMAND: ${{ secrets.HA_DRILL_COMMAND }}" in text
    assert "HA_EVIDENCE_JSON: ${{ secrets.HA_EVIDENCE_JSON }}" in text
    assert "python scripts/generate_acceptance_challenge.py" in text
    assert "--profile runtime --confirm-real-target" in text
    assert "--profile ha --confirm-real-target" in text
    assert text.index("--profile runtime --confirm-real-target") < text.index("--profile ha --confirm-real-target")
    assert "manifest_runtime.json" in text
    assert "manifest_ha.json" in text
    assert "HA_TARGET_IDENTITY.json" in text
    assert "phase243-ha-acceptance-${{ inputs.candidate_ref }}" in text
    assert "production_ready = $false" in text
    assert "It does not authorize LIVE trading" in text


def test_phase243_workflow_secret_scope_is_ha_only() -> None:
    text = _text(WORKFLOW)
    for marker in (
        "secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
        "secrets.HA_DRILL_COMMAND",
        "secrets.HA_EVIDENCE_JSON",
    ):
        assert marker in text
    for marker in (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "RESTART_DRILL_COMMAND",
        "RESTART_EVIDENCE_JSON",
        "PITR_DRILL_COMMAND",
        "PITR_EVIDENCE_JSON",
        "WORM_ACCEPTANCE_COMMAND",
        "WORM_EVIDENCE_JSON",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    ):
        assert marker not in text


def test_phase243_workflow_is_windows_native_and_isolated() -> None:
    text = _text(WORKFLOW)
    assert "shell: pwsh" in text
    assert "shell: bash" not in text
    assert "reports/external_acceptance/phase243_runtime.env" in text
    assert "Copy-Item -LiteralPath '.env.example' -Destination $runtimeEnv -Force" in text
    assert "Pre-existing secrets directory detected after clean checkout" in text
    assert "python scripts/bootstrap_secrets.py" in text
    assert '"kripto_phase243_$shortSha"' in text
    assert "$env:COMPOSE_PROJECT_NAME = $projectName" in text
    assert "$env:APP_ENV_FILE = 'reports/external_acceptance/phase243_runtime.env'" in text
    assert "ACCEPTANCE_ENVIRONMENT_ID" in text
    assert "ACCEPTANCE_TOPOLOGY_HASH" in text
    assert "runner_os = $env:RUNNER_OS" in text
    assert "topology_hash = $topologyHash" in text
    assert "docker compose down -v --remove-orphans" in text
    assert "Remove-Item -LiteralPath 'secrets' -Recurse -Force" in text


def test_phase243_orchestrator_correlates_exact_run_and_verifies_both_manifests() -> None:
    text = _text(ORCHESTRATOR)
    assert "CandidateRef -notmatch '^[0-9a-fA-F]{40}$'" in text
    assert '$expectedRunTitle = "Phase 243 HA Acceptance $CandidateRef"' in text
    assert '"databaseId,createdAt,status,conclusion,displayTitle"' in text
    assert '($displayTitle -eq $expectedRunTitle)' in text
    assert '"workflow", "run", "Phase 243 HA Acceptance"' in text
    assert '"candidate_ref=$CandidateRef"' in text
    assert '& gh run watch $runId --repo $Repository --exit-status' in text
    assert '$artifactName = "phase243-ha-acceptance-$CandidateRef"' in text
    assert '"PHASE243_HA_RESULT.json"' in text
    assert '"HA_TARGET_IDENTITY.json"' in text
    assert '"manifest_runtime.json"' in text
    assert '"manifest_ha.json"' in text
    assert '$identity.classification -ne "PHASE243_HA_TARGET_IDENTITY_NOT_ACCEPTANCE_EVIDENCE"' in text
    assert '$identity.candidate_sha -ne $CandidateRef' in text
    assert '$identity.runner_os -ne "Windows"' in text
    assert '$manifest.environment.git_commit_sha -ne $CandidateRef' in text
    assert '$manifest.environment.topology_hash -ne $identity.topology_hash' in text
    assert '$runtime.profile -ne "runtime"' in text
    assert '$ha.profile -ne "ha"' in text
    assert '$workflowResult.candidate_sha -ne $CandidateRef' in text
    assert '$runtime.challenge.verified -eq $true' in text
    assert '$ha.challenge.verified -eq $true' in text
    assert '$runtime.challenge.trust_verified -eq $true' in text
    assert '$ha.challenge.trust_verified -eq $true' in text
    assert '$runtimeStatus -eq "PASS"' in text
    assert '$haStatus -eq "PASS"' in text
    assert "PHASE243_HA_ACCEPTANCE=PASS" in text
    assert "PHASE243_HA_ACCEPTANCE=FAIL" in text
    assert "production_ready = $false" in text
