# Backup / Restore / PITR Acceptance

Canonical production targets: **RPO 15 minutes**, **RTO 60 minutes**. These are design targets, not measured claims until a production-like restore drill is completed.

- Logical backup: `scripts/backup.sh` / `scripts/backup.ps1`, checksum mandatory.
- Restore: checksum verification occurs before `pg_restore`.
- Production PITR profile: PostgreSQL WAL archiving or managed-database PITR with off-host encrypted storage is required.
- Trading state, orders/fills/ledger, audit evidence, strategy/config snapshots and universe metadata are in the database backup scope.
- Secrets are excluded from plaintext DB backup policy and are restored through the production secret provider.
- `scripts/restore_drill.sh` restores into an isolated PostgreSQL 18.6 container and checks schema presence. Full referential-integrity/read-only application smoke is required in a Docker-capable acceptance environment.
- If the restore drill has not actually run, backup health must be reported `UNKNOWN/DEGRADED`, never `PASS`.

## Phase 189 — restore evidence freshness and environment identity

Restore-drill receipts are schema `1.1` evidence and must include an explicit `CTP_ENVIRONMENT_ID`. The receipt binds that identifier through `environment_fingerprint` and records a timezone-aware completion timestamp. Migration backup receipts are issued only from a fresh restore-drill receipt for the same backup SHA256 and the same environment identity. The default verification freshness window is 24 hours; stale or cross-environment evidence is rejected fail-closed.
