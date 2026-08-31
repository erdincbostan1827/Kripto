from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.external.acceptance_handoff_bundle import MANIFEST_NAME, build, verify


def _fixture_root(tmp_path: Path) -> Path:
    from scripts.external.acceptance_handoff_bundle import FILES
    root = tmp_path / "repo"
    for rel in FILES:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"safe fixture for {rel}\n", encoding="utf-8")
    (root / "PACKAGE_MANIFEST.json").write_text(json.dumps({"content_set_sha256": "a" * 64}), encoding="utf-8")
    return root


def test_phase177_handoff_is_deterministic_and_verified(tmp_path: Path):
    root = _fixture_root(tmp_path)
    a = tmp_path / "a.zip"; b = tmp_path / "b.zip"
    first = build(root, a); second = build(root, b)
    assert first["sha256"] == second["sha256"]
    assert verify(a) == {"verified": True, "problems": []}
    assert first["manifest"]["classification"].endswith("NOT_ACCEPTANCE_EVIDENCE")
    assert first["manifest"]["secret_transport"] is False


def test_phase177_handoff_rejects_secret_values(tmp_path: Path):
    root = _fixture_root(tmp_path)
    target = root / "scripts/external_acceptance_runner.py"
    target.write_text("api_secret=super-secret-value-12345\n", encoding="utf-8")
    with pytest.raises(ValueError, match="HANDOFF_SECRET_PATTERN"):
        build(root, tmp_path / "bad.zip")


def test_phase177_verifier_detects_tampering(tmp_path: Path):
    root = _fixture_root(tmp_path)
    archive = tmp_path / "ok.zip"
    build(root, archive)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive) as src, zipfile.ZipFile(tampered, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "RELEASE_MANIFEST.json":
                data += b"tamper"
            dst.writestr(info, data)
    result = verify(tampered)
    assert result["verified"] is False
    assert any(p.startswith("HASH_MISMATCH:RELEASE_MANIFEST.json") for p in result["problems"])


def test_phase177_handoff_manifest_has_no_generated_timestamp(tmp_path: Path):
    root = _fixture_root(tmp_path)
    archive = tmp_path / "ok.zip"
    build(root, archive)
    with zipfile.ZipFile(archive) as zf:
        manifest = json.loads(zf.read(MANIFEST_NAME))
    assert "generated_at" not in manifest
