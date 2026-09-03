from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase238-runtime-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase238_runtime_acceptance.ps1"
COMPOSE = ROOT / "docker-compose.yml"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase238_workflow_is_exact_sha_runtime_only_and_fail_closed() -> None:
    text = _text(WORKFLOW)

    assert "name: Phase 238 Runtime Acceptance" in text
    assert "run-name: Phase 238 Runtime Acceptance ${{ inputs.candidate_ref }}" in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "python-version: ${{ env.PYTHON_VERSION }}" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "candidate_ref must be an exact 40-character commit SHA" in text
    assert "python scripts/verify_source_locks.py" in text

    assert "ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: '1'" in text
    assert "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND: ${{ secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND }}" in text
    assert "python scripts/generate_acceptance_challenge.py" in text
    assert "--profile runtime --confirm-real-target" in text
    assert "challengeTrustVerified" in text
    assert "challenge_trust_verified" in text

    assert "phase238-runtime-acceptance-${{ inputs.candidate_ref }}" in text
    assert "production_ready = $false" in text
    assert "It does not authorize LIVE trading" in text

    unrelated_external_gates = (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "PITR_DRILL_COMMAND",
        "HA_FAILOVER_COMMAND",
        "WORM_STORAGE_COMMAND",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    )
    for forbidden in unrelated_external_gates:
        assert forbidden not in text


def test_phase238_workflow_uses_isolated_runtime_inputs_without_source_dirty_env() -> None:
    text = _text(WORKFLOW)

    assert "reports/external_acceptance/runtime.env" in text
    assert "Copy-Item -LiteralPath '.env.example' -Destination $runtimeEnv -Force" in text
    assert "Pre-existing secrets directory detected after clean checkout" in text
    assert "python scripts/bootstrap_secrets.py" in text
    assert 'COMPOSE_PROJECT_NAME = $projectName' not in text  # env assignment must use process env + GITHUB_ENV
    assert "$env:COMPOSE_PROJECT_NAME = $projectName" in text
    assert "$env:APP_ENV_FILE = 'reports/external_acceptance/runtime.env'" in text
    assert "docker compose config" in text
    assert "ACCEPTANCE_TOPOLOGY_HASH" in text
    assert "docker compose down -v --remove-orphans" in text
    assert "Remove-Item -LiteralPath 'secrets' -Recurse -Force" in text
    assert "cp .env.example .env" not in text


def test_compose_defaults_to_dotenv_but_allows_report_scoped_acceptance_env() -> None:
    text = _text(COMPOSE)

    marker = "env_file: [${APP_ENV_FILE:-.env}]"
    assert text.count(marker) == 2
    assert "env_file: [.env]" not in text


def test_phase238_orchestrator_correlates_exact_candidate_and_verifies_artifact() -> None:
    text = _text(ORCHESTRATOR)

    assert "CandidateRef -notmatch '^[0-9a-fA-F]{40}$'" in text
    assert '$expectedRunTitle = "Phase 238 Runtime Acceptance $CandidateRef"' in text
    assert '"--json", "databaseId,createdAt,status,conclusion,displayTitle"' in text
    assert '($displayTitle -eq $expectedRunTitle)' in text
    assert '"workflow", "run", "Phase 238 Runtime Acceptance"' in text
    assert '"-f", "candidate_ref=$CandidateRef"' in text
    assert '& gh run watch $runId --repo $Repository --exit-status' in text
    assert '$artifactName = "phase238-runtime-acceptance-$CandidateRef"' in text
    assert '"PHASE238_RUNTIME_RESULT.json"' in text
    assert '"manifest_runtime.json"' in text
    assert '$manifest.profile -ne "runtime"' in text
    assert '$manifest.environment.git_commit_sha -ne $CandidateRef' in text
    assert '$manifest.challenge.verified -eq $true' in text
    assert '$manifest.challenge.trust_verified -eq $true' in text
    assert '$manifest.selected_all_pass -eq $true' in text
    assert '$runtimeStatus -eq "PASS"' in text
    assert 'PHASE238_RUNTIME_ACCEPTANCE=PASS' in text
    assert 'PHASE238_RUNTIME_ACCEPTANCE=FAIL' in text
    assert 'production_ready = $false' in text
