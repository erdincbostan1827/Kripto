from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_external_acceptance import verify_manifest


def _base(root: Path, *, schema: str) -> Path:
    reports = root / "reports" / "external_acceptance"
    reports.mkdir(parents=True, exist_ok=True)
    artifact = root / "artifact.log"
    artifact.write_text("ok\n", encoding="utf-8")
    import hashlib
    row = {
        "schema_version": schema,
        "classification": "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE",
        "generated_at": "2026-08-30T16:00:00+00:00",
        "profile": "runtime",
        "real_target_explicitly_confirmed": True,
        "environment": {"git_commit_sha": "UNAVAILABLE", "acceptance_environment_id_hash": "a"*64, "topology_hash": "b"*64},
        "evidence": [{"key": "docker_runtime", "status": "PASS", "real_system": True, "exit_code": 0, "blocker": None, "artifact": "artifact.log", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "observed_at": "2026-08-30T16:00:00+00:00", "command": []}],
        "groups": {"runtime": "PASS"},
        "selected_all_pass": True,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(row), encoding="utf-8")
    return path


def test_legacy_schema_cannot_claim_pass(tmp_path: Path) -> None:
    result = verify_manifest(_base(tmp_path, schema="3.1"), root=tmp_path)
    assert "LEGACY_SCHEMA_PASS_NOT_ALLOWED" in result["problems"]
    assert result["verified"] is False


def test_strict_schema_rejects_symlink_artifact_source_contract() -> None:
    text = Path("scripts/verify_external_acceptance.py").read_text(encoding="utf-8")
    assert "ARTIFACT_SYMLINK_NOT_ALLOWED" in text
    assert "MANIFEST_SYMLINK_NOT_ALLOWED" in text
