from pathlib import Path


def test_phase266_wrapper_captures_native_success_without_last_exit_seed() -> None:
    text = Path("tools/run_phase266_campaign_runtime.ps1").read_text(encoding="utf-8")
    strict = text.index("Set-StrictMode -Version Latest")
    git_capture = text.index("$gitSucceeded = $?")
    runtime_capture = text.index("$runtimeSucceeded = $?")
    assert "$LASTEXITCODE = 0" not in text
    assert strict < git_capture < runtime_capture
    assert "if (-not $gitSucceeded" in text
    assert "if (-not $runtimeSucceeded)" in text


def test_phase266_wrapper_remains_live_disabled_and_fail_closed() -> None:
    text = Path("tools/run_phase266_campaign_runtime.ps1").read_text(encoding="utf-8")
    assert "LIVE remains disabled" in text
    assert "real-order command" in text
    assert "PHASE266_LOCAL_HEAD_NOT_CANDIDATE" in text
    assert "PHASE266_PROTECTED_CAMPAIGN_RUNTIME=FAIL" in text
