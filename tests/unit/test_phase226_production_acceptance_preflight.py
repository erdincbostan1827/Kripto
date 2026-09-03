from __future__ import annotations

import json
from pathlib import Path

import scripts.production_acceptance_preflight as preflight

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "production-acceptance.yml"


def _valid_env() -> dict[str, str]:
    sha = "a" * 40
    digest = "ghcr.io/owner/repo/acceptance@sha256:" + "b" * 64
    env = {
        "GITHUB_REPOSITORY": "owner/repo",
        "GITHUB_RUN_ID": "12345",
        "GITHUB_WORKFLOW_REF": "owner/repo/.github/workflows/production-acceptance.yml@refs/heads/main",
        "EXPECTED_ACCEPTANCE_SHA": sha,
        "CI_COMMIT_SHA": sha,
        "ACCEPTANCE_CONTAINER_IMAGE": f"ghcr.io/owner/repo/acceptance:{sha}",
        "EXPECTED_CONTAINER_DIGEST": digest,
        "ACCEPTANCE_ENVIRONMENT_ID": "prod-acceptance-runner-a",
        "ACCEPTANCE_TOPOLOGY_HASH": "c" * 64,
        "ACCEPTANCE_REQUIRE_CHALLENGE_TRUST": "1",
        "BINANCE_TESTNET_EXECUTE": "YES",
    }
    for name in preflight.SECRET_ENV_NAMES:
        env[name] = "SUPER_SECRET_SENTINEL"
    return env


def _prepare_receipt(root: Path, env: dict[str, str]) -> None:
    path = root / "reports" / "CI_CONTAINER_REPODIGEST_VERIFIED.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(env["EXPECTED_CONTAINER_DIGEST"] + "\n", encoding="utf-8")


def test_valid_preflight_is_verified_without_serializing_secrets(tmp_path: Path, monkeypatch):
    env = _valid_env()
    _prepare_receipt(tmp_path, env)
    monkeypatch.setattr(preflight, "_git_sha", lambda root: env["EXPECTED_ACCEPTANCE_SHA"])
    payload = preflight.run_preflight(tmp_path, env=env, which=lambda tool: f"/tools/{tool}")
    assert payload["verified"] is True
    assert payload["problems"] == []
    assert payload["secret_values_serialized"] is False
    assert "SUPER_SECRET_SENTINEL" not in json.dumps(payload, sort_keys=True)


def test_missing_secret_fails_closed_and_remains_redacted(tmp_path: Path, monkeypatch):
    env = _valid_env()
    env["BINANCE_TESTNET_API_SECRET"] = ""
    _prepare_receipt(tmp_path, env)
    monkeypatch.setattr(preflight, "_git_sha", lambda root: env["EXPECTED_ACCEPTANCE_SHA"])
    payload = preflight.run_preflight(tmp_path, env=env, which=lambda tool: f"/tools/{tool}")
    assert payload["verified"] is False
    assert "SECRET_PRESENT:BINANCE_TESTNET_API_SECRET" in payload["problems"]
    assert "SUPER_SECRET_SENTINEL" not in json.dumps(payload, sort_keys=True)


def test_candidate_sha_mismatch_fails_closed(tmp_path: Path, monkeypatch):
    env = _valid_env()
    _prepare_receipt(tmp_path, env)
    monkeypatch.setattr(preflight, "_git_sha", lambda root: "d" * 40)
    payload = preflight.run_preflight(tmp_path, env=env, which=lambda tool: f"/tools/{tool}")
    assert payload["verified"] is False
    assert "GIT_SHA_MATCHES_EXPECTED" in payload["problems"]


def test_invalid_topology_and_digest_receipt_fail_closed(tmp_path: Path, monkeypatch):
    env = _valid_env()
    env["ACCEPTANCE_TOPOLOGY_HASH"] = "not-a-sha256"
    receipt = tmp_path / "reports" / "CI_CONTAINER_REPODIGEST_VERIFIED.txt"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text("ghcr.io/owner/repo/acceptance@sha256:" + "e" * 64 + "\n", encoding="utf-8")
    monkeypatch.setattr(preflight, "_git_sha", lambda root: env["EXPECTED_ACCEPTANCE_SHA"])
    payload = preflight.run_preflight(tmp_path, env=env, which=lambda tool: f"/tools/{tool}")
    assert payload["verified"] is False
    assert "ACCEPTANCE_TOPOLOGY_HASH_VALID" in payload["problems"]
    assert "VERIFIED_CONTAINER_DIGEST_RECEIPT_MATCH" in payload["problems"]


def test_missing_required_tool_fails_closed(tmp_path: Path, monkeypatch):
    env = _valid_env()
    _prepare_receipt(tmp_path, env)
    monkeypatch.setattr(preflight, "_git_sha", lambda root: env["EXPECTED_ACCEPTANCE_SHA"])
    payload = preflight.run_preflight(tmp_path, env=env, which=lambda tool: None if tool == "docker" else f"/tools/{tool}")
    assert payload["verified"] is False
    assert "TOOL_AVAILABLE:docker" in payload["problems"]


def test_workflow_runs_preflight_before_orchestrator_and_uploads_report():
    text = WORKFLOW.read_text(encoding="utf-8")
    preflight_command = "python scripts/production_acceptance_preflight.py"
    orchestrator_command = "python scripts/production_acceptance_orchestrator.py --confirm-real-target"
    assert preflight_command in text
    assert orchestrator_command in text
    assert text.index(preflight_command) < text.index(orchestrator_command)
    preflight_to_orchestrator = text[text.index(preflight_command):text.index(orchestrator_command)]
    assert "continue-on-error" not in preflight_to_orchestrator
    assert "reports/production_acceptance/PRODUCTION_ACCEPTANCE_PREFLIGHT.json" in text
    assert "reports/production_acceptance/**" in text
    assert "if: always()" in text
    for name in preflight.SECRET_ENV_NAMES:
        assert f"{name}:" in text
