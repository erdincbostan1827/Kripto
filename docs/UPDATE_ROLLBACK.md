# Update / Rollback Prosedürü

Güncellemeden önce şifreli backup alın ve restore doğrulamasını ayrı bir hedef veritabanında yapın. Migration'lar backward-compatible expand/roll-forward yaklaşımıyla uygulanmalı; frontend/backend API compatibility penceresi korunmalıdır. Yeni server sürümü health/readiness ve migration kontrollerinden geçmeden trafik almamalıdır. Rollback kararı schema compatibility, config migration ve mevcut açık pozisyon/reconciliation durumunu dikkate alır. İmzalı paket/auto-update kanıtı yoksa manuel update açıkça tercih edilir; unsigned artifact production acceptance sayılmaz.

## Restore güvenlik sözleşmesi

`scripts/restore.sh` ve `scripts/restore.ps1` mevcut hedef veritabanını ezmez. `trading`, `postgres`, `template0` ve `template1` hedefleri restore için reddedilir; hedef adları yalnızca güvenli PostgreSQL identifier biçiminde kabul edilir.

Restore önce checksum doğrulaması yapar, ardından yeni bir staging veritabanı oluşturur. Şifreli backup yalnızca bu staging veritabanına `pg_restore --exit-on-error` ile yüklenir. Restore tamamen başarılı olursa staging veritabanı hedef ada atomik rename ile terfi ettirilir. Hata oluşursa staging veritabanı temizlenir; kullanıcıya yarım restore edilmiş bir hedef veritabanı bırakılmaz.

Gerçek production rollback yalnızca backup bulunmasına dayanmaz. Restore drill, migration compatibility, runtime health, açık emir/pozisyon reconciliation ve external production acceptance kanıtları ayrıca PASS olmalıdır. Bu kontroller tamamlanmadığında PROD LIVE blokajı korunur.

## Dependency-lock transaction recovery

Dependency lock generation is treated as a two-file transaction. `uv.lock` and `frontend/package-lock.json` are resolved outside canonical paths, backed by a durable rollback journal, and promoted only as a verified pair. If the process is interrupted between promotions, the next installer/bootstrap start runs `scripts/bootstrap_dependency_locks.py --recover-only` and restores the exact pre-transaction state before any secret generation, build, migration, or service startup. Invalid or externally redirected transaction journals fail closed.

## Secret bootstrap hardening

Secret bootstrap uses exclusive create-once file creation with restrictive permissions. Existing secret files are retained only when they are non-empty regular files; symlinks, special files, an unsafe `secrets` directory, or an empty secret fail closed. A failed first write removes the incomplete newly-created secret rather than leaving partial credential material behind.

## Transactional manual release update

Manual source updates use `scripts/transactional_release_update.py`. The candidate source ZIP is safety-scanned, package-manifest verified, extracted into a sibling staging directory, and source identity is verified before cutover. The active tree is renamed to a rollback directory and the verified candidate is promoted by same-filesystem directory rename. A durable `.release-update.transaction.json` journal exists across the cutover window.

If the process or host stops while that journal exists, the next `--recover-only` invocation restores the pre-update active tree and discards the uncommitted candidate. A surviving journal is never interpreted as a successful update. After a successful cutover the previous active tree remains in a `.release-update-rollback-*` directory until runtime health, migration compatibility, reconciliation, and operator acceptance are complete. Explicit rollback requires that exact sibling rollback directory and rejects redirected/symlink paths.

The installer also creates `.env` through `scripts/bootstrap_env.py` using exclusive create-once semantics. Existing `.env` is retained only when it is a non-empty regular file; symlinks and unsafe file types fail closed, and an interrupted first write removes the partial file.

## Phase 186 — post-cutover acceptance and hash-bound rollback

`transactional_release_update.py` now keeps the update journal authoritative until the promoted tree passes a fail-closed post-cutover contract. The built-in static binding verifies the extracted source-package identity, requires `RELEASE_MANIFEST.json.git_commit_sha` to match the package manifest identity, requires the release migration version to equal the single Alembic head, and requires the recorded architecture-profile SHA-256 to match the promoted file.

An optional `--acceptance-command-json '["program","arg",...]'` can execute a local runtime/health acceptance command after cutover. It is executed with `shell=False`; non-zero exit or timeout rejects the candidate while the transaction journal still exists, causing deterministic restoration of the pre-update tree. This command is an operator-supplied runtime gate; it does not turn unavailable Docker, database, exchange, browser, or production acceptance into PASS.

After successful acceptance, the retained rollback directory is accompanied by a `*.receipt.json` containing its deterministic tree hash. Explicit rollback requires that receipt and verifies the complete rollback tree before moving the active tree. A missing, unsafe, malformed, redirected, or hash-mismatched rollback receipt fails closed without changing the active release.

## Phase 187 — guarded database migration contract

Release cutover must not infer database rollback safety from Alembic files alone. `MIGRATION_COMPATIBILITY.json` classifies every revision and the updater compares the active and candidate migration heads before moving the active tree.

If the candidate introduces a new migration head, the generic release updater fails closed until a `VERIFIED_DATABASE_MIGRATION_RECEIPT` is supplied. That receipt can only be produced by `scripts/database_migration_guard.py`, which requires a hash-bound `VERIFIED_DATABASE_BACKUP_RECEIPT`, verifies the authoritative database head before migration, executes the migration command without a shell, verifies the authoritative target head after migration, and preserves a transaction journal across interruption.

Recovery never guesses. If an interrupted migration probe reports the original head, the transaction is classified as not applied and the journal is cleared. If it reports the target head, a verified migration receipt is finalized. Any other head is `DATABASE_MIGRATION_STATE_AMBIGUOUS`; the journal is retained and deployment remains blocked for operator recovery. Destructive downgrade support is never inferred.

A successful code cutover now emits a provenance-hashed `VERIFIED_RELEASE_UPDATE_ACCEPTANCE_RECEIPT`. The rollback receipt is cryptographically bound to that acceptance receipt. Tampering with either the rollback tree or acceptance provenance causes rollback to fail closed before the active tree is moved.

These controls do not prove production database recovery, PITR, HA, Docker runtime, exchange credentials, or live-market readiness. Those external acceptance items remain separate release blockers until executed in the target environment.

## Phase 188 single-writer and restore-drill evidence policy

Install, release update, release rollback and guarded database migration use the same deployment-parent operation lock. A concurrent writer is rejected fail-closed; a live owner lock is never stolen. A stale lock may be recovered only when its recorded PID is no longer alive and the configured minimum age has elapsed. Symlink or malformed lock files are rejected.

A database backup hash alone is not sufficient to authorize a schema-changing update. `scripts/restore_drill.sh` produces a `VERIFIED_DATABASE_RESTORE_DRILL_RECEIPT` only after the disposable PostgreSQL restore and smoke checks succeed. `scripts/database_backup_receipt.py` binds that receipt, the backup artifact hash, the active release tree hash and the current migration head. `scripts/database_migration_guard.py` refuses a backup receipt whose restore-drill receipt is missing, tampered, for another backup, or not PASS. This mechanism does not claim a production restore drill when Docker/PostgreSQL are unavailable.

`scripts/release_acceptance_attestation.py` can build a canonical, signable acceptance attestation that binds the release acceptance receipt and package provenance (and optionally a migration receipt). Locally generated attestations are explicitly `UNSIGNED`; they are not trusted CI/signing provenance until an authorized external signing system supplies and verifies a signature.

## Phase 189 — PID-reuse-safe operation ownership and DB-aware rollback

The deployment mutex records the host, boot identity, and process creation identity in addition to the PID. A matching live PID is not sufficient to prove ownership: a changed process-start identity is treated as PID reuse, while a lock from another host is never stolen automatically. Stale recovery re-reads the token immediately before unlinking so a concurrently replaced lock is not deleted.

When a release acceptance receipt is bound to a guarded database migration receipt, explicit code rollback requires an authoritative database-head probe. Rollback is allowed only when the database is already at the rollback release head, or when it remains at the newer head and the migration compatibility contract proves `previous_release_compatible=true`. Any third/ambiguous database head is fail-closed and the active release tree is left untouched.

## Phase 190 rollback runtime acceptance and provenance graph

Rollback can now require a post-cutover runtime acceptance command. The command is executed without a shell after the rollback tree is promoted. A non-zero result, timeout, or static runtime-binding failure aborts the rollback and atomically restores the pre-rollback active release; rollback and acceptance evidence are preserved for inspection/retry.

The deployment operation lock now maintains a heartbeat lease while a long-running install/update/rollback/migration operation owns the single-writer lock. Stale recovery uses the latest heartbeat epoch rather than only creation time and still requires owner-identity/liveness checks and token continuity before removal.

`scripts/release_provenance_graph.py` can build a hash-closed local graph across restore-drill, database-backup, database-migration, release-acceptance, rollback, and package-provenance receipts. The local graph is explicitly `UNSIGNED` and is not trusted CI provenance until an external signing system supplies a trusted signature.

## Phase 191 deployment transaction integrity

- The platform operation lock heartbeat is now an actively checked lease. `operation_lock_exec.py` monitors ownership while a child command runs and terminates the child if heartbeat ownership is lost or tampered with; body exceptions are never suppressed by lock cleanup.
- Release update, rollback, and guarded database migration inspect the unified deployment transaction state while holding the single-writer mutex. A surviving transaction journal from another mutation class fails closed instead of allowing overlapping recovery assumptions.
- A successful explicit rollback emits `VERIFIED_RELEASE_ROLLBACK_ACCEPTANCE_RECEIPT` and a tamper-evident deployment audit-chain event. Failed rollback runtime acceptance still restores the pre-rollback active release and does not emit an accepted receipt.
- Trusted-signing support is deliberately adapter-only: local code can create a canonical signing request and attach externally produced signature bytes, but marks them `SIGNED_EXTERNAL_UNVERIFIED`. Only the external trusted CI/verifier may promote that evidence to trusted provenance.

## Phase 192 deployment audit and external trust verification

Successful install health acceptance, guarded database migration commits, transactional release update acceptance, and accepted rollback are recorded in the tamper-evident deployment audit chain. The audit writer verifies the complete existing hash chain before appending and fsyncs each event. A damaged chain fails closed and blocks a new accepted mutation from being recorded as clean.

Rollback acceptance receipts can be included as first-class nodes in `scripts/release_provenance_graph.py`. The graph then hash-binds the rollback acceptance receipt to both the original rollback receipt and the update acceptance receipt.

`trusted_signing_adapter.py` does not turn an attached signature blob into trusted provenance. `request` prepares a signing request; `attach` creates only `SIGNED_EXTERNAL_UNVERIFIED`. Trust requires the separate `verify` contract to execute an explicit argv-based external verifier without a shell. The verifier must return a successful JSON verdict binding `subject_sha256`, `canonical_payload_sha256`, and `signing_identity`. Only then is a `TRUSTED_SIGNING_VERIFICATION_RECEIPT` created. Local generation of that receipt without a successful external verifier is intentionally impossible through this adapter.
