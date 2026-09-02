from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.external_acceptance_runner as runner
import scripts.merge_external_acceptance as merger
import scripts.production_acceptance_handoff as handoff
import scripts.verify_external_acceptance as verifier


def _timeout(*args, **kwargs):
    raise subprocess.TimeoutExpired(["git", "rev-parse", "HEAD"], 10)


def test_external_git_probes_are_bounded_and_fail_closed(monkeypatch, tmp_path):
    for module, fn, args in (
        (runner, runner._git_sha, ()),
        (merger, merger._git_sha, (tmp_path,)),
        (verifier, verifier._git_sha, (tmp_path,)),
    ):
        monkeypatch.setattr(module, "run_captured_split", _timeout)
        assert fn(*args) == "UNAVAILABLE"


def test_real_runner_blocks_before_commands_without_git_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports" / "external_acceptance")
    monkeypatch.setattr(runner, "verify_challenge", lambda *a, **k: {"verified": True, "challenge_id":"x", "sha256":"y"})
    monkeypatch.setattr(runner, "_git_sha", lambda: "UNAVAILABLE")
    monkeypatch.setenv("ACCEPTANCE_ENVIRONMENT_ID", "phase214")
    monkeypatch.setenv("ACCEPTANCE_TOPOLOGY_HASH", "a" * 64)
    payload = runner.execute("locks", confirm_real=True, timeout=1)
    assert payload["selected_all_pass"] is False
    assert payload["blocker"].startswith("ACCEPTANCE_ENVIRONMENT_IDENTITY_MISSING:")
    assert "GIT_COMMIT_SHA" in payload["blocker"]
    assert payload["evidence"] == []


def test_merger_records_unavailable_git_identity(monkeypatch, tmp_path):
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    monkeypatch.setattr(merger, "_git_sha", lambda root: "UNAVAILABLE")
    monkeypatch.setattr(merger, "verify_challenge", lambda *a, **k: {"verified": False, "trust_verified": False})
    result = merger.merge(root=tmp_path)
    assert "GIT_IDENTITY_UNAVAILABLE" in result["merge_problems"]
    assert result["selected_all_pass"] is False


def test_verifier_declared_pass_requires_current_git_identity(monkeypatch, tmp_path):
    reports = tmp_path / "reports" / "external_acceptance"
    reports.mkdir(parents=True)
    manifest = reports / "manifest_runtime.json"
    now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    payload = {
        "schema_version":"3.2", "classification":"EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "profile":"runtime", "generated_at":now, "command_contract_sha256": verifier.command_contract_sha256("runtime"),
        "groups": {g:("PASS" if g=="runtime" else "NOT_TESTED") for g in verifier.GROUP_KEYS},
        "environment":{"git_commit_sha":"UNAVAILABLE","acceptance_environment_id_hash":"b"*64,"topology_hash":"c"*64},
        "challenge":{}, "evidence":[], "real_target_explicitly_confirmed":True,
    }
    manifest.write_text(json.dumps(payload))
    monkeypatch.setattr(verifier, "_git_sha", lambda root: "UNAVAILABLE")
    monkeypatch.setattr(verifier, "verify_challenge", lambda *a, **k: {"verified":False})
    result = verifier.verify_manifest(manifest, root=tmp_path)
    assert result["verified"] is False
    assert "GIT_IDENTITY_UNAVAILABLE" in result["problems"]


def test_handoff_git_timeout_fails_to_package_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(handoff, "run_captured_split", _timeout)
    monkeypatch.setattr(handoff, "verify_source_package_identity", lambda *a, **k: {"verified": False})
    sha, tags, mode, verified = handoff._candidate_identity(tmp_path)
    assert sha is None and tags == [] and mode == "UNAVAILABLE" and verified is False
