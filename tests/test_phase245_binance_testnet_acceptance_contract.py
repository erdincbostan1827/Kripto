from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase245-binance-testnet-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase245_binance_testnet_acceptance.ps1"
TESTNET_SCRIPT = ROOT / "scripts" / "external" / "binance_testnet_acceptance.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase245_workflow_is_exact_sha_credentialed_testnet_and_fail_closed() -> None:
    text = _text(WORKFLOW)
    assert "name: Phase 245 Binance TESTNET Acceptance" in text
    assert "run-name: Phase 245 Binance TESTNET Acceptance ${{ inputs.candidate_ref }}" in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "candidate_ref must be an exact 40-character commit SHA" in text
    assert "python scripts/verify_source_locks.py" in text
    assert "ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: '1'" in text
    assert "BINANCE_TESTNET_EXECUTE: 'YES'" in text
    assert "BINANCE_TESTNET_MAX_NOTIONAL must be >0 and <=15" in text
    assert "python scripts/generate_acceptance_challenge.py" in text
    assert "--profile runtime --confirm-real-target" in text
    assert "--profile testnet --confirm-real-target" in text
    assert text.index("--profile runtime --confirm-real-target") < text.index("--profile testnet --confirm-real-target")
    assert "manifest_runtime.json" in text
    assert "manifest_testnet.json" in text
    assert "BINANCE_TESTNET_TARGET_IDENTITY.json" in text
    assert "https://testnet.binance.vision" in text
    assert "PRESENT_REDACTED" in text
    assert "market_order_pass" in text
    assert "limit_order_pass" in text
    assert "cancel_pass" in text
    assert "partial_fill_pass" in text
    assert "production_ready = $false" in text
    assert "live_enabled = $false" in text
    assert "does not authorize real-money LIVE trading" in text


def test_phase245_workflow_secret_scope_is_testnet_only() -> None:
    text = _text(WORKFLOW)
    for marker in (
        "secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
        "secrets.BINANCE_TESTNET_API_KEY",
        "secrets.BINANCE_TESTNET_API_SECRET",
    ):
        assert marker in text
    for marker in (
        "RESTART_DRILL_COMMAND",
        "RESTART_EVIDENCE_JSON",
        "PITR_DRILL_COMMAND",
        "PITR_EVIDENCE_JSON",
        "HA_DRILL_COMMAND",
        "HA_EVIDENCE_JSON",
        "WORM_ACCEPTANCE_COMMAND",
        "WORM_EVIDENCE_JSON",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    ):
        assert marker not in text


def test_phase245_workflow_is_windows_native_isolated_and_redaction_safe() -> None:
    text = _text(WORKFLOW)
    assert "shell: pwsh" in text
    assert "shell: bash" not in text
    assert "reports/external_acceptance/phase245_runtime.env" in text
    assert "Copy-Item -LiteralPath '.env.example' -Destination $runtimeEnv -Force" in text
    assert "Pre-existing secrets directory detected after clean checkout" in text
    assert "python scripts/bootstrap_secrets.py" in text
    assert '"kripto_phase245_$shortSha"' in text
    assert "$env:COMPOSE_PROJECT_NAME = $projectName" in text
    assert "$env:APP_ENV_FILE = 'reports/external_acceptance/phase245_runtime.env'" in text
    assert "ACCEPTANCE_ENVIRONMENT_ID" in text
    assert "ACCEPTANCE_TOPOLOGY_HASH" in text
    assert "runner_os = $env:RUNNER_OS" in text
    assert "topology_hash = $topologyHash" in text
    assert "docker compose down -v --remove-orphans" in text
    assert "Remove-Item -LiteralPath 'secrets' -Recurse -Force" in text
    assert "BINANCE_TESTNET_API_KEY" not in text.split("$identity = [ordered]@{", 1)[1]
    assert "BINANCE_TESTNET_API_SECRET" not in text.split("$identity = [ordered]@{", 1)[1]


def test_phase245_orchestrator_correlates_exact_run_and_verifies_testnet_scenario() -> None:
    text = _text(ORCHESTRATOR)
    assert "CandidateRef -notmatch '^[0-9a-fA-F]{40}$'" in text
    assert '$expectedRunTitle = "Phase 245 Binance TESTNET Acceptance $CandidateRef"' in text
    assert '"databaseId,createdAt,status,conclusion,displayTitle"' in text
    assert '($displayTitle -eq $expectedRunTitle)' in text
    assert '"workflow", "run", "Phase 245 Binance TESTNET Acceptance"' in text
    assert '"candidate_ref=$CandidateRef"' in text
    assert '"symbol=$Symbol"' in text
    assert '"max_notional=$maxNotionalText"' in text
    assert '"partial_price=$partialPriceText"' in text
    assert '& gh run watch $runId --repo $Repository --exit-status' in text
    assert '$artifactName = "phase245-binance-testnet-acceptance-$CandidateRef"' in text
    assert '"PHASE245_BINANCE_TESTNET_RESULT.json"' in text
    assert '"BINANCE_TESTNET_TARGET_IDENTITY.json"' in text
    assert '"manifest_runtime.json"' in text
    assert '"manifest_testnet.json"' in text
    assert '"binance_testnet.log"' in text
    assert '$identity.runner_os -ne "Windows"' in text
    assert '$identity.exchange_endpoint -ne "https://testnet.binance.vision"' in text
    assert '$manifest.environment.git_commit_sha -ne $CandidateRef' in text
    assert '$manifest.environment.topology_hash -ne $identity.topology_hash' in text
    assert '$testnet.credentials.binance_testnet -ne "PRESENT_REDACTED"' in text
    assert '$scenario.endpoint -ne "https://testnet.binance.vision"' in text
    assert '$scenario.checks.market_order.pass -eq $true' in text
    assert '$scenario.checks.limit_order.pass -eq $true' in text
    assert '$scenario.checks.cancel.pass -eq $true' in text
    assert '$scenario.checks.partial_fill.pass -eq $true' in text
    assert "PHASE245_BINANCE_TESTNET_ACCEPTANCE=PASS" in text
    assert "PHASE245_BINANCE_TESTNET_ACCEPTANCE=FAIL" in text
    assert "production_ready = $false" in text
    assert "live_enabled = $false" in text


def test_binance_acceptance_script_is_hard_pinned_to_spot_testnet() -> None:
    text = _text(TESTNET_SCRIPT)
    assert 'TESTNET_URL = "https://testnet.binance.vision"' in text
    assert 'if not adapter.testnet or adapter.base_url.rstrip("/") != TESTNET_URL:' in text
    assert 'raise RuntimeError("refusing to execute: adapter is not pinned to Binance Spot TESTNET")' in text
    assert 'if os.getenv("BINANCE_TESTNET_EXECUTE") != "YES":' in text
    assert 'max_notional = Decimal(os.getenv("BINANCE_TESTNET_MAX_NOTIONAL", "15"))' in text
    assert 'auto_select_symbol = symbol_raw == AUTO_VALUE' in text
    assert 'partial_raw is not None and partial_raw.strip().upper() == AUTO_VALUE' in text
    assert 'if auto_partial_price or not partial_raw' in text
    assert 'else Decimal(partial_raw)' in text
    assert 'adapter = BinanceSpotAdapter(api_key=key, api_secret=secret, testnet=True)' in text
    assert 'result["all_pass"] = bool(market_ok and limit_ok and cancel_ok and partial_ok)' in text
