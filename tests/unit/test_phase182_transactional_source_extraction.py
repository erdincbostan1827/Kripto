from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

import scripts.extract_source_package as extraction


def _plain_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("project/file.txt", b"payload")


def test_failed_copy_leaves_absent_destination_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    package = tmp_path / "source.zip"
    _plain_zip(package)
    destination = tmp_path / "out"

    def fail_copy(*args, **kwargs):
        raise OSError("simulated copy failure")

    monkeypatch.setattr(extraction.shutil, "copyfileobj", fail_copy)
    with pytest.raises(OSError, match="simulated copy failure"):
        extraction.extract(package, destination)

    assert not destination.exists()
    assert not list(tmp_path.glob(".out.extract-*"))


def test_failed_copy_preserves_preexisting_empty_destination(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    package = tmp_path / "source.zip"
    _plain_zip(package)
    destination = tmp_path / "out"
    destination.mkdir()

    def fail_copy(*args, **kwargs):
        raise OSError("simulated copy failure")

    monkeypatch.setattr(extraction.shutil, "copyfileobj", fail_copy)
    with pytest.raises(OSError, match="simulated copy failure"):
        extraction.extract(package, destination)

    assert destination.is_dir()
    assert list(destination.iterdir()) == []
    assert not list(tmp_path.glob(".out.extract-*"))


def test_success_atomically_promotes_staging_tree(tmp_path: Path):
    package = tmp_path / "source.zip"
    _plain_zip(package)
    destination = tmp_path / "out"

    result = extraction.extract(package, destination)

    assert (destination / "project/file.txt").read_bytes() == b"payload"
    assert result["files_extracted"] == 1
    assert not list(tmp_path.glob(".out.extract-*"))
