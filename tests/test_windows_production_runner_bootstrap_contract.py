from pathlib import Path


SCRIPT = Path("tools/bootstrap_production_acceptance_runner_windows.ps1")


def _text() -> str:
    return SCRIPT.read_text(encoding="utf-8")


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
    assert 'actions/runners/registration-token' in text
    assert '"--unattended"' in text
    assert '"--replace"' in text
    assert '"--labels", "production-acceptance"' in text
    assert '"--runasservice"' in text
    assert "--no-default-labels" not in text
    assert "throw \"GitHub Actions Runner configuration failed" in text


def test_protected_environment_bootstrap_does_not_embed_secret_values() -> None:
    text = _text()
    assert 'environments/$EnvironmentName' in text
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
