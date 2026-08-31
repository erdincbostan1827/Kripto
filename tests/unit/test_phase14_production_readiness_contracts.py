import pytest

from backend.app.availability.profile import AvailabilityProfile, AvailabilityTier, FailoverEvidence
from backend.app.recovery.policy import BackupRecoveryPolicy, RestoreDrillEvidence
from backend.app.release.provenance import ReleaseAttestation, sign_attestation, verify_attestation


def _attestation(**overrides):
    data = dict(
        release_id="1.2.3", git_commit_sha="a"*40, source_tree_hash="b"*64,
        ci_run_id="ci-123", build_timestamp="2026-08-28T00:00:00Z",
        dependency_lock_hash="c"*64, sbom_hash="d"*64,
        container_digest="sha256:"+"e"*64, frontend_artifact_hash="f"*64,
        migration_version="0003", architecture_profile_hash="1"*64,
        requirement_matrix_hash="2"*64, test_evidence_reference="reports/LATEST_PYTEST.txt",
    )
    data.update(overrides)
    return ReleaseAttestation(**data)


def test_release_attestation_is_tamper_evident_and_requires_production_provenance():
    att = _attestation()
    att.assert_production_complete()
    key = b"k" * 32
    sig = sign_attestation(att, key)
    assert verify_attestation(att, sig, key)
    assert not verify_attestation(_attestation(ci_run_id="ci-124"), sig, key)
    with pytest.raises(ValueError, match="dependency_lock_hash"):
        _attestation(dependency_lock_hash=None).assert_production_complete()


def test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls():
    policy = BackupRecoveryPolicy(15, 60, 10, 30)
    policy.validate()
    with pytest.raises(ValueError, match="RPO"):
        BackupRecoveryPolicy(5, 60, 10, 30).validate()
    with pytest.raises(ValueError, match="mandatory"):
        BackupRecoveryPolicy(15, 60, 10, 30, off_host_copy_required=False).validate()


def test_restore_drill_cannot_be_reported_complete_without_all_evidence():
    complete = RestoreDrillEvidence(True, True, True, True, True, True, "reports/restore-2026-08.md")
    complete.assert_complete()
    with pytest.raises(ValueError, match="read_only_smoke_passed"):
        RestoreDrillEvidence(True, True, True, True, True, False, "report").assert_complete()


def test_single_host_profile_requires_external_backup_restart_reconciliation_and_downtime_disclosure():
    AvailabilityProfile(AvailabilityTier.SINGLE_HOST, True, True, True).validate()
    with pytest.raises(ValueError, match="downtime"):
        AvailabilityProfile(AvailabilityTier.SINGLE_HOST, True, True, False).validate()


def test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover():
    full = AvailabilityProfile(AvailabilityTier.HA_STANDBY, True, True, True, True, True, True, True, True)
    full.validate()
    with pytest.raises(ValueError, match="standby_trading_engine"):
        AvailabilityProfile(AvailabilityTier.HA_STANDBY, True, True, True, True, True, False, True, True).validate()


def test_ha_failover_evidence_is_fail_closed_until_every_drill_passes():
    with pytest.raises(ValueError, match="host_loss_simulation_passed"):
        FailoverEvidence(True, True, True).assert_ha_drill_complete()
    FailoverEvidence(True, True, True, True, True, True, True).assert_ha_drill_complete()
