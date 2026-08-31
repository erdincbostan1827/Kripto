from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.extract_source_package import extract
from scripts.package_release import build_release, verify_archive
from scripts.verify_source_locks import verify_source_locks
from scripts.verify_source_package_identity import verify_source_package_identity


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def test_packaged_source_identity_verifies_without_dot_git(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "frontend").mkdir()
    (repo / "uv.lock").write_text("backend-lock\n", encoding="utf-8")
    (repo / "frontend/package-lock.json").write_text('{"lockfileVersion":3}\n', encoding="utf-8")
    (repo / "app.py").write_text("x=1\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "phase101@example.invalid")
    _git(repo, "config", "user.name", "Phase101")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "source")
    archive = tmp_path / "source.zip"
    build_release(repo, archive)
    extracted = tmp_path / "extracted"
    result = extract(archive, extracted)
    root = extracted / repo.name
    identity = verify_source_package_identity(root)
    locks = verify_source_locks(root)
    assert result["manifest_verified"] is True
    assert identity["verified"] is True
    assert identity["git_commit_sha"] is not None
    assert locks["verified"] is True
    assert locks["identity_mode"] == "PACKAGE_MANIFEST"
    assert all(row["package_manifest_bound"] for row in locks["locks"])


def test_source_archive_rejects_unexpected_member(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    with zipfile.ZipFile(archive, "a") as zf:
        zf.writestr(f"{root.name}/unexpected.txt", b"evil")
    result = verify_archive(archive)
    assert any(item.startswith("UNEXPECTED_MEMBER:") for item in result["mismatches"])
    with pytest.raises(ValueError, match="integrity verification failed"):
        extract(archive, tmp_path / "out")


def test_source_package_identity_detects_post_extract_tamper(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    extract(archive, out)
    extracted_root = out / root.name
    (extracted_root / "a.txt").write_text("tampered\n", encoding="utf-8")
    result = verify_source_package_identity(extracted_root)
    assert result["verified"] is False
    assert any(problem.startswith("PACKAGE_FILE_") for problem in result["problems"])


def test_content_set_hash_is_bound_inside_manifest(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    with zipfile.ZipFile(archive) as zf:
        manifest_name = f"{root.name}/PACKAGE_MANIFEST.json"
        manifest = json.loads(zf.read(manifest_name))
    assert len(manifest["content_set_sha256"]) == 64
