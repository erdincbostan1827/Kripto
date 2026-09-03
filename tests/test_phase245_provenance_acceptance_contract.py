from __future__ import annotations

import hashlib
import json
from pathlib import Path

import scripts.external.verify_phase225_transfer as transfer


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase245-provenance-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase245_provenance_acceptance.ps1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_phase245_workflow_is_exact_sha_transfer_plus_provenance_and_fail_closed() -> None:
    text = _text(WORKFLOW)
    assert "name: Phase 245 Provenance Acceptance" in text
    assert "run-name: Phase 245 Provenance Acceptance ${{ inputs.candidate_ref }}" in text
    assert "name: locate-phase225-evidence" in text
    assert 'Phase 225 Production Build Evidence' in text
    assert 'phase225-production-build-evidence-${CANDIDATE_REF,,}' in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "NODE_VERSION: '24'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "python scripts/verify_source_locks.py" in text
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in text
    assert "github-token: ${{ github.token }}" in text
    assert "run-id: ${{ needs.locate-phase225-evidence.outputs.phase225_run_id }}" in text
    assert "python scripts/external/verify_phase225_transfer.py --expected-sha $env:CANDIDATE_REF" in text
    assert "PROVENANCE_SIGN_VERIFY_COMMAND: ${{ secrets.PROVENANCE_SIGN_VERIFY_COMMAND }}" in text
    assert "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND: ${{ secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND }}" in text
    assert "python scripts/generate_acceptance_challenge.py" in text
    assert "--profile provenance --confirm-real-target" in text
    assert "manifest_provenance.json" in text
    assert "PROVENANCE_TARGET_IDENTITY.json" in text
    assert "PHASE225_TRANSFER_VERIFICATION.json" in text
    assert "production_ready = $false" in text
    assert "It does not close ledger checkpoint" in text


def test_phase245_workflow_secret_scope_is_provenance_only() -> None:
    text = _text(WORKFLOW)
    for marker in (
        "secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
        "secrets.PROVENANCE_SIGN_VERIFY_COMMAND",
    ):
        assert marker in text
    for marker in (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "RESTART_DRILL_COMMAND",
        "RESTART_EVIDENCE_JSON",
        "PITR_DRILL_COMMAND",
        "PITR_EVIDENCE_JSON",
        "HA_DRILL_COMMAND",
        "HA_EVIDENCE_JSON",
        "WORM_ACCEPTANCE_COMMAND",
        "WORM_EVIDENCE_JSON",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    ):
        assert marker not in text


def test_phase245_self_hosted_job_is_windows_native_and_binds_identity() -> None:
    text = _text(WORKFLOW)
    self_hosted = text.split("  provenance-acceptance:", 1)[1]
    assert "shell: pwsh" in self_hosted
    assert "shell: bash" not in self_hosted
    assert "reports/external_acceptance/phase245_runtime.env" in self_hosted
    assert "Pre-existing secrets directory detected after clean checkout" in self_hosted
    assert "python scripts/bootstrap_secrets.py" in self_hosted
    assert '"kripto_phase245_$shortSha"' in self_hosted
    assert "ACCEPTANCE_ENVIRONMENT_ID" in self_hosted
    assert "ACCEPTANCE_TOPOLOGY_HASH" in self_hosted
    assert "phase225_run_id = [string]$env:PHASE225_RUN_ID" in self_hosted
    assert "acceptance_image_digest = $env:ACCEPTANCE_CONTAINER_IMAGE" in self_hosted
    assert "runner_os = $env:RUNNER_OS" in self_hosted
    assert "Remove-Item -LiteralPath 'secrets' -Recurse -Force" in self_hosted


def test_phase245_orchestrator_correlates_exact_run_and_reverifies_artifact() -> None:
    text = _text(ORCHESTRATOR)
    assert "CandidateRef -notmatch '^[0-9a-fA-F]{40}$'" in text
    assert '$expectedRunTitle = "Phase 245 Provenance Acceptance $CandidateRef"' in text
    assert '"databaseId,createdAt,status,conclusion,displayTitle"' in text
    assert '($displayTitle -eq $expectedRunTitle)' in text
    assert '"workflow", "run", "Phase 245 Provenance Acceptance"' in text
    assert '"candidate_ref=$CandidateRef"' in text
    assert '& gh run watch $runId --repo $Repository --exit-status' in text
    assert '$artifactName = "phase245-provenance-acceptance-$CandidateRef"' in text
    assert '"PHASE245_PROVENANCE_RESULT.json"' in text
    assert '"PROVENANCE_TARGET_IDENTITY.json"' in text
    assert '"PHASE225_TRANSFER_VERIFICATION.json"' in text
    assert '"manifest_provenance.json"' in text
    assert '$identity.runner_os -ne "Windows"' in text
    assert '$identity.acceptance_image_digest -ne $transfer.acceptance_image_digest' in text
    assert '$manifest.environment.git_commit_sha -ne $CandidateRef' in text
    assert '$manifest.environment.topology_hash -ne $identity.topology_hash' in text
    assert '$manifest.challenge.trust_verified -eq $true' in text
    assert '$provenanceStatus -eq "PASS"' in text
    assert "PHASE245_PROVENANCE_ACCEPTANCE=PASS" in text
    assert "PHASE245_PROVENANCE_ACCEPTANCE=FAIL" in text
    assert "production_ready = $false" in text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_phase225_transfer_verifier_accepts_bound_evidence_and_rejects_tamper(tmp_path: Path, monkeypatch) -> None:
    expected = "a" * 40
    monkeypatch.setattr(transfer, "ROOT", tmp_path)
    monkeypatch.setattr(transfer, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(transfer, "EXTERNAL", tmp_path / "reports" / "external_acceptance")
    monkeypatch.setattr(transfer, "_git_sha", lambda: expected)
    monkeypatch.setattr(transfer, "verify_supply_chain_artifacts", lambda *_: {"verified": True, "problems": []})
    monkeypatch.setattr(transfer, "verify_scanner_image_digests", lambda *_: {"verified": True, "problems": []})

    uv_lock = tmp_path / "uv.lock"
    package_lock = tmp_path / "frontend" / "package-lock.json"
    sbom = tmp_path / "reports" / "external_acceptance" / "sbom.cdx.json"
    licenses = tmp_path / "reports" / "external_acceptance" / "dependency_licenses.json"
    semantic = tmp_path / "reports" / "external_acceptance" / "supply_chain_artifact_verification.json"
    scanner = tmp_path / "reports" / "external_acceptance" / "scanner_image_digests.json"
    provenance = tmp_path / "reports" / "external_acceptance" / "provenance.json"
    build = tmp_path / "reports" / "phase225" / "PRODUCTION_BUILD_EVIDENCE.json"

    uv_lock.parent.mkdir(parents=True, exist_ok=True)
    package_lock.parent.mkdir(parents=True, exist_ok=True)
    sbom.parent.mkdir(parents=True, exist_ok=True)
    uv_lock.write_text("lock\n", encoding="utf-8")
    package_lock.write_text("{}\n", encoding="utf-8")
    sbom.write_text('{"bomFormat":"CycloneDX","components":[]}\n', encoding="utf-8")
    licenses.write_text("[]\n", encoding="utf-8")
    scanner.write_text('{"schema_version":"1.0","classification":"CI_SCANNER_IMAGE_DIGEST_RECEIPT","scanners":{}}\n', encoding="utf-8")
    _write_json(
        semantic,
        {
            "classification": "SUPPLY_CHAIN_ARTIFACT_SEMANTIC_VERIFICATION",
            "verified": True,
            "sbom": {"sha256": _sha(sbom)},
            "license_report": {"sha256": _sha(licenses)},
        },
    )

    image = f"ghcr.io/erdincbostan1827/kripto/acceptance:{expected}"
    digest = "ghcr.io/erdincbostan1827/kripto/acceptance@sha256:" + "b" * 64
    _write_json(
        provenance,
        {
            "classification": "REAL_CI_BUILD_PROVENANCE",
            "git_commit_sha": expected,
            "dependency_lock_hash": _sha(uv_lock),
            "frontend_lock_hash": _sha(package_lock),
            "sbom_hash": _sha(sbom),
            "license_report_hash": _sha(licenses),
            "supply_chain_verification_hash": _sha(semantic),
            "scanner_image_digest_manifest_hash": _sha(scanner),
            "frontend_artifact_hash": "c" * 64,
            "container_image": image,
            "container_digest": digest,
            "ci_run_id": "12345",
        },
    )
    _write_json(
        build,
        {
            "classification": "PRODUCTION_BUILD_EVIDENCE_HOSTED_ONLY",
            "verified": True,
            "git_commit_sha": expected,
            "acceptance_image": image,
            "acceptance_image_digest": digest,
            "sbom_sha256": _sha(sbom),
            "provenance_sha256": _sha(provenance),
            "truth_boundary": {
                "hosted_build_evidence_passed": True,
                "real_target_acceptance_claimed": False,
                "credentialed_testnet_claimed": False,
                "restart_pitr_ha_worm_claimed": False,
                "trusted_signing_claimed": False,
                "production_live_accepted": False,
            },
        },
    )

    passed = transfer.verify(expected)
    assert passed["verified"] is True
    assert passed["problems"] == []

    sbom.write_text('{"bomFormat":"CycloneDX","components":[{"name":"tampered"}]}\n', encoding="utf-8")
    failed = transfer.verify(expected)
    assert failed["verified"] is False
    assert "BUILD_RECEIPT_SBOM_HASH_MISMATCH" in failed["problems"]
    assert "PROVENANCE_HASH_MISMATCH:sbom_hash" in failed["problems"]
