from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.verify_source_locks import verify_source_locks


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )


def _init_source_lock_repo(root: Path) -> None:
    (root / "frontend").mkdir(parents=True)
    (root / "uv.lock").write_bytes(b"version = 1\n")
    (root / "frontend" / "package-lock.json").write_bytes(b'{"lockfileVersion":3}\n')

    _git(root, "init")
    _git(root, "config", "user.email", "phase237@example.invalid")
    _git(root, "config", "user.name", "Phase 237")
    _git(root, "config", "core.autocrlf", "true")
    _git(root, "add", "uv.lock", "frontend/package-lock.json")
    _git(root, "commit", "-m", "fixture locks")


def test_windows_crlf_checkout_matches_canonical_head_blob(tmp_path: Path) -> None:
    _init_source_lock_repo(tmp_path)

    (tmp_path / "uv.lock").write_bytes(b"version = 1\r\n")
    (tmp_path / "frontend" / "package-lock.json").write_bytes(b'{"lockfileVersion":3}\r\n')

    result = verify_source_locks(tmp_path)

    assert result["verified"] is True
    assert result["problems"] == []
    for row in result["locks"]:
        assert row["tracked"] is True
        assert row["matches_head"] is True
        assert row["comparison_mode"] == "GIT_CANONICAL_BLOB"
        assert row["head_blob_oid"] == row["working_tree_blob_oid"]
        assert row["head_sha256"] != row["working_tree_sha256"]


def test_substantive_lock_change_still_fails_closed_after_crlf_conversion(tmp_path: Path) -> None:
    _init_source_lock_repo(tmp_path)

    (tmp_path / "uv.lock").write_bytes(b"version = 2\r\n")
    (tmp_path / "frontend" / "package-lock.json").write_bytes(b'{"lockfileVersion":3}\r\n')

    result = verify_source_locks(tmp_path)

    assert result["verified"] is False
    assert "uv.lock:DIFFERS_FROM_HEAD" in result["problems"]

    rows = {row["path"]: row for row in result["locks"]}
    assert rows["uv.lock"]["matches_head"] is False
    assert rows["uv.lock"]["head_blob_oid"] != rows["uv.lock"]["working_tree_blob_oid"]
    assert rows["frontend/package-lock.json"]["matches_head"] is True
