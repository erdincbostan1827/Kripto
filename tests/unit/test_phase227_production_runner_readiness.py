from __future__ import annotations

import json
from pathlib import Path

import scripts.production_runner_readiness as readiness

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "production-runner-readiness.yml"


def _actions_env() -> dict[str, str]:
    return {
        "GITHUB_ACTIONS": "true",
        "RUNNER_NAME": "prod-runner-a",
        "RUNNER_OS": "Linux",
        "RUNNER_ARCH": "X64",
        "BINANCE_TESTNET_API_SECRET": "MUST_NOT_APPEAR",
    }


def _fake_probe(command, *, root: Path, timeout: float = 20):
    return True, f"ok:{command[0]}"


def test_verified_readiness_is_secret_free(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness, "verify_source_locks", lambda root: {"verified": True, "problems": [], "locks": {}})
    payload = readiness.run_readiness(
        tmp_path,
        env=_actions_env(),
        which=lambda tool: f"/usr/bin/{tool}",
        probe=_fake_probe,
        require_actions_context=True,
    )
    assert payload["verified"] is True
    assert payload["problems"] == []
    assert "MUST_NOT_APPEAR" not in json.dumps(payload, sort_keys=True)


def test_missing_docker_fails_closed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness, "verify_source_locks", lambda root: {"verified": True, "problems": [], "locks": {}})
    payload = readiness.run_readiness(
        tmp_path,
        env=_actions_env(),
        which=lambda tool: None if tool == "docker" else f"/usr/bin/{tool}",
        probe=_fake_probe,
        require_actions_context=True,
    )
    assert payload["verified"] is False
    assert "TOOL_AVAILABLE:docker" in payload["problems"]
    assert "DOCKER_DAEMON" in payload["problems"]
    assert "DOCKER_COMPOSE" in payload["problems"]


def test_docker_daemon_failure_is_blocking(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness, "verify_source_locks", lambda root: {"verified": True, "problems": [], "locks": {}})

    def probe(command, *, root: Path, timeout: float = 20):
        if tuple(command[:2]) == ("docker", "info"):
            return False, "daemon_unreachable"
        return True, "ok"

    payload = readiness.run_readiness(
        tmp_path,
        env=_actions_env(),
        which=lambda tool: f"/usr/bin/{tool}",
        probe=probe,
        require_actions_context=True,
    )
    assert payload["verified"] is False
    assert "DOCKER_DAEMON" in payload["problems"]


def test_missing_actions_context_fails_when_required(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness, "verify_source_locks", lambda root: {"verified": True, "problems": [], "locks": {}})
    payload = readiness.run_readiness(
        tmp_path,
        env={},
        which=lambda tool: f"/usr/bin/{tool}",
        probe=_fake_probe,
        require_actions_context=True,
    )
    assert payload["verified"] is False
    assert "GITHUB_ACTIONS_CONTEXT" in payload["problems"]
    assert "RUNNER_CONTEXT:RUNNER_NAME" in payload["problems"]


def test_source_lock_failure_is_blocking(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(readiness, "verify_source_locks", lambda root: {"verified": False, "problems": ["LOCK_MISMATCH"], "locks": {}})
    payload = readiness.run_readiness(
        tmp_path,
        env=_actions_env(),
        which=lambda tool: f"/usr/bin/{tool}",
        probe=_fake_probe,
        require_actions_context=True,
    )
    assert payload["verified"] is False
    assert "SOURCE_LOCKS_VERIFIED" in payload["problems"]
    assert payload["source_lock_problems"] == ["LOCK_MISMATCH"]


def test_workflow_is_self_hosted_secret_free_and_fail_closed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "python scripts/production_runner_readiness.py" in text
    assert "--require-actions-context" in text
    assert "if: always()" in text
    assert "PRODUCTION_RUNNER_READINESS.json" in text
    assert "secrets." not in text
    assert "continue-on-error" not in text
    assert "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683" in text
    assert "actions/setup-python@42375524e23c412d93fb67b49958b491fce71c38" in text
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in text
