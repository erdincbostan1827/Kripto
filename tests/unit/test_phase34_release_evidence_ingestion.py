from __future__ import annotations

import json
from pathlib import Path

import scripts.generate_release_manifest as grm


def test_missing_external_manifest_is_not_tested(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    assert grm.external_acceptance_evidence()["status"] == "NOT_TESTED"


def test_simulated_or_unconfirmed_bundle_never_promotes(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    p = tmp_path / "reports/external_acceptance/manifest_all.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"profile": "all", "selected_all_pass": True,
                             "real_target_explicitly_confirmed": False}))
    out = grm.external_acceptance_evidence()
    assert out["status"] == "BLOCKED"
    assert out["real_target_confirmed"] is False
    assert len(out["sha256"]) == 64


def test_bare_confirmed_pass_claim_without_hashed_evidence_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    p = tmp_path / "reports/external_acceptance/manifest_all.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"profile": "all", "selected_all_pass": True,
                             "real_target_explicitly_confirmed": True}))
    out = grm.external_acceptance_evidence()
    assert out["status"] == "BLOCKED"
    assert out["real_target_confirmed"] is True
    assert out["verified"] is False


def test_unconfirmed_groups_cannot_promote_release_acceptance(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    p = tmp_path / "reports/external_acceptance/manifest_all.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"profile": "all", "selected_all_pass": True,
                             "real_target_explicitly_confirmed": False,
                             "groups": {"runtime": "PASS", "supply_chain": "PASS"}}))
    ext = grm.external_acceptance_evidence()
    statuses = grm.acceptance_statuses(ext)
    assert statuses["docker_runtime"] == "NOT_TESTED"
    assert statuses["supply_chain_scans_and_sbom"] == "NOT_TESTED"


def test_verified_group_pass_promotes_only_mapped_acceptance(tmp_path, monkeypatch):
    monkeypatch.setattr(grm, "ROOT", tmp_path)
    p = tmp_path / "reports/external_acceptance/manifest_all.json"
    p.parent.mkdir(parents=True)
    p.write_text("{}")
    monkeypatch.setattr(grm, "verify_manifest", lambda *a, **k: {
        "verified": True, "selected_all_pass": False, "manifest_sha256": "a" * 64,
        "real_target_confirmed": True, "profile": "all", "problems": [],
        "groups": {"runtime": "PASS", "pitr": "BLOCKED", "testnet": "NOT_TESTED"},
    })
    ext = grm.external_acceptance_evidence()
    statuses = grm.acceptance_statuses(ext)
    assert statuses["docker_runtime"] == "PASS"
    assert statuses["postgres_runtime_migration"] == "PASS"
    assert statuses["redis_runtime_integration"] == "PASS"
    assert statuses["pitr_restore_drill"] == "NOT_TESTED"
    assert statuses["credentialed_binance_testnet"] == "NOT_TESTED"
    assert statuses["credentialed_private_stream"] == "NOT_TESTED"
