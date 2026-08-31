from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from backend.app.release.acceptance_contract import PROFILE_ORDER, PROFILE_TO_GROUPS
import scripts.verify_external_acceptance as verifier


def _payload(root: Path) -> dict:
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


def _fake_verify(path: Path, *, root: Path, max_age_hours: int = 168, group_ttl_hours=None):
    profile = path.stem.removeprefix("manifest_")
    return {"verified": True, "profile": profile, "groups": {g: "PASS" for g in PROFILE_TO_GROUPS[profile]}}


def test_aggregate_rebinds_each_source_profile_to_same_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(tmp_path)
    monkeypatch.setattr(verifier, "verify_manifest", _fake_verify)
    assert verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168) == []


def test_aggregate_rejects_source_profile_from_different_environment_even_with_valid_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(tmp_path)
    path = tmp_path / "reports" / "external_acceptance" / "manifest_runtime.json"
    doc = json.loads(path.read_text())
    doc["environment"]["acceptance_environment_id_hash"] = "c" * 64
    path.write_text(json.dumps(doc), encoding="utf-8")
    payload["source_profiles"]["runtime"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(verifier, "verify_manifest", _fake_verify)
    problems = verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168)
    assert "AGGREGATE_SOURCE_PROFILE_ENVIRONMENT_MISMATCH:runtime" in problems


def test_aggregate_rejects_source_profile_from_different_topology_even_with_valid_hash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _payload(tmp_path)
    path = tmp_path / "reports" / "external_acceptance" / "manifest_ha.json"
    doc = json.loads(path.read_text())
    doc["environment"]["topology_hash"] = "d" * 64
    path.write_text(json.dumps(doc), encoding="utf-8")
    payload["source_profiles"]["ha"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(verifier, "verify_manifest", _fake_verify)
    problems = verifier._verify_aggregate_source_profiles(payload, root=tmp_path, max_age_hours=168)
    assert "AGGREGATE_SOURCE_PROFILE_TOPOLOGY_MISMATCH:ha" in problems
