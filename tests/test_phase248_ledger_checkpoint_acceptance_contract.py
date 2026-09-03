from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "phase248-ledger-checkpoint-acceptance.yml"
ORCHESTRATOR = ROOT / "tools" / "run_phase248_ledger_checkpoint_acceptance.ps1"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase248_workflow_is_exact_sha_return_bundle_bound_and_fail_closed() -> None:
    text = _text(WORKFLOW)
    assert "name: Phase 248 Ledger Checkpoint Acceptance" in text
    assert "run-name: Phase 248 Ledger Checkpoint Acceptance ${{ inputs.candidate_ref }}" in text
    assert "runs-on: [self-hosted, production-acceptance]" in text
    assert "environment: production-acceptance" in text
    assert "PYTHON_VERSION: '3.12.10'" in text
    assert "ref: ${{ inputs.candidate_ref }}" in text
    assert "clean: true" in text
    assert "return_bundle_path must be absolute" in text
    assert "acceptance_return_bundle.py verify" in text
    assert "acceptance_return_bundle.py stage" in text
    assert "acceptance_return_promotion.py assess" in text
    assert "acceptance_return_promotion.py promote" in text
    assert "pre-signed ledger checkpoint artifacts are forbidden" in text
    assert "evidence_ledger.json" in text
    assert "ledger_checkpoint_sign_verify.py" in text
    assert "LEDGER_CHECKPOINT_VERIFICATION.json" in text
    assert "LEDGER_CHECKPOINT_SIGNATURE.bin" in text
    assert "PHASE248_LEDGER_RESULT.json" in text
    assert "production_ready = $false" in text
    assert "live_enabled = $false" in text
    assert "shell: bash" not in text


def test_phase248_workflow_secret_scope_is_ledger_only() -> None:
    text = _text(WORKFLOW)
    required = (
        "secrets.ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
        "secrets.LEDGER_CHECKPOINT_SIGN_COMMAND",
        "secrets.ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND",
        "vars.ACCEPTANCE_ENVIRONMENT_ID",
        "vars.ACCEPTANCE_TOPOLOGY_HASH",
    )
    for marker in required:
        assert marker in text
    for forbidden in (
        "BINANCE_TESTNET_API_KEY",
        "BINANCE_TESTNET_API_SECRET",
        "RESTART_DRILL_COMMAND",
        "PITR_DRILL_COMMAND",
        "HA_DRILL_COMMAND",
        "WORM_ACCEPTANCE_COMMAND",
        "PROVENANCE_SIGN_VERIFY_COMMAND",
        "CAMPAIGN_BUNDLE_PATH",
    ):
        assert forbidden not in text


def test_phase248_workflow_requires_atomic_semantic_promotion_before_signing() -> None:
    text = _text(WORKFLOW)
    promote = text.index("acceptance_return_promotion.py promote")
    ledger_required = text.index("Promoted evidence ledger is missing")
    pre_checkpoint = text.index("A checkpoint unexpectedly existed before Phase 248 signing")
    sign = text.index("ledger_checkpoint_sign_verify.py")
    assert promote < ledger_required < pre_checkpoint < sign
    assert "$promotion.promoted -ne $true" in text
    assert "$promotion.rolled_back -eq $true" in text
    assert "$verification.trust_verified -eq $true" in text
    assert "$verification.ledger_head_hash -eq $checkpoint.ledger_head_hash" in text
    assert "[int64]$verification.ledger_entries -eq [int64]$checkpoint.ledger_entries" in text


def test_phase248_orchestrator_correlates_exact_run_and_detects_bundle_toc_tou() -> None:
    text = _text(ORCHESTRATOR)
    assert "Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256" in text
    assert '$expectedRunTitle = "Phase 248 Ledger Checkpoint Acceptance $CandidateRef"' in text
    assert '"workflow", "run", "Phase 248 Ledger Checkpoint Acceptance"' in text
    assert '"candidate_ref=$CandidateRef"' in text
    assert '"return_bundle_path=$bundleFullPath"' in text
    assert '"return_bundle_sha256=$bundleSha"' in text
    assert "($displayTitle -eq $expectedRunTitle)" in text
    assert "Return bundle changed during Phase 248 execution" in text
    assert '$artifactName = "phase248-ledger-checkpoint-$CandidateRef"' in text
    assert "PHASE248_LEDGER_RESULT.json" in text
    assert "LEDGER_TARGET_IDENTITY.json" in text
    assert "RETURN_PROMOTION_RESULT.json" in text
    assert "LEDGER_CHECKPOINT_VERIFICATION.json" in text
    assert "LEDGER_CHECKPOINT_SIGNATURE.bin" in text


def test_phase248_orchestrator_reverifies_identity_promotion_trust_and_signature() -> None:
    text = _text(ORCHESTRATOR)
    assert '$identity.runner_os -ne "Windows"' in text
    assert "$promotion.verified -ne $true" in text
    assert "$promotion.promoted -ne $true" in text
    assert "$promotion.rolled_back -eq $true" in text
    assert "$checkpoint.real_system -ne $true" in text
    assert "$checkpoint.executed -ne $true" in text
    assert "$checkpoint.signature_verified -ne $true" in text
    assert "$verification.verified -ne $true" in text
    assert "$verification.trust_verified -ne $true" in text
    assert "Ledger checkpoint head/count binding mismatch" in text
    assert "Downloaded checkpoint signature hash mismatch" in text
    assert "PHASE248_LEDGER_CHECKPOINT_ACCEPTANCE=PASS" in text
    assert "PHASE248_LEDGER_CHECKPOINT_ACCEPTANCE=FAIL" in text
    assert "production_ready = $false" in text
    assert "live_enabled = $false" in text
