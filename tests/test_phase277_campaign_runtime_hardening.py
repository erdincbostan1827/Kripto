from pathlib import Path


WRAPPER = Path("tools/run_phase266_campaign_runtime.ps1")


def test_phase266_wrapper_never_seeds_last_exit_code() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    assert "$LASTEXITCODE = 0" not in source
    assert "$runtimeSucceeded = $?" in source
    assert "if (-not $runtimeSucceeded)" in source
    assert "PHASE266_PROTECTED_CAMPAIGN_RUNTIME=FAIL" in source


def test_phase266_wrapper_binds_real_github_runner_identity() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    assert "$env:RUNNER_NAME" in source
    assert "$env:RUNNER_OS" in source
    assert "$env:RUNNER_ARCH" in source
    assert "github-actions:{0}:{1}:{2}:phase266-protected-campaign" in source
    assert "Protected GitHub runner identity components are incomplete" in source
    assert '"github-actions:$env:RUNNER_NAME:$env:RUNNER_OS:$env:RUNNER_ARCH:phase266-protected-campaign"' not in source


def test_phase266_git_checks_capture_native_success_immediately() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    assert "$gitSucceeded = $?" in source
    assert "$repoRootResolved = $?" in source
    assert "if (-not $gitSucceeded" in source
    assert "if (-not $repoRootResolved" in source
