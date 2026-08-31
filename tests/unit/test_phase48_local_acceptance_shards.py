from __future__ import annotations

import json
from pathlib import Path

import scripts.local_acceptance_runner as runner
import scripts.merge_local_acceptance as merger


def test_shard_selection_is_complete_disjoint_and_deterministic() -> None:
    files = [f"tests/test_{i}.py" for i in range(23)]
    shards = [runner.select_shard(files, i, 5) for i in range(5)]
    flattened = [x for shard in shards for x in shard]
    assert sorted(flattened) == sorted(files)
    assert len(flattened) == len(set(flattened))
    assert shards == [runner.select_shard(files, i, 5) for i in range(5)]


def test_merge_rejects_missing_shards(monkeypatch, tmp_path: Path) -> None:
    reports = tmp_path / "reports/local_acceptance"
    reports.mkdir(parents=True)
    monkeypatch.setattr(merger, "ROOT", tmp_path)
    monkeypatch.setattr(merger, "REPORTS", reports)
    monkeypatch.setattr(merger, "discover", lambda: ["tests/a.py"])
    monkeypatch.setattr(merger, "_git_sha", lambda: "abc")
    result = merger.merge(2)
    assert result["status"] == "BLOCKED"
    assert "SHARD_MISSING:0" in result["problems"]


def test_merge_detects_tampered_log(monkeypatch, tmp_path: Path) -> None:
    reports = tmp_path / "reports/local_acceptance"
    reports.mkdir(parents=True)
    monkeypatch.setattr(merger, "ROOT", tmp_path)
    monkeypatch.setattr(merger, "REPORTS", reports)
    monkeypatch.setattr(merger, "discover", lambda: ["tests/a.py"])
    monkeypatch.setattr(merger, "_git_sha", lambda: "abc")
    log = reports / "s.log"; log.write_text("pass")
    row = {"git_commit_sha":"abc","status":"PASS","exit_code":0,"log":"reports/local_acceptance/s.log","log_sha256":"0"*64,"selected_files":["tests/a.py"]}
    (reports / "shard_00_of_01.json").write_text(json.dumps(row))
    result = merger.merge(1)
    assert result["status"] == "BLOCKED"
    assert "SHARD_LOG_HASH_INVALID:0" in result["problems"]
