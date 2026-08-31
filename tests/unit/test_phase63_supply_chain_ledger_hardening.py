from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

import pytest

from backend.app.release.evidence_ledger import append_entry, verify_ledger
from backend.app.release.supply_chain_evidence import verify_supply_chain_artifacts
import scripts.external_acceptance_runner as runner
import scripts.external.provenance_capture as provenance


def test_phase63_supply_chain_requires_license_and_semantic_verification():
    keys = {key for key, _, _ in runner.build_plan("supply-chain")}
    assert keys == {"transferred_supply_chain_verification"}
    verifier = (ROOT / "scripts/external/verify_transferred_supply_chain.py").read_text()
    assert "verify_supply_chain_artifacts" in verifier
    assert "verify_scanner_digests" in verifier
    assert "verify_build_evidence" in verifier


def test_phase63_semantic_supply_chain_verifier_accepts_realistic_artifacts(tmp_path: Path):
    sbom = tmp_path / "sbom.json"
    licenses = tmp_path / "licenses.json"
    sbom.write_text(json.dumps({"bomFormat":"CycloneDX","specVersion":"1.6","components":[{"name":"fastapi","version":"1.0"}]}))
    licenses.write_text(json.dumps([{"Name":"fastapi","Version":"1.0","License":"MIT"}]))
    result = verify_supply_chain_artifacts(sbom, licenses)
    assert result["verified"] is True
    assert result["sbom"]["components"] == 1 and result["license_report"]["packages"] == 1


def test_phase63_semantic_supply_chain_verifier_rejects_empty_or_unlicensed(tmp_path: Path):
    sbom = tmp_path / "sbom.json"
    licenses = tmp_path / "licenses.json"
    sbom.write_text(json.dumps({"bomFormat":"CycloneDX","specVersion":"1.6","components":[]}))
    licenses.write_text(json.dumps([{"Name":"x","Version":"1"}]))
    result = verify_supply_chain_artifacts(sbom, licenses)
    assert result["verified"] is False
    assert any("SBOM_COMPONENTS_EMPTY" in p for p in result["problems"])
    assert any("LICENSE_VALUE_MISSING" in p for p in result["problems"])


def test_phase63_ledger_refuses_tampered_existing_chain(tmp_path: Path):
    path = tmp_path / "evidence_ledger.json"
    append_entry(path, manifest_sha256="a"*64, challenge_id="c1", git_commit_sha="b"*40, profile="runtime")
    doc = json.loads(path.read_text())
    doc["entries"][0]["profile"] = "tampered"
    path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="invalid evidence ledger"):
        append_entry(path, manifest_sha256="d"*64, challenge_id="c1", git_commit_sha="b"*40, profile="pitr")


def test_phase63_ledger_root_binding_rejects_escape(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError, match="escapes configured root"):
        append_entry(tmp_path / "outside.json", manifest_sha256="a"*64, challenge_id="c1", git_commit_sha="b"*40, profile="runtime", root=root)


def test_phase63_provenance_contract_hashes_license_and_semantic_verification():
    source = Path(provenance.__file__).read_text(encoding="utf-8")
    assert '"license_report_hash"' in source
    assert '"supply_chain_verification_hash"' in source
