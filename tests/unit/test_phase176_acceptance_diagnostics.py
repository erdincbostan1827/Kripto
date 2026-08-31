from __future__ import annotations

import subprocess
from pathlib import Path

import scripts.external_acceptance_runner as runner
from scripts.acceptance_diagnostics import classify_blocker, redact_text
from scripts.bootstrap_dependency_locks import _run as lock_run


def test_phase176_redacts_known_env_credentials_and_common_auth_syntax():
    env = {
        "BINANCE_TESTNET_API_KEY": "super-secret-key-123",
        "OTHER": "not-secret",
    }
    text = (
        "key=super-secret-key-123 Authorization: Bearer abcdefghijklmnop "
        "https://alice:password123@example.test/path?api_key=qwertyuiop"
    )
    safe = redact_text(text, env)
    assert "super-secret-key-123" not in safe
    assert "abcdefghijklmnop" not in safe
    assert "password123" not in safe
    assert "qwertyuiop" not in safe
    assert safe.count("[REDACTED]") >= 4


def test_phase176_blocker_taxonomy_is_specific_and_never_copies_output():
    cases = {
        "Could not resolve host: registry.example": "NETWORK_DNS_UNAVAILABLE",
        "package not found in cache while offline mode enabled": "OFFLINE_CACHE_INCOMPLETE",
        "npm error code ENOTCACHED; no cached response is available": "OFFLINE_CACHE_INCOMPLETE",
        "alembic was not found in the cache because the network was disabled": "OFFLINE_CACHE_INCOMPLETE",
        "HTTP 401 Unauthorized token=abcdefghi": "AUTHENTICATION_FAILED",
        "HTTP 403 Forbidden": "AUTHORIZATION_FAILED",
        "Permission denied": "PERMISSION_DENIED",
        "Connection refused": "NETWORK_ENDPOINT_UNAVAILABLE",
        "Cannot connect to the Docker daemon": "CONTAINER_RUNTIME_UNAVAILABLE",
        "No such file or directory": "REQUIRED_FILE_MISSING",
    }
    for output, expected in cases.items():
        blocker = classify_blocker(output, 1, tool="tool")
        assert blocker == expected
        assert output not in blocker
    assert classify_blocker("unknown failure", 7, tool="tool") == "EXIT_CODE:7"


def test_phase176_external_runner_redacts_logs_and_classifies_nonzero(monkeypatch, tmp_path: Path):
    secret = "credential-value-987654"
    monkeypatch.setenv("SERVICE_TOKEN", secret)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner.shutil, "which", lambda _: "/usr/bin/fake")
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a[0], 1, f"Could not resolve host registry; token={secret}\n"),
    )
    ev = runner._run("diagnostic", ["fake", "arg"], real_system=True, run_dir=tmp_path)
    log = (tmp_path / "diagnostic.log").read_text(encoding="utf-8")
    assert ev.status == "BLOCKED"
    assert ev.blocker == "NETWORK_DNS_UNAVAILABLE"
    assert secret not in log
    assert "[REDACTED]" in log


def test_phase176_dependency_lock_runner_redacts_and_classifies(monkeypatch, tmp_path: Path):
    secret = "npm-secret-abcdef"
    monkeypatch.setenv("NPM_TOKEN", secret)
    monkeypatch.setattr("scripts.bootstrap_dependency_locks.shutil.which", lambda _: "/usr/bin/npm")

    class FakeProc:
        returncode = 1
        pid = 12345
        def communicate(self, timeout=None):
            return (f"offline cache miss; token={secret}", None)
        def poll(self):
            return self.returncode

    monkeypatch.setattr("scripts.bootstrap_dependency_locks.subprocess.Popen", lambda *a, **k: FakeProc())
    result = lock_run(["npm", "install"], tmp_path, offline=False)
    assert result["blocker"] == "OFFLINE_CACHE_INCOMPLETE"
    assert secret not in result["output"]
    assert result["process_tree_terminated"] is False
