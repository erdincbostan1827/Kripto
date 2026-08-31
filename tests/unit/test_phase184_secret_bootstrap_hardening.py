import os
from pathlib import Path

import pytest

from scripts import bootstrap_secrets as mod


def test_phase184_secret_create_once_preserves_existing_value_and_permissions(tmp_path):
    root = tmp_path / "secrets"
    assert mod.write_secret_once(root, "postgres_password.txt", "first-value") is True
    path = root / "postgres_password.txt"
    assert path.read_text(encoding="utf-8") == "first-value"
    assert mod.write_secret_once(root, "postgres_password.txt", "replacement") is False
    assert path.read_text(encoding="utf-8") == "first-value"
    assert path.stat().st_mode & 0o777 == 0o600
    assert root.stat().st_mode & 0o777 == 0o700


def test_phase184_secret_bootstrap_rejects_symlink_target(tmp_path):
    root = tmp_path / "secrets"
    root.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("do-not-touch", encoding="utf-8")
    (root / "postgres_password.txt").symlink_to(victim)
    with pytest.raises(RuntimeError, match="SECRET_PATH_UNSAFE"):
        mod.write_secret_once(root, "postgres_password.txt", "new-secret")
    assert victim.read_text(encoding="utf-8") == "do-not-touch"


def test_phase184_secret_bootstrap_rejects_symlink_secret_directory(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "secrets"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(RuntimeError, match="SECRETS_DIRECTORY_UNSAFE"):
        mod.write_secret_once(link, "postgres_password.txt", "new-secret")
    assert not (real / "postgres_password.txt").exists()


def test_phase184_secret_bootstrap_removes_partial_new_file_when_write_fails(tmp_path, monkeypatch):
    root = tmp_path / "secrets"
    real_write = os.write
    calls = {"n": 0}

    def fail_write(fd, data):
        calls["n"] += 1
        if calls["n"] == 1:
            real_write(fd, data[: min(2, len(data))])
            raise OSError("simulated disk error")
        return real_write(fd, data)

    monkeypatch.setattr(mod.os, "write", fail_write)
    with pytest.raises(OSError, match="simulated disk error"):
        mod.write_secret_once(root, "postgres_password.txt", "secret-value")
    assert not (root / "postgres_password.txt").exists()


def test_phase184_empty_or_special_existing_secret_fails_closed(tmp_path):
    root = tmp_path / "secrets"
    root.mkdir()
    empty = root / "postgres_password.txt"
    empty.touch()
    with pytest.raises(RuntimeError, match="SECRET_EMPTY"):
        mod.write_secret_once(root, "postgres_password.txt", "new-secret")
