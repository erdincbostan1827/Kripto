from __future__ import annotations

import json
from pathlib import Path

import scripts.external.provenance_capture as provenance
from scripts.external.verify_scanner_image_digests import verify

ROOT = Path(__file__).resolve().parents[2]


def _receipt(path: Path, *, digest: str = "a" * 64) -> None:
    path.write_text(json.dumps({
        "schema_version": "1.0",
        "classification": "CI_SCANNER_IMAGE_DIGEST_RECEIPT",
        "scanners": {
            "gitleaks": {"requested_image": "ghcr.io/gitleaks/gitleaks:v8.28.0", "resolved_digest": "ghcr.io/gitleaks/gitleaks@sha256:" + digest},
            "trivy": {"requested_image": "aquasec/trivy:0.65.0", "resolved_digest": "aquasec/trivy@sha256:" + digest},
            "syft": {"requested_image": "anchore/syft:v1.32.0", "resolved_digest": "anchore/syft@sha256:" + digest},
        },
    }))


def test_scanner_digest_receipt_requires_all_three_immutable_repodeigests(tmp_path: Path):
    path = tmp_path / "scanner_image_digests.json"
    _receipt(path)
    assert verify(path)["verified"] is True
    data = json.loads(path.read_text())
    data["scanners"]["trivy"]["resolved_digest"] = "aquasec/trivy:0.65.0"
    path.write_text(json.dumps(data))
    result = verify(path)
    assert result["verified"] is False
    assert "SCANNER_REPODIGEST_INVALID:trivy" in result["problems"]


def test_scanner_digest_receipt_rejects_missing_scanner(tmp_path: Path):
    path = tmp_path / "scanner_image_digests.json"
    _receipt(path)
    data = json.loads(path.read_text())
    del data["scanners"]["syft"]
    path.write_text(json.dumps(data))
    result = verify(path)
    assert not result["verified"]
    assert "SCANNER_DIGEST_SET_MISMATCH" in result["problems"]


def test_provenance_contract_requires_scanner_digest_manifest():
    source = Path(provenance.__file__).read_text(encoding="utf-8")
    assert '"scanner_image_digest_manifest_hash"' in source
    verifier = (ROOT / "scripts/verify_external_acceptance.py").read_text(encoding="utf-8")
    assert '"scanner_image_digest_manifest_hash"' in verifier


def test_production_workflow_runs_scanners_by_resolved_digest_and_uploads_receipt():
    workflow = (ROOT / ".github/workflows/production-acceptance.yml").read_text(encoding="utf-8")
    assert "Resolve scanner images to immutable digests" in workflow
    assert '"$GITLEAKS_DIGEST" detect' in workflow
    assert '"$TRIVY_DIGEST" fs' in workflow
    assert '"$SYFT_DIGEST" dir:/repo' in workflow
    assert "verify_scanner_image_digests.py" in workflow
    assert "scanner_image_digests.json" in workflow
    # Scanner execution must not use the mutable image tag directly.
    assert 'ghcr.io/gitleaks/gitleaks:v8.28.0 detect' not in workflow
    assert 'aquasec/trivy:0.65.0 fs' not in workflow
    assert 'anchore/syft:v1.32.0 dir:/repo' not in workflow


def test_recovery_lineage_is_explicitly_non_production_and_binds_verified_phase82_archive():
    payload = json.loads((ROOT / "SOURCE_RECOVERY_LINEAGE.json").read_text(encoding="utf-8"))
    assert payload["classification"] == "RECOVERED_SOURCE_BASELINE_NOT_ORIGINAL_GIT_HISTORY"
    assert payload["original_git_commit_sha"] == "767dcf8e215850b5b81e773de29e74c8c6538df8"
    assert payload["source_archive_sha256"] == "0d7cb6526b09304302ea91014b30b663861e72e945746f1072bc90df07668c91"
    assert "not production acceptance evidence" in payload["truth_policy"].lower()


def test_production_workflow_fail_closed_verifies_cross_job_build_evidence_manifest():
    workflow = (ROOT / ".github/workflows/production-acceptance.yml").read_text(encoding="utf-8")
    assert "ci_build_evidence_manifest.py create" in workflow
    assert "reports/CI_BUILD_EVIDENCE_MANIFEST.json" in workflow
    assert 'ci_build_evidence_manifest.py verify' in workflow
    assert '--expected-git-sha' in workflow
    assert '--expected-run-id' in workflow
