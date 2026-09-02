from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import scripts.local_acceptance_runner as acceptance_runner
import scripts.local_coverage_runner as coverage_runner
import scripts.merge_local_acceptance as merge_acceptance
import scripts.merge_local_coverage as merge_coverage
import scripts.verify_local_acceptance as verify_acceptance
import scripts.verify_local_coverage as verify_coverage


def _timeout(*args, **kwargs):
    raise subprocess.TimeoutExpired(["git", "rev-parse", "HEAD"], 10)


def test_git_probes_use_bounded_runner_and_fail_closed(monkeypatch):
    for module in (acceptance_runner, coverage_runner, merge_acceptance, merge_coverage, verify_acceptance, verify_coverage):
        monkeypatch.setattr(module, "run_captured_split", _timeout)
        if module in (verify_acceptance, verify_coverage):
            assert module._git_sha(Path.cwd()) == "UNAVAILABLE"
        else:
            assert module._git_sha() == "UNAVAILABLE"


def test_acceptance_shard_cannot_pass_without_git_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(acceptance_runner, "ROOT", tmp_path)
    monkeypatch.setattr(acceptance_runner, "REPORTS", tmp_path / "reports" / "local_acceptance")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok(): assert True\n")
    monkeypatch.setattr(acceptance_runner, "run_captured", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "1 passed\n", ""))
    monkeypatch.setattr(acceptance_runner, "_git_sha", lambda: "UNAVAILABLE")
    row = acceptance_runner.run_shard(0, 1, 30)
    assert row["status"] == "BLOCKED"
    assert row["blocker"] == "GIT_IDENTITY_UNAVAILABLE"


def test_coverage_shard_cannot_pass_without_git_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(coverage_runner, "ROOT", tmp_path)
    monkeypatch.setattr(coverage_runner, "REPORTS", tmp_path / "reports" / "local_coverage")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_ok.py").write_text("def test_ok(): assert True\n")
    monkeypatch.setattr(coverage_runner, "discover", lambda: ["tests/test_ok.py"])
    monkeypatch.setattr(coverage_runner, "select_shard", lambda files, index, count: files)
    def fake_run(command, *, cwd, timeout, env=None):
        # emulate coverage parallel artifact
        data_arg = next(x for x in command if x.startswith("--data-file="))
        base = Path(data_arg.split("=",1)[1])
        (base.parent / (base.name + ".fake")).write_bytes(b"coverage")
        return subprocess.CompletedProcess(command, 0, "1 passed\n", "")
    monkeypatch.setattr(coverage_runner, "run_captured", fake_run)
    monkeypatch.setattr(coverage_runner, "_git_sha", lambda: "UNAVAILABLE")
    row = coverage_runner.run_shard(0, 1, 30)
    assert row["status"] == "BLOCKED"
    assert row["blocker"] == "GIT_IDENTITY_UNAVAILABLE"


def test_verifiers_cannot_accept_unavailable_identity(monkeypatch, tmp_path):
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps({"classification":"LOCAL_FULL_REGRESSION_EVIDENCE","git_commit_sha":"UNAVAILABLE","status":"PASS","problems":[],"shards":[]}) )
    monkeypatch.setattr(verify_acceptance, "_git_sha", lambda root: "UNAVAILABLE")
    result = verify_acceptance.verify_local_acceptance(reg, tmp_path)
    assert result["verified"] is False
    assert "GIT_IDENTITY_UNAVAILABLE" in result["problems"]

    cov = tmp_path / "cov.json"
    cov.write_text(json.dumps({"classification":"LOCAL_FULL_COVERAGE_EVIDENCE","git_commit_sha":"UNAVAILABLE","status":"PASS","problems":[],"coverage_percent":90.0,"shard_count":0,"shards":[]}) )
    monkeypatch.setattr(verify_coverage, "_git_sha", lambda root: "UNAVAILABLE")
    result2 = verify_coverage.verify(cov, root=tmp_path)
    assert result2["verified"] is False
    assert "GIT_IDENTITY_UNAVAILABLE" in result2["problems"]
