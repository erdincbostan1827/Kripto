from __future__ import annotations

from pathlib import Path

from scripts.extract_source_package import extract
from scripts.package_release import build_release
from scripts.verify_source_package_identity import verify_source_package_identity


def test_package_identity_rejects_injected_dot_git_directory(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    extract(archive, out)
    extracted = out / root.name
    (extracted / ".git").mkdir()
    (extracted / ".git/config").write_text("[core]\nrepositoryformatversion = 0\n", encoding="utf-8")
    result = verify_source_package_identity(extracted)
    assert result["verified"] is False
    assert "PACKAGE_DOT_GIT_PRESENT" in result["problems"]


def test_package_identity_rejects_injected_dot_git_file(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("x = 1\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    extract(archive, out)
    extracted = out / root.name
    (extracted / ".git").write_text("gitdir: /tmp/fake.git\n", encoding="utf-8")
    result = verify_source_package_identity(extracted)
    assert result["verified"] is False
    assert "PACKAGE_DOT_GIT_PRESENT" in result["problems"]
