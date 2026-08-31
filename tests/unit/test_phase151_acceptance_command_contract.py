from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from scripts.external_acceptance_runner import command_contract, command_contract_sha256
from scripts.verify_external_acceptance import verify_manifest


def _manifest(root: Path, *, command: list[str], contract_hash: str | None = None, key: str = "docker_compose_config") -> Path:
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    log = reports / "evidence.log"
    log.write_text("evidence\n", encoding="utf-8")
    payload = {
        "schema_version": "3.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "profile": "runtime",
        "command_contract_sha256": contract_hash or command_contract_sha256("runtime"),
        "real_target_explicitly_confirmed": True,
        "challenge": {},
        "environment": {"git_commit_sha": "UNAVAILABLE"},
        "evidence": [{
            "key": key,
            "status": "BLOCKED",
            "real_system": True,
            "command": command,
            "exit_code": 0,
            "blocker": "TEST_BLOCKED",
            "artifact": str(log.relative_to(root)),
            "sha256": sha256(log.read_bytes()).hexdigest(),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }],
        "groups": {"runtime": "BLOCKED"},
        "selected_all_pass": False,
    }
    out = reports / "manifest_runtime.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out


def test_command_contract_is_deterministic_and_contains_supplemental_guards():
    first = command_contract_sha256("runtime")
    second = command_contract_sha256("runtime")
    assert first == second
    assert len(first) == 64
    contract = command_contract("runtime")
    assert contract["docker_compose_config"] == ["docker", "compose", "config", "--quiet"]
    assert contract["uv_lock_file"] == []
    assert contract["credential_guard"] == []


def test_strict_manifest_rejects_command_substitution(tmp_path: Path):
    result = verify_manifest(_manifest(tmp_path, command=["true"]), root=tmp_path)
    assert result["verified"] is False
    assert "COMMAND_CONTRACT_COMMAND_MISMATCH:docker_compose_config" in result["problems"]


def test_strict_manifest_rejects_contract_hash_substitution(tmp_path: Path):
    canonical = command_contract("runtime")["docker_compose_config"]
    result = verify_manifest(_manifest(tmp_path, command=canonical, contract_hash="0" * 64), root=tmp_path)
    assert result["verified"] is False
    assert "COMMAND_CONTRACT_HASH_MISMATCH" in result["problems"]


def test_strict_manifest_rejects_unknown_evidence_key(tmp_path: Path):
    result = verify_manifest(_manifest(tmp_path, command=[], key="forged_success_probe"), root=tmp_path)
    assert result["verified"] is False
    assert "COMMAND_CONTRACT_UNKNOWN_EVIDENCE_KEY:forged_success_probe" in result["problems"]


def test_release_challenge_rejects_dirty_tracked_source(tmp_path: Path):
    import subprocess
    from backend.app.release.acceptance_challenge import create_challenge, verify_challenge

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    source = tmp_path / "app.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp_path, check=True)
    challenge_path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    created = create_challenge(tmp_path, challenge_path)
    assert created["schema_version"] == "2.3"
    assert created["source_worktree_clean_at_creation"] is True
    source.write_text("VALUE = 2\n", encoding="utf-8")
    checked = verify_challenge(challenge_path, root=tmp_path)
    assert checked["verified"] is False
    assert "CHALLENGE_SOURCE_WORKTREE_DIRTY" in checked["problems"]


def test_release_challenge_ignores_runtime_report_outputs(tmp_path: Path):
    import subprocess
    from backend.app.release.acceptance_challenge import create_challenge, verify_challenge

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    source = tmp_path / "app.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=tmp_path, check=True)
    challenge_path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    create_challenge(tmp_path, challenge_path)
    (tmp_path / "reports" / "runtime.log").write_text("runtime evidence\n", encoding="utf-8")
    checked = verify_challenge(challenge_path, root=tmp_path)
    assert checked["verified"] is True
    assert checked["source_worktree_dirty_paths"] == []
