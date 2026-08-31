from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.external.acceptance_return_bundle import MANIFEST, build, stage, verify


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "reports/external_acceptance").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "phase178@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Phase 178"], cwd=root, check=True)
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
    return root


def test_phase178_return_bundle_deterministic_and_git_bound(tmp_path: Path):
    root = _repo(tmp_path)
    p = root / "reports/external_acceptance/manifest_runtime.json"
    p.write_text(json.dumps({"evidence": []}), encoding="utf-8")
    a = tmp_path / "a.zip"; b = tmp_path / "b.zip"
    first = build(root, a); second = build(root, b)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert first["sha256"] == second["sha256"]
    assert verify(a, expected_git_sha=sha)["verified"] is True
    assert first["manifest"]["secret_transport"] is False


def test_phase178_return_bundle_rejects_secret(tmp_path: Path):
    root = _repo(tmp_path)
    p = root / "reports/external_acceptance/provenance.json"
    p.write_text('api_key="super-secret-value-123456"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="RETURN_SECRET_PATTERN"):
        build(root, tmp_path / "bad.zip")


def test_phase178_return_verifier_rejects_source_mismatch_and_tamper(tmp_path: Path):
    root = _repo(tmp_path); archive = tmp_path / "ok.zip"
    (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    build(root, archive)
    mismatch = verify(archive, expected_git_sha="f" * 40)
    assert "SOURCE_GIT_MISMATCH" in mismatch["problems"]
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive) as src, zipfile.ZipFile(tampered, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "uv.lock": data += b"tamper"
            dst.writestr(info, data)
    assert any(p.startswith("HASH_MISMATCH:uv.lock") for p in verify(tampered)["problems"])


def test_phase178_stage_is_atomic_idempotent_and_never_promotes_canonical(tmp_path: Path):
    root = _repo(tmp_path); archive = tmp_path / "ok.zip"
    canonical = root / "reports/external_acceptance/manifest_all.json"
    canonical.write_text('{"canonical":true}\n', encoding="utf-8")
    build(root, archive)
    staging = tmp_path / "incoming"
    first = stage(archive, root=root, staging_root=staging)
    second = stage(archive, root=root, staging_root=staging)
    assert first["staged"] is True and first["idempotent"] is False
    assert second["staged"] is True and second["idempotent"] is True
    assert json.loads(canonical.read_text())["canonical"] is True
    assert (Path(first["path"]) / MANIFEST).is_file()
