from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackupRecoveryPolicy:
    rpo_minutes: int
    rto_minutes: int
    backup_frequency_minutes: int
    retention_days: int
    off_host_copy_required: bool = True
    encryption_at_rest_required: bool = True
    checksum_verification_required: bool = True
    access_control_required: bool = True
    pitr_or_managed_equivalent_required: bool = True
    restore_drill_frequency_days: int = 90

    def validate(self) -> None:
        if min(self.rpo_minutes, self.rto_minutes, self.backup_frequency_minutes, self.retention_days, self.restore_drill_frequency_days) <= 0:
            raise ValueError("recovery targets must be positive")
        if self.backup_frequency_minutes > self.rpo_minutes:
            raise ValueError("backup frequency cannot exceed RPO")
        if not all((self.off_host_copy_required, self.encryption_at_rest_required, self.checksum_verification_required, self.access_control_required, self.pitr_or_managed_equivalent_required)):
            raise ValueError("production recovery controls are mandatory")


@dataclass(frozen=True)
class RestoreDrillEvidence:
    isolated_environment: bool
    backup_or_pitr_restored: bool
    schema_validated: bool
    referential_integrity_validated: bool
    checksum_validated: bool
    read_only_smoke_passed: bool
    report_reference: str | None

    def assert_complete(self) -> None:
        checks = {
            "isolated_environment": self.isolated_environment,
            "backup_or_pitr_restored": self.backup_or_pitr_restored,
            "schema_validated": self.schema_validated,
            "referential_integrity_validated": self.referential_integrity_validated,
            "checksum_validated": self.checksum_validated,
            "read_only_smoke_passed": self.read_only_smoke_passed,
            "report_reference": bool(self.report_reference),
        }
        missing = [k for k, ok in checks.items() if not ok]
        if missing:
            raise ValueError("incomplete restore drill evidence: " + ",".join(missing))
