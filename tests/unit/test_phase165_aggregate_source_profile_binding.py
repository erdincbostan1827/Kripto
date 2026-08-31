from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import backend.app.release.acceptance_challenge as challenge_mod
from backend.app.release.acceptance_challenge import create_challenge, verify_challenge
from backend.app.release.acceptance_contract import (
    ACCEPTANCE_CONTRACT_SCHEMA,
    PROFILE_ORDER,
    PROFILE_TO_GROUPS,
    acceptance_contract_payload,
)
from scripts import merge_external_acceptance as merger
import scripts.verify_external_acceptance as verifier


def _git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "p165@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "P165"], cwd=root, check=True)
    (root / "seed").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "seed"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=root, check=True)


def _source_payload(root: Path) -> dict:
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    environment = {"acceptance_environment_id_hash": "a" * 64, "topology_hash": "b" * 64}
    sources = {}
    aggregate_evidence = []
    for profile in PROFILE_ORDER:
        profile_evidence = [
            {"key": key, "source_profile": profile}
            for group in PROFILE_TO_GROUPS[profile]
            for key in verifier.GROUP_KEYS[group]
        ]
        aggregate_evidence.extend(profile_evidence)
        path = reports / f"manifest_{profile}.json"
        path.write_text(json.dumps({"profile": profile, "environment": environment, "evidence": profile_evidence}), encoding="utf-8")
        sources[profile] = {
            "status": "VERIFIED",
            "reference": str(path.relative_to(root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "problems": [],
        }
    return {"source_profiles": sources, "environment": environment, "evidence": aggregate_evidence}


def test_profile_to_group_mapping_is_part_of_canonical_acceptance_contract() -> None:
    payload = acceptance_contract_payload()
    assert ACCEPTANCE_CONTRACT_SCHEMA == "1.1"
    assert payload["profile_to_groups"] == {k: list(v) for k, v in PROFILE_TO_GROUPS.items()}
    assert merger.PROFILE_TO_GROUPS is PROFILE_TO_GROUPS
    assert set(PROFILE_TO_GROUPS) == set(PROFILE_ORDER)


def test_challenge_detects_profile_to_group_semantic_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _git(tmp_path)
    challenge_path = tmp_path / "reports" / "external_acceptance" / "release_challenge.json"
    create_challenge(tmp_path, challenge_path)
    monkeypatch.setitem(PROFILE_TO_GROUPS, "runtime", ("ha",))
    result = verify_challenge(challenge_path, root=tmp_path, require_trust=False)
    assert result["verified"] is False
    assert "CHALLENGE_ACCEPTANCE_CONTRACT_MISMATCH" in result["problems"]


def test_aggregate_source_profile_binding_reverifies_all_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _source_payload(tmp_path)
    calls = []

    def fake_verify(path: Path, *, root: Path, max_age_hours: int = 168, group_ttl_hours=None):
        profile = path.stem.removeprefix("manifest_")
        calls.append(profile)
        return {
            "verified": True,
            "profile": profile,
            "groups": {group: "PASS" for group in PROFILE_TO_GROUPS[profile]},
        }

    monkeypatch.setattr(verifier, "verify_manifest", fake_verify)
    problems = verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168)
    assert problems == []
    assert calls == list(PROFILE_ORDER)


def test_aggregate_source_profile_binding_rejects_hash_replacement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _source_payload(tmp_path)
    payload["source_profiles"]["locks"]["sha256"] = "0" * 64
    def fake_verify(path: Path, *, root: Path, max_age_hours: int = 168, group_ttl_hours=None):
        profile = path.stem.removeprefix("manifest_")
        assert profile != "locks", "hash mismatch must fail before recursive verification for the replaced source"
        return {"verified": True, "profile": profile, "groups": {g: "PASS" for g in PROFILE_TO_GROUPS[profile]}}
    monkeypatch.setattr(verifier, "verify_manifest", fake_verify)
    problems = verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168)
    assert "AGGREGATE_SOURCE_PROFILE_HASH_MISMATCH:locks" in problems


def test_aggregate_source_profile_binding_rejects_noncanonical_reference(tmp_path: Path) -> None:
    payload = _source_payload(tmp_path)
    payload["source_profiles"]["runtime"]["reference"] = "reports/external_acceptance/runs/forged/manifest.json"
    problems = verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168)
    assert "AGGREGATE_SOURCE_PROFILE_REFERENCE_INVALID:runtime" in problems
