from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import backend.app.release.acceptance_challenge as challenge_mod
from backend.app.release.acceptance_challenge import create_challenge, verify_challenge
from backend.app.release.acceptance_contract import (
    DEFAULT_GROUP_TTL_HOURS,
    GROUP_KEYS,
    RUNNER_GROUP_KEYS,
    acceptance_contract_sha256,
    command_contract_sha256,
)
from scripts.external_acceptance_runner import command_contract_sha256 as runner_contract_sha
from scripts.verify_external_acceptance import DEFAULT_GROUP_TTL_HOURS as verifier_ttls
from scripts.verify_external_acceptance import GROUP_KEYS as verifier_groups


def _git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p160@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P160"], cwd=root, check=True)
    (root / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "seed.txt"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)


def test_challenge_schema_23_binds_current_acceptance_contract(tmp_path: Path) -> None:
    _git(tmp_path)
    path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    doc = create_challenge(tmp_path, path)
    assert doc["schema_version"] == "2.3"
    assert doc["acceptance_contract_sha256"] == acceptance_contract_sha256()
    result = verify_challenge(path, root=tmp_path, require_trust=False)
    assert result["verified"] is True
    assert result["acceptance_contract_sha256"] == acceptance_contract_sha256()


def test_challenge_rejects_acceptance_semantic_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path)
    path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    create_challenge(tmp_path, path)
    monkeypatch.setattr(challenge_mod, "acceptance_contract_sha256", lambda: "f" * 64)
    result = verify_challenge(path, root=tmp_path, require_trust=False)
    assert result["verified"] is False
    assert "CHALLENGE_ACCEPTANCE_CONTRACT_MISMATCH" in result["problems"]


def test_runner_and_verifier_share_one_canonical_contract() -> None:
    assert runner_contract_sha("all") == command_contract_sha256("all")
    assert verifier_groups is GROUP_KEYS
    assert verifier_ttls is DEFAULT_GROUP_TTL_HOURS
    assert RUNNER_GROUP_KEYS["dependency_locks_and_frontend_build"][0] == "source_lock_compliance"
