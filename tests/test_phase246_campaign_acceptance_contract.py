from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from scripts.external.stage_campaign_evidence_bundle import CLASSIFICATION, MANIFEST_NAME, verify_and_stage

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase246-campaign-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase246_campaign_acceptance.ps1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_phase246_workflow_is_exact_sha_bundle_bound_and_fail_closed() -> None:
    text = _text(WORKFLOW)
    assert "name: Phase 246 Campaign Acceptance" in text
    assert "run-name: Phase 246 Campaign Acceptance ${{ inputs.candidate_ref }}" in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "clean: true" in text
    assert "bundle_path must be absolute" in text
    assert "scripts/external/stage_campaign_evidence_bundle.py" in text
    assert "--profile campaigns --confirm-real-target" in text
    assert "manifest_campaigns.json" in text
    assert "CAMPAIGN_BUNDLE_TRANSFER_VERIFICATION.json" in text
    assert "CAMPAIGN_TARGET_IDENTITY.json" in text
    assert "private_stream_group" in text
    assert "paper_campaign_group" in text
    assert "live_shadow_group" in text
    assert "profitability_group" in text
    assert "live_enabled = $false" in text
    assert "production_ready = $false" in text
    assert "zero real order submissions" in text


def test_phase246_workflow_secret_scope_is_campaign_only() -> None:
    text = _text(WORKFLOW)
    assert "secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND" in text
    for forbidden in (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "RESTART_DRILL_COMMAND",
        "PITR_DRILL_COMMAND",
        "HA_DRILL_COMMAND",
        "WORM_ACCEPTANCE_COMMAND",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "LEDGER_CHECKPOINT_SIGN_COMMAND",
        "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
    ):
        assert forbidden not in text


def test_phase246_orchestrator_correlates_exact_run_and_prevents_bundle_toc_tou() -> None:
    text = _text(ORCHESTRATOR)
    assert "Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256" in text
    assert '$expectedRunTitle = "Phase 246 Campaign Acceptance $CandidateRef"' in text
    assert '"workflow", "run", "Phase 246 Campaign Acceptance"' in text
    assert '"bundle_path=$bundleFullPath"' in text
    assert '"bundle_sha256=$bundleSha"' in text
    assert '($displayTitle -eq $expectedRunTitle)' in text
    assert "Campaign evidence bundle changed during acceptance execution" in text
    assert '$artifactName = "phase246-campaign-acceptance-$CandidateRef"' in text
    assert "PHASE246_CAMPAIGN_RESULT.json" in text
    assert "CAMPAIGN_BUNDLE_TRANSFER_VERIFICATION.json" in text
    assert "manifest_campaigns.json" in text
    assert '$identity.runner_os -ne "Windows"' in text
    assert "$manifest.challenge.trust_verified -eq $true" in text
    assert "$manifest.selected_all_pass -eq $true" in text
    assert "real_orders_submitted" in text
    assert "exchange_submit_calls" in text
    assert "PHASE246_CAMPAIGN_ACCEPTANCE=PASS" in text
    assert "PHASE246_CAMPAIGN_ACCEPTANCE=FAIL" in text


def _receipt(source: str, data: bytes) -> bytes:
    return (json.dumps({"source_artifacts": [{"path": source, "sha256": _sha(data)}]}, sort_keys=True) + "\n").encode()


def _write_bundle(path: Path, *, candidate: str, tamper_hash: bool = False, traversal: bool = False) -> str:
    source = "reports/external_acceptance/campaign/source/events.jsonl"
    source_data = b'{"event":"ok"}\n'
    files: dict[str, bytes] = {
        "reports/external_acceptance/release_challenge.json": b'{"schema_version":"1.0"}\n',
        "reports/external_acceptance/campaign/private_stream.json": _receipt(source, source_data),
        "reports/external_acceptance/campaign/paper_campaign.json": _receipt(source, source_data),
        "reports/external_acceptance/campaign/live_shadow.json": _receipt(source, source_data),
        "reports/external_acceptance/campaign/profitability.json": _receipt(source, source_data),
        source: source_data,
    }
    if traversal:
        files["../escape.txt"] = b"escape"
    hashes = {name: _sha(data) for name, data in files.items()}
    if tamper_hash:
        hashes[source] = "0" * 64
    manifest = {
        "schema_version": "1.0",
        "classification": CLASSIFICATION,
        "candidate_sha": candidate,
        "acceptance_environment_id": "campaign-env-1",
        "topology_hash": "a" * 64,
        "files": hashes,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, json.dumps(manifest, sort_keys=True))
        for name, data in files.items():
            archive.writestr(name, data)
    return _sha(path.read_bytes())


def test_campaign_bundle_staging_accepts_exact_hash_and_stages_only_bound_files(tmp_path: Path) -> None:
    candidate = "b" * 40
    bundle = tmp_path / "campaign.zip"
    digest = _write_bundle(bundle, candidate=candidate)
    root = tmp_path / "repo"
    root.mkdir()
    result = verify_and_stage(bundle.resolve(), expected_sha256=digest, expected_candidate=candidate, root=root)
    assert result["verified"] is True
    assert result["candidate_sha"] == candidate
    assert result["bundle_sha256"] == digest
    assert result["staged_file_count"] == 6
    assert result["referenced_source_artifact_count"] == 1
    assert (root / "reports/external_acceptance/campaign/private_stream.json").is_file()
    assert (root / "reports/external_acceptance/campaign/source/events.jsonl").read_bytes() == b'{"event":"ok"}\n'


def test_campaign_bundle_staging_rejects_member_hash_tamper(tmp_path: Path) -> None:
    candidate = "c" * 40
    bundle = tmp_path / "campaign-tampered.zip"
    digest = _write_bundle(bundle, candidate=candidate, tamper_hash=True)
    root = tmp_path / "repo"
    root.mkdir()
    result = verify_and_stage(bundle.resolve(), expected_sha256=digest, expected_candidate=candidate, root=root)
    assert result["verified"] is False
    assert "BUNDLE_MEMBER_SHA256_MISMATCH" in result["problems"]
    assert not (root / "reports/external_acceptance/campaign").exists()


def test_campaign_bundle_staging_rejects_path_traversal(tmp_path: Path) -> None:
    candidate = "d" * 40
    bundle = tmp_path / "campaign-traversal.zip"
    digest = _write_bundle(bundle, candidate=candidate, traversal=True)
    root = tmp_path / "repo"
    root.mkdir()
    result = verify_and_stage(bundle.resolve(), expected_sha256=digest, expected_candidate=candidate, root=root)
    assert result["verified"] is False
    assert "ARCHIVE_MEMBER_PATH_UNSAFE" in result["problems"]
    assert not (tmp_path / "escape.txt").exists()
