from pathlib import Path


def test_phase266_wrapper_initializes_global_last_exit_code_before_native_checks() -> None:
    text = Path("tools/run_phase266_campaign_runtime.ps1").read_text(encoding="utf-8")
    strict = text.index("Set-StrictMode -Version Latest")
    seed = text.index("$global:LASTEXITCODE = 0")
    first_check = text.index("if ($LASTEXITCODE -ne 0")
    assert strict < seed < first_check
    assert "\n$LASTEXITCODE = 0\n" not in text


def test_phase266_wrapper_snapshots_native_exit_before_reporting_pass() -> None:
    text = Path("tools/run_phase266_campaign_runtime.ps1").read_text(encoding="utf-8")
    invoke = text.index("& $venvPython @arguments")
    snapshot = text.index("$nativeExitCode = $LASTEXITCODE")
    fail = text.index("PHASE266_PROTECTED_CAMPAIGN_RUNTIME=FAIL")
    passed = text.index("PHASE266_PROTECTED_CAMPAIGN_RUNTIME=PASS")
    assert invoke < snapshot < fail < passed
    assert "if ($nativeExitCode -ne 0)" in text


def test_phase266_wrapper_remains_live_disabled_and_fail_closed() -> None:
    text = Path("tools/run_phase266_campaign_runtime.ps1").read_text(encoding="utf-8")
    assert "LIVE remains disabled" in text
    assert "real-order command" in text
    assert "PHASE266_LOCAL_HEAD_NOT_CANDIDATE" in text
    assert "PHASE266_PROTECTED_CAMPAIGN_RUNTIME=FAIL" in text
