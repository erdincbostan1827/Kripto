from __future__ import annotations

import json
from pathlib import Path

import scripts.generate_release_manifest as grm


def test_external_acceptance_exposes_verified_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    p = tmp_path / "reports/external_acceptance/manifest_all.json"
    p.parent.mkdir(parents=True)
    p.write_text("{}")
    provenance = {"ci_run_id": "77", "dependency_lock_hash": "a"*64, "frontend_lock_hash": "b"*64,
                  "sbom_hash": "c"*64, "container_digest": "repo@sha256:" + "d"*64,
                  "frontend_artifact_hash": "e"*64, "git_commit_sha": "f"*40}
    monkeypatch.setattr(grm, "verify_manifest", lambda *a, **k: {
        "verified": True, "selected_all_pass": False, "manifest_sha256": "1"*64,
        "real_target_confirmed": True, "profile": "all", "problems": [],
        "groups": {"provenance": "PASS"}, "provenance": provenance,
    })
    ext = grm.external_acceptance_evidence()
    assert ext["provenance"] == provenance
    assert ext["groups"]["provenance"] == "PASS"


def test_unverified_provenance_cannot_be_exposed_as_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    p = tmp_path / "reports/external_acceptance/manifest_all.json"
    p.parent.mkdir(parents=True)
    p.write_text("{}")
    monkeypatch.setattr(grm, "verify_manifest", lambda *a, **k: {
        "verified": False, "selected_all_pass": False, "manifest_sha256": "1"*64,
        "real_target_confirmed": True, "profile": "all", "problems": ["BAD"],
        "groups": {"provenance": "BLOCKED"}, "provenance": None,
    })
    ext = grm.external_acceptance_evidence()
    assert ext["status"] == "BLOCKED"
    assert ext["provenance"] is None
