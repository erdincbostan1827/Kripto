from pathlib import Path


WORKFLOW = Path(".github/workflows/production-acceptance.yml")
WRAPPER = Path("tools/run_phase251_final_production_acceptance.ps1")
HANDOFF = Path("scripts/external/final_campaign_bundle_handoff.py")


def test_final_workflow_requires_exact_campaign_bundle_before_preflight() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    required = (
        "campaign_bundle_path:",
        "campaign_bundle_sha256:",
        "Verify and stage exact campaign evidence handoff",
        "scripts/external/final_campaign_bundle_handoff.py",
        "--expected-candidate $env:EXPECTED_ACCEPTANCE_SHA",
        "--expected-environment-id $env:ACCEPTANCE_ENVIRONMENT_ID",
        "--expected-topology-hash $env:ACCEPTANCE_TOPOLOGY_HASH",
        'ACCEPTANCE_REQUIRE_CHALLENGE_TRUST: "1"',
        "reports/phase251/FINAL_CAMPAIGN_HANDOFF_VERIFICATION.json",
        "python scripts/production_acceptance_orchestrator.py --confirm-real-target --reuse-current-challenge",
        "reports/phase251/**",
    )
    for needle in required:
        assert needle in text
    handoff_index = text.index("Verify and stage exact campaign evidence handoff")
    preflight_index = text.index("Fail-closed production real-target preflight")
    orchestrator_index = text.index("Run fail-closed real-target orchestrator")
    assert handoff_index < preflight_index < orchestrator_index


def test_handoff_is_fail_closed_and_keeps_live_disabled() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    required = (
        "BUNDLE_MUST_BE_OUTSIDE_REPOSITORY",
        "verify_and_stage(",
        "CAMPAIGN_ENVIRONMENT_ID_MISMATCH",
        "CAMPAIGN_TOPOLOGY_HASH_MISMATCH",
        "PROMOTION_DESTINATION_ALREADY_EXISTS",
        "verify_challenge(",
        "require_trust=True",
        "verify_campaign_evidence(",
        '"private-stream"',
        '"paper"',
        '"live-shadow"',
        '"profitability"',
        "LIVE_SHADOW_ORDER_SUBMISSION_DETECTED",
        '"classification": "PHASE251_FINAL_CAMPAIGN_HANDOFF_VERIFICATION"',
        '"live_enabled": False',
        '"production_ready": False',
    )
    for needle in required:
        assert needle in text
    assert "uuid.uuid4().hex" in text


def test_operator_wrapper_binds_bundle_run_and_human_approval_boundary() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    required = (
        "[Parameter(Mandatory = $true)][string]$CampaignEvidenceBundlePath",
        "Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256",
        '"campaign_bundle_path=$bundleFullPath"',
        '"campaign_bundle_sha256=$bundleSha"',
        '"acceptance_ref=$CandidateRef"',
        '"headSha"',
        '"real-target-evidence-$CandidateRef"',
        '"FINAL_CAMPAIGN_HANDOFF_VERIFICATION.json"',
        '"PHASE251_FINAL_CAMPAIGN_HANDOFF_VERIFICATION"',
        '"reuse_current_challenge"',
        '"PHASE251_FINAL_PRODUCTION_ACCEPTANCE=PASS"',
        '"LIVE remains disabled. Separate human approval is required before any LIVE enablement."',
        "Refusing to overwrite existing Phase 251 evidence directory",
        "FINAL_ACCEPTANCE_REQUIRES_CURRENT_REMOTE_MAIN",
        "REMOTE_MAIN_MOVED_DURING_ACCEPTANCE",
    )
    for needle in required:
        assert needle in text
    for profile in (
        "locks", "runtime", "restart-drills", "supply-chain", "pitr",
        "ha", "worm", "testnet", "provenance", "campaigns",
    ):
        assert f'"{profile}"' in text
    assert "Remove-Item" not in text
