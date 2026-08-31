from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.release.acceptance_contract import command_contract_sha256
from scripts import external_acceptance_runner as runner
from scripts.verify_external_acceptance import _strict_regular_artifact, verify_manifest


def _manifest(root: Path, *, profile: str, schema: str) -> Path:
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": schema,
        "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "command_contract_sha256": command_contract_sha256(profile),
        "real_target_explicitly_confirmed": True,
        "challenge": {},
        "environment": {
            "git_commit_sha": "UNAVAILABLE",
            "acceptance_environment_id_hash": "a" * 64,
            "topology_hash": "b" * 64,
        },
        "evidence": [],
        "groups": {"runtime": "PASS"},
        "selected_all_pass": True,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_aggregate_pass_requires_schema_4_1(tmp_path: Path) -> None:
    result = verify_manifest(_manifest(tmp_path, profile="all", schema="3.2"), root=tmp_path)
    assert "AGGREGATE_PASS_REQUIRES_SCHEMA_4_1" in result["problems"]
    assert result["verified"] is False


def test_individual_profile_pass_requires_schema_3_2(tmp_path: Path) -> None:
    result = verify_manifest(_manifest(tmp_path, profile="runtime", schema="4.1"), root=tmp_path)
    assert "PROFILE_PASS_REQUIRES_SCHEMA_3_2" in result["problems"]
    assert result["verified"] is False


def test_nested_acceptance_artifact_symlink_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "evidence.json"
    target.write_text("{}\n", encoding="utf-8")
    link = tmp_path / "nested.json"
    link.symlink_to(target.name)
    with pytest.raises(ValueError, match="symlink"):
        _strict_regular_artifact(tmp_path, "nested.json")


def test_real_all_runner_requires_merge_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reports = tmp_path / "reports" / "external_acceptance"
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", reports)
    payload = runner.execute("all", confirm_real=True, timeout=1)
    assert payload["selected_all_pass"] is False
    assert payload["blocker"] == "AGGREGATE_REAL_ACCEPTANCE_REQUIRES_MERGE"
    assert payload["schema_version"] == "3.2"
