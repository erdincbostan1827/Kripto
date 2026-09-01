from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.test_inventory as inventory


def _configure_paths(monkeypatch, root: Path) -> None:
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(inventory, "ROOT", root)
    monkeypatch.setattr(inventory, "OUT_JSON", reports / "TEST_INVENTORY.json")
    monkeypatch.setattr(inventory, "OUT_TEXT", reports / "TEST_COUNT.txt")
    monkeypatch.setattr(inventory, "OUT_COLLECTION", reports / "TEST_COLLECTION.txt")
    monkeypatch.setattr(inventory, "REGRESSION", reports / "local_acceptance" / "full_regression_manifest.json")


def test_generate_uses_bounded_runner_for_pytest_collection(monkeypatch, tmp_path: Path):
    _configure_paths(monkeypatch, tmp_path)
    sha = "a" * 40
    monkeypatch.setattr(inventory, "_git_sha", lambda root=inventory.ROOT: sha)
    called: dict[str, object] = {}

    def fake_run(command, *, cwd, timeout, env=None):
        called.update(command=list(command), cwd=cwd, timeout=timeout, env=env)
        return subprocess.CompletedProcess(list(command), 0, "tests/unit/test_a.py: 2\n", None)

    monkeypatch.setattr(inventory, "run_captured", fake_run)
    inventory.REGRESSION.parent.mkdir(parents=True, exist_ok=True)
    inventory.REGRESSION.write_text(json.dumps({
        "git_commit_sha": sha,
        "status": "PASS",
        "problems": [],
        "covered_test_file_count": 1,
    }), encoding="utf-8")

    payload = inventory.generate(timeout=17)

    assert called["command"] == ["pytest", "--collect-only", "-q"]
    assert called["cwd"] == tmp_path
    assert called["timeout"] == 17
    assert payload["test_count"] == 2
    assert payload["test_file_count"] == 1


def test_collection_timeout_fails_closed_without_promoting_inventory(monkeypatch, tmp_path: Path):
    _configure_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(inventory, "_git_sha", lambda root=inventory.ROOT: "b" * 40)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(["pytest", "--collect-only", "-q"], kwargs["timeout"], output="partial")

    monkeypatch.setattr(inventory, "run_captured", timeout)

    with pytest.raises(subprocess.TimeoutExpired):
        inventory.generate(timeout=1)

    assert not inventory.OUT_JSON.exists()
    assert not inventory.OUT_TEXT.exists()
    assert not inventory.OUT_COLLECTION.exists()


def test_collection_keyboard_interrupt_propagates_without_promoting_inventory(monkeypatch, tmp_path: Path):
    _configure_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(inventory, "_git_sha", lambda root=inventory.ROOT: "c" * 40)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(inventory, "run_captured", interrupt)

    with pytest.raises(KeyboardInterrupt):
        inventory.generate(timeout=1)

    assert not inventory.OUT_JSON.exists()
    assert not inventory.OUT_TEXT.exists()
    assert not inventory.OUT_COLLECTION.exists()
