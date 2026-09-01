from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import scripts.external.acceptance_return_promotion as promo
import scripts.external.frontend_browser_acceptance as frontend
import scripts.external.run_all_external_requirements as master
import scripts.external.tauri_build_readiness as tauri
import scripts.local_coverage_runner as coverage_runner
import scripts.merge_local_coverage as coverage_merge


def _completed(command: list[str], stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, stdout, "")


def test_phase209_candidate_worktree_timeout_removes_temp_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    parent = tmp_path / "candidate-parent"

    def fake_mkdtemp(*, prefix: str) -> str:
        assert prefix.startswith("acceptance-promotion-assess-")
        parent.mkdir()
        return str(parent)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0] if args else ["git"], kwargs.get("timeout", 1))

    monkeypatch.setattr(promo.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(promo, "run_captured_split", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        promo._candidate_worktree(tmp_path)
    assert not parent.exists()


def test_phase209_worktree_cleanup_prunes_after_remove_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    parent = tmp_path / "candidate-parent"
    worktree = parent / "repo"
    worktree.mkdir(parents=True)
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        command = list(command)
        calls.append(command)
        if command[:4] == ["git", "worktree", "remove", "--force"]:
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 1))
        return _completed(command)

    monkeypatch.setattr(promo, "run_captured_split", fake_run)
    promo._cleanup_worktree(tmp_path, parent, worktree)
    assert calls[0][:4] == ["git", "worktree", "remove", "--force"]
    assert calls[1] == ["git", "worktree", "prune", "--expire", "now"]
    assert not parent.exists()


def test_phase209_git_identity_probes_use_bounded_runner(monkeypatch: pytest.MonkeyPatch):
    expected = "a" * 40
    seen: list[tuple[str, float]] = []

    def fake_run(command, **kwargs):
        seen.append((" ".join(command), float(kwargs["timeout"])))
        return _completed(list(command), expected + "\n")

    monkeypatch.setattr(master, "run_captured", fake_run)
    monkeypatch.setattr(frontend, "run_captured", fake_run)
    monkeypatch.setattr(tauri, "run_captured", fake_run)

    assert master._current_git_sha() == expected
    assert frontend._git_sha() == expected
    assert tauri.git_sha() == expected
    assert len(seen) == 3
    assert all(command == "git rev-parse HEAD" and timeout == 10 for command, timeout in seen)


def test_phase209_coverage_merge_timeout_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    reports = root / "reports" / "local_coverage"
    reports.mkdir(parents=True)
    log = reports / "coverage_shard_00_of_01.log"
    data = reports / ".coverage.00_of_01"
    log.write_text("ok\n", encoding="utf-8")
    data.write_bytes(b"coverage")
    shard = {
        "git_commit_sha": "b" * 40,
        "status": "PASS",
        "exit_code": 0,
        "log": str(log.relative_to(root)),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "coverage_data": str(data.relative_to(root)),
        "coverage_data_sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
        "selected_files": ["tests/test_x.py"],
    }
    (reports / "coverage_shard_00_of_01.json").write_text(json.dumps(shard), encoding="utf-8")

    monkeypatch.setattr(coverage_merge, "ROOT", root)
    monkeypatch.setattr(coverage_merge, "REPORTS", reports)
    monkeypatch.setattr(coverage_merge, "OUT", reports / "full_coverage_manifest.json")
    monkeypatch.setattr(coverage_merge, "COVERAGE_JSON", reports / "coverage.json")
    monkeypatch.setattr(coverage_merge, "discover", lambda: ["tests/test_x.py"])
    monkeypatch.setattr(coverage_merge, "_git_sha", lambda: "b" * 40)

    def timeout(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 1), output="partial")

    monkeypatch.setattr(coverage_merge, "run_captured", timeout)
    result = coverage_merge.merge(1)
    assert result["status"] == "BLOCKED"
    assert "COVERAGE_COMBINE_TIMEOUT" in result["problems"]
    assert result["coverage_percent"] is None


def test_phase209_shard_parallel_combine_timeout_does_not_promote_missing_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    reports = root / "reports" / "local_coverage"
    reports.mkdir(parents=True)
    monkeypatch.setattr(coverage_runner, "ROOT", root)
    monkeypatch.setattr(coverage_runner, "REPORTS", reports)
    monkeypatch.setattr(coverage_runner, "discover", lambda: ["tests/test_x.py"])
    monkeypatch.setattr(coverage_runner, "select_shard", lambda files, index, count: files)
    monkeypatch.setattr(coverage_runner, "_git_sha", lambda: "c" * 40)
    calls = 0

    def fake_run(command, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            (reports / ".coverage.00_of_01.host.a").write_bytes(b"a")
            (reports / ".coverage.00_of_01.host.b").write_bytes(b"b")
            return _completed(list(command), "1 passed\n")
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout", 1), output="combine partial")

    monkeypatch.setattr(coverage_runner, "run_captured", fake_run)
    result = coverage_runner.run_shard(0, 1, 30)
    assert result["status"] == "FAIL"
    assert result["coverage_data"] is None
    assert result["blocker"] == "COVERAGE_DATA_MISSING"
    log = root / result["log"]
    assert "COVERAGE_COMBINE_TIMEOUT" in log.read_text(encoding="utf-8")
