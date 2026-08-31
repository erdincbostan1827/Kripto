from __future__ import annotations

from pathlib import Path

import pytest

from scripts.extract_source_package import extract
from scripts.package_release import build_release


def test_extract_rejects_nonempty_destination(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    out.mkdir()
    (out / "stale.txt").write_text("stale\n", encoding="utf-8")
    with pytest.raises(ValueError, match="destination must be empty"):
        extract(archive, out)
    assert (out / "stale.txt").read_text(encoding="utf-8") == "stale\n"
    assert not (out / root.name).exists()


def test_extract_reverifies_extracted_manifest_inventory(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    (root / "a.txt").write_text("safe\n", encoding="utf-8")
    archive = tmp_path / "source.zip"
    build_release(root, archive)
    out = tmp_path / "out"
    result = extract(archive, out)
    assert result["manifest_verified"] is True
    assert result["extracted_identity_verified"] is True
    assert (out / root.name / "a.txt").read_text(encoding="utf-8") == "safe\n"
