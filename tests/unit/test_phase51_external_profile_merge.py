import json
from pathlib import Path

import pytest

from scripts import external_acceptance_runner as runner
from scripts import merge_external_acceptance as merger


def test_external_runner_uses_immutable_unique_run_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports/external_acceptance")
    (tmp_path / "reports/external_acceptance").mkdir(parents=True)
    # Simulation does not need a challenge and must remain BLOCKED, but its artifacts
    # must still be isolated so a later run cannot overwrite their hashes.
    a = runner.execute("runtime", confirm_real=False, timeout=1)
    b = runner.execute("runtime", confirm_real=False, timeout=1)
    assert a["run_id"] != b["run_id"]
    assert a["immutable_manifest"] != b["immutable_manifest"]
    pa = tmp_path / a["immutable_manifest"]
    pb = tmp_path / b["immutable_manifest"]
    assert pa.is_file() and pb.is_file()
    adoc = json.loads(pa.read_text())
    bdoc = json.loads(pb.read_text())
    aa = {x["artifact"] for x in adoc["evidence"]}
    ba = {x["artifact"] for x in bdoc["evidence"]}
    assert aa.isdisjoint(ba)


def test_merge_missing_profiles_fails_closed(tmp_path, monkeypatch):
    reports = tmp_path / "reports/external_acceptance"
    reports.mkdir(parents=True)
    monkeypatch.setattr(merger, "ROOT", tmp_path)
    monkeypatch.setattr(merger, "REPORTS", reports)
    result = merger.merge(root=tmp_path)
    assert result["selected_all_pass"] is False
    assert all(v == "NOT_TESTED" for v in result["groups"].values())
    assert result["verification"]["verified"] is False  # no real target/challenge


def test_profile_map_covers_every_external_group():
    assert {g for groups in merger.PROFILE_TO_GROUPS.values() for g in groups} == set(merger.GROUP_KEYS)
