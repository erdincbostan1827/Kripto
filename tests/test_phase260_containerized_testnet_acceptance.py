from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.release.acceptance_contract import ACCEPTANCE_PLANS  # noqa: E402
from scripts.acceptance_diagnostics import classify_blocker  # noqa: E402


def test_testnet_acceptance_runs_inside_locked_app_container_without_cli_secrets() -> None:
    key, command, requires_real = ACCEPTANCE_PLANS["testnet"][0]

    assert key == "binance_testnet"
    assert requires_real is True
    assert command[:4] == ("docker", "compose", "run", "--rm")
    assert command[-3:] == (
        "app",
        "python",
        "scripts/external/binance_testnet_acceptance_hardened.py",
    )

    expected_env_names = (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "BINANCE_TESTNET_EXECUTE",
        "BINANCE_TESTNET_SYMBOL",
        "BINANCE_TESTNET_MAX_NOTIONAL",
        "BINANCE_TESTNET_PARTIAL_PRICE",
    )
    for name in expected_env_names:
        index = command.index(name)
        assert index > 0
        assert command[index - 1] == "-e"

    joined = " ".join(command)
    assert "https://api.binance.com" not in joined
    assert "BINANCE_API_KEY=" not in joined
    assert "BINANCE_API_SECRET=" not in joined
    assert "BINANCE_TESTNET_API_KEY=" not in joined
    assert "BINANCE_TESTNET_API_SECRET=" not in joined


def test_missing_python_dependency_is_not_misclassified_as_dns() -> None:
    traceback = (
        "Traceback (most recent call last):\n"
        "  File 'scripts/external/binance_testnet_acceptance_hardened.py', line 16, in <module>\n"
        "ModuleNotFoundError: No module named 'httpx'\n"
    )

    assert classify_blocker(traceback, 1, tool="python") == "RUNTIME_DEPENDENCY_MISSING"


def test_real_dns_failure_remains_distinct_from_dependency_failure() -> None:
    assert classify_blocker("socket.gaierror: getaddrinfo failed", 1) == "NETWORK_DNS_UNAVAILABLE"
