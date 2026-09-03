from pathlib import Path


BOOTSTRAP = Path("tools/bootstrap_production_acceptance_runner_windows.ps1")
RESOLVER = Path("tools/resolve_python312_windows.ps1")
READINESS = Path(".github/workflows/production-runner-readiness.yml")
PRODUCTION_ACCEPTANCE = Path(".github/workflows/production-acceptance.yml")


def test_bootstrap_provisions_exact_python_to_runner_tool_cache() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    assert '$PinnedPythonVersion = "3.12.10"' in text
    assert "Provision-PythonToolCache" in text
    assert 'Python\\$PinnedPythonVersion' in text
    assert 'x64.complete' in text
    assert "Copied CPython $PinnedPythonVersion tool-cache runtime does not provide pip" in text


def test_resolver_requires_exact_version_x64_and_pip() -> None:
    text = RESOLVER.read_text(encoding="utf-8")
    assert "$RequiredPythonVersion = '3.12.10'" in text
    assert "$RequiredPointerBits = 64" in text
    assert "struct.calcsize('P') * 8" in text
    assert "pip is unavailable" in text
    assert "No production acceptance can proceed" in text


def test_readiness_uses_exact_cached_python() -> None:
    text = READINESS.read_text(encoding="utf-8")
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "Setup pinned Python from runner tool cache" in text
    assert "RUNNER_TOOL_CACHE" in text
    assert "actions/setup-python@42375524e23c412d93fb67b49958b491fce71c38" in text


def test_production_acceptance_still_targets_self_hosted_gate() -> None:
    text = PRODUCTION_ACCEPTANCE.read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "python-version: ${{ env.PYTHON_VERSION }}" in text
