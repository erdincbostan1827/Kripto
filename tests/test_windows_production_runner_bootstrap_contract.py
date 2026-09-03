from pathlib import Path


SCRIPT = Path("tools/bootstrap_production_acceptance_runner_windows.ps1")
RESOLVER = Path("tools/resolve_python312_windows.ps1")


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _resolver_text() -> str:
    return RESOLVER.read_text(encoding="utf-8")


def test_runner_release_is_pinned_and_checksum_verified() -> None:
    text = _text()
    assert '$RunnerVersion = "2.337.0"' in text
    assert (
        '$RunnerSha256 = "1150692afa94e71f872017e254ea55b6eece1eece3fe7e3a6d4c93d0a1b85cfc"'
        in text
    )
    assert "Get-FileHash -Algorithm SHA256" in text
    assert "checksum mismatch" in text


def test_registration_is_repo_scoped_and_fail_closed() -> None:
    text = _text()
    assert "actions/runners/registration-token" in text
    assert '"--unattended"' in text
    assert '"--replace"' in text
    assert '"--labels", "production-acceptance"' in text
    assert '"--runasservice"' in text
    assert "--no-default-labels" not in text
    assert 'throw "GitHub Actions Runner configuration failed' in text


def test_existing_runner_is_reused_instead_of_deleted_or_reconfigured() -> None:
    text = _text()
    assert "Existing runner configuration detected and will be reused" in text
    assert "Get-ExistingRunnerListener" in text
    assert "Foreground runner is already running" in text
    assert "Remove the old runner registration first" not in text
    assert "config.cmd remove" not in text
    assert "Remove-Item -Recurse" not in text


def test_python312_is_fail_closed_before_runner_use() -> None:
    text = _text()
    resolver_text = _resolver_text()
    assert "Assert-Python312" in text
    assert 'resolve_python312_windows.ps1' in text
    assert "Assert-Python312\n\n$exactSha" in text
    assert "^3\\.12\\.\\d+$" in resolver_text
    assert "Python.Python.3.12" in resolver_text
    assert "No production acceptance can proceed" in resolver_text
    assert "-AddToGitHubPath" in resolver_text


def test_protected_environment_bootstrap_does_not_embed_secret_values() -> None:
    text = _text()
    assert "environments/$EnvironmentName" in text
    assert "ACCEPTANCE_ENVIRONMENT_ID" in text
    assert "ACCEPTANCE_TOPOLOGY_HASH" in text
    assert "TopologyDescriptorPath" in text
    assert "gh secret set $name --env $EnvironmentName --repo $Repository" in text
    assert "gh secret set $name --env $EnvironmentName --repo $Repository --body" not in text


def test_real_external_gates_remain_explicit() -> None:
    text = _text()
    required = {
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "PITR_DRILL_COMMAND",
        "PITR_EVIDENCE_JSON",
        "HA_DRILL_COMMAND",
        "HA_EVIDENCE_JSON",
        "WORM_ACCEPTANCE_COMMAND",
        "WORM_EVIDENCE_JSON",
        "RESTART_DRILL_COMMAND",
        "RESTART_EVIDENCE_JSON",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    }
    for name in required:
        assert f'"{name}"' in text
    assert "No production-ready/LIVE claim is made by this bootstrap." in text
