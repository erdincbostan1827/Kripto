# Phase 24 External Acceptance Runbook

This runbook covers evidence that cannot be honestly produced by the local acceptance environment. Local/mock evidence must never be promoted to production evidence.

## Evidence truth rules

Every external acceptance result must identify the environment, the real system used, the exact command/scenario, exit code, UTC timestamp, artifact path and SHA-256. Mock/simulated execution cannot satisfy a real-runtime or credentialed gate.

## Runtime integration and restart drills

Use isolated non-production PostgreSQL and Redis instances. Run schema/migration checks, create representative state, restart the service, reconnect, reconcile and verify state/invariants. Capture service logs and test output. Redis/PostgreSQL restart requirements remain NOT_TESTED until these real services are available.

## Binance TESTNET

Use dedicated TESTNET credentials with minimum permissions. Exercise market order, limit order, cancel and partial-fill/reconciliation scenarios. Capture request correlation IDs and sanitized exchange responses. Never reuse LIVE credentials. TESTNET evidence does not enable LIVE by itself.

## Supply-chain acceptance

Generate resolved backend/frontend lock files. Run vulnerability scanning, SAST, secret scanning and license reporting with identified tool/version. Generate CycloneDX or SPDX SBOM and hash it. Container/image signing and verification require a real built image/package and signing identity. Tool absence is a blocker, not PASS.

## PITR / restore drill

In an isolated environment restore backup/PITR to the target point, validate schema/migrations, verify checksums/evidence and run read-only application smoke tests. Record achieved RPO/RTO and preserve logs. A policy document alone is not restore evidence.

## HA / failover

Run host-loss, DB failover, applicable Redis failover and network-partition drills. Validate leader fencing, reconciliation and no duplicate exchange side effects. Capture exact topology and timestamps.

## Build provenance

A production artifact must bind real git commit SHA, CI run ID, dependency lock hash, SBOM hash, container digest and frontend artifact hash. If signing is enabled, deployment must verify the signature before activation.

## LIVE-safety campaigns

Promotion requires sufficient calendar duration, multiple market regimes, adequate action samples for the active market type, fee/slippage/latency stress, independent OOS evidence and bounded execution divergence. PAPER/TESTNET/LIVE-shadow evidence must remain distinct.

## Phase 33 one-command evidence runner

Run `python scripts/external_acceptance_runner.py --profile all` first without confirmation to obtain a fail-closed diagnostic bundle. On the isolated target acceptance host, after verifying that Docker/services/tooling and the intended TESTNET environment are real, run with `--confirm-real-target`. This flag is an explicit operator attestation only; it cannot override missing tools, non-zero commands, missing credentials or missing evidence.

Profiles can be executed independently: `locks`, `runtime`, `supply-chain`, `pitr`, `ha`, and `testnet`. Evidence is written under `reports/external_acceptance/` with UTC observation time and SHA-256. Credential values are never persisted; only `PRESENT_REDACTED` or missing-variable names are recorded.

For PITR and HA profiles, set `PITR_DRILL_COMMAND` and `HA_DRILL_COMMAND` to organization-approved commands that operate only on the isolated acceptance topology. The repository intentionally does not guess destructive infrastructure commands. The TESTNET profile is fail-closed until the project-specific credentialed scenario adapter is wired to the target acceptance environment; possession of credentials alone is not acceptance evidence.

## Phase 36–40 evidence integrity and operator inputs

External evidence is re-verified before release-manifest ingestion. A claimed PASS is rejected if an evidence artifact is missing, its SHA-256 does not match, the bundle is stale, the real-target attestation is absent, the evidence was produced from a different git commit, or a group is marked PASS without every required real command returning exit code 0.

The TESTNET scenario is implemented in `scripts/external/binance_testnet_acceptance.py` and is hard-pinned to `https://testnet.binance.vision`. It refuses the LIVE endpoint. Required variables are `BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`, and explicit `BINANCE_TESTNET_EXECUTE=YES`. `BINANCE_TESTNET_SYMBOL` defaults to `BTCUSDT`; `BINANCE_TESTNET_MAX_NOTIONAL` defaults to `15` TESTNET quote units and acts as a safety ceiling. A real partial-fill observation is mandatory. Set `BINANCE_TESTNET_PARTIAL_PRICE` to an operator-selected TESTNET-only probe price; if the exchange does not report `0 < filledQty < origQty`, the scenario remains BLOCKED.

The `provenance` profile requires a real CI environment and produces `reports/external_acceptance/provenance.json`. It binds the CI run ID, checked-out git SHA, resolved backend/frontend lock hashes, real SBOM hash, frontend build tree hash and immutable container RepoDigest. Set `ACCEPTANCE_CONTAINER_IMAGE` to the image built by that CI run. The capture fails if CI identity is missing, the declared commit differs from the checkout, build inputs are missing, or the image has no SHA-256 RepoDigest.

Signing and signature verification are intentionally organization-specific. Set `PROVENANCE_SIGN_VERIFY_COMMAND` to the approved CI command that signs the intended release artifact/image and verifies that signature using the organization trust policy. The `provenance` group does not PASS unless both provenance capture and sign+verify commands succeed on the explicitly confirmed real target.

Recommended execution order on the isolated acceptance/CI environment:

```bash
python scripts/external_acceptance_runner.py --profile locks --confirm-real-target
python scripts/external_acceptance_runner.py --profile runtime --confirm-real-target
python scripts/external_acceptance_runner.py --profile supply-chain --confirm-real-target
python scripts/external_acceptance_runner.py --profile pitr --confirm-real-target
python scripts/external_acceptance_runner.py --profile ha --confirm-real-target
python scripts/external_acceptance_runner.py --profile testnet --confirm-real-target
python scripts/external_acceptance_runner.py --profile provenance --confirm-real-target
python scripts/external_acceptance_runner.py --profile all --confirm-real-target
python scripts/verify_external_acceptance.py reports/external_acceptance/manifest_all.json
python scripts/generate_release_manifest.py
python scripts/release_gate.py
```

Do not run `--confirm-real-target` merely to remove a blocker. It is an operator attestation that the commands are actually executing against the intended isolated real acceptance systems. LIVE remains disabled until the final release gate independently passes.

## Phase 41-44 hardening addendum

External acceptance is now semantic as well as process-level. A zero exit code alone is never sufficient for PITR, HA, or WORM acceptance.

### PITR restore drill

Set both `PITR_DRILL_COMMAND` and `PITR_EVIDENCE_JSON`. The command must perform the isolated restore; the JSON must use classification `REAL_EXTERNAL_ACCEPTANCE_DRILL`, kind `PITR_RESTORE`, set `real_system=true`, match the current Git commit, contain fresh timezone-aware observation time, bind at least one real artifact by SHA-256, and prove isolation, restore, schema/referential-integrity/checksum validation, read-only smoke, and result reporting.

### HA failover drill

Set `HA_DRILL_COMMAND` and `HA_EVIDENCE_JSON`. Evidence must prove process kill/fencing/private-stream reconciliation, host loss, database failover and network partition. Redis failover is mandatory when the selected deployment declares Redis HA applicable.

### WORM audit-storage acceptance

Set `WORM_ACCEPTANCE_COMMAND` and `WORM_EVIDENCE_JSON`. Evidence must prove append-only behavior, retention lock, denied early deletion, denied overwrite, successful readback, provider identity and retention-policy reference. The release gate now requires this control explicitly.

### Restart drills

The `restart-drills` profile performs real Docker Compose Redis and PostgreSQL restarts followed by service health checks. Redis/PostgreSQL restart acceptance is now separate from generic runtime acceptance and is required by the production release gate.

### Evidence templates and preflight

Use `python scripts/external/generate_drill_template.py {pitr|ha|worm}` to generate fail-closed templates. Templates deliberately start with `real_system=false` and all result booleans false. `python scripts/external_acceptance_preflight.py` reports prerequisite readiness only; READY is never acceptance PASS.

### Cryptographic nesting

The PITR/HA/WORM wrapper receipt contains the semantic evidence JSON path and SHA-256. `verify_external_acceptance.py` re-checks the outer log hash, nested evidence hash, Git commit, freshness, semantic fields and all nested artifact hashes before a group can remain PASS.

## Phase 47–49 hardening: release challenge, evidence ledger, and sharded local regression

Before any `--confirm-real-target` external acceptance run, generate a fresh release-bound challenge:

```bash
python scripts/generate_acceptance_challenge.py
```

The challenge is bound to the current Git commit and expires. A confirmed-real acceptance run refuses to execute if the challenge is missing, stale, or belongs to another commit. Successful real acceptance manifests are appended to `reports/external_acceptance/evidence_ledger.json`, whose entries are hash chained. Verification rejects a broken chain, manifest replay, a manifest not bound to the current challenge, or evidence from a different Git commit.

For local regression on constrained runners, use deterministic shards. Every shard records the exact test files, Git SHA, exit code, log path, and log SHA-256. After every shard passes, merge them into a single coverage proof:

```bash
python scripts/local_acceptance_runner.py --shard-index 0 --shard-count 8
# repeat indexes 1..7
python scripts/merge_local_acceptance.py --shard-count 8
```

The merged result is PASS only if every discovered `test_*.py` file is covered exactly once, every shard is from the same current Git commit, every shard passed, and every log hash verifies.

Generate the current execution plan with:

```bash
python scripts/production_readiness_dossier.py
```

The dossier is planning metadata only and never satisfies an acceptance requirement by itself.

## Phase 51–53 hardening: immutable profile runs, merged acceptance, campaign evidence, orchestration

Each external acceptance profile now writes its logs and immutable manifest under a unique `reports/external_acceptance/runs/<run_id>/<profile>/` directory. The compatibility alias `manifest_<profile>.json` points to the latest manifest content, but previously hashed run artifacts are never overwritten. This prevents a later profile run from invalidating an earlier profile manifest by replacing shared log files.

When profiles are executed separately, merge them before final verification:

```bash
python scripts/merge_external_acceptance.py
python scripts/verify_external_acceptance.py reports/external_acceptance/manifest_all.json
```

The merge step accepts PASS only from individually verified manifests bound to the current release challenge and Git commit. Missing/invalid profiles remain NOT_TESTED/BLOCKED. The merged manifest is itself bound into the append-only evidence ledger whenever it contains PASS groups.

Four previously manual release-gate areas now have machine-verifiable evidence contracts, without creating or fabricating the underlying evidence:

```bash
python scripts/external/generate_campaign_evidence_templates.py
# Populate the non-template JSON files only from real external campaign/source artifacts.
python scripts/external_acceptance_runner.py --profile campaigns --confirm-real-target
```

The campaign profile validates: credentialed private-stream lifecycle/reconciliation; a real-market PAPER campaign against the promotion policy; LIVE-shadow with zero real order submissions/exchange submit calls; and real point-in-time profitability evidence with independent OOS, leakage/survivorship controls, cost stress, positive after-cost expectancy and statistical confidence. Every receipt is release-challenge/Git bound and must hash real source artifacts. Templates start fail-closed and are not evidence.

A one-command orchestrator is available for an isolated acceptance host:

```bash
python scripts/production_acceptance_orchestrator.py
# plan-only: executes no external acceptance command

python scripts/production_acceptance_orchestrator.py --confirm-real-target
# explicit operator attestation: challenge -> all profiles -> merge -> verify -> release manifest -> gate -> dossier
```

The orchestrator returns success only when every profile passes on the same release-bound challenge, the merged verifier passes, release-manifest generation succeeds, and the canonical release gate is eligible. It never enables LIVE; human approval remains a separate post-gate action.

## Phase 54–55 — Source / Evidence / Distribution package separation

Release transport is intentionally split into three deterministic artifacts:

1. `scripts/package_release.py` builds the **source release archive**. It contains source code, configuration, migrations, tests, documentation, and only canonical current local reports. Historical `reports/PHASE*` files and external acceptance run artifacts are intentionally excluded.
2. `scripts/package_evidence.py` builds a **Git-bound evidence transport bundle**. It includes canonical release/status/traceability evidence plus only external acceptance files explicitly referenced by the merged acceptance manifest. Unreferenced logs are never swept into the archive.
3. `scripts/package_distribution.py` creates the **distribution bundle** containing the source archive, evidence archive, `RELEASE_BUNDLE.json`, and `SHA256SUMS.txt`.

The distribution builder fails closed unless `RELEASE_MANIFEST.json` and `reports/LOCAL_SOURCE_PROVENANCE.json` match the current Git SHA, source provenance is clean and immutably tagged, default mode is `PAPER`, and LIVE remains disabled. Archive/hash integrity proves transport integrity only; it does not convert BLOCKED/NOT_TESTED acceptance into PASS and never enables LIVE.


## Phase 59 — CI production-acceptance pipeline

A manual, fail-closed GitHub Actions workflow is provided at `.github/workflows/production-acceptance.yml`. It is intentionally separate from ordinary PR CI. Trigger it only for an immutable candidate tag/SHA.

The first job runs on a hosted build runner and resolves both backend/frontend lock files, installs from those locks, builds the frontend, executes canonical 24-shard local acceptance, builds and pushes an immutable candidate container, runs dependency/SAST/secret/container/SBOM checks, captures the scanner versions, and produces real CI provenance tied to the actual checked-out SHA and GitHub run ID. Generated lock files are evidence from that run; they do not retroactively make a source release compliant until the resolved locks are reviewed and committed to source.

The second job is deliberately restricted to a `self-hosted` runner carrying the `production-acceptance` label and the protected `production-acceptance` environment. It downloads the exact first-job evidence, pulls the exact candidate image by the source SHA, then invokes the existing fail-closed production acceptance orchestrator with protected TESTNET/PITR/HA/WORM/signing secrets. The workflow never enables LIVE and the canonical release gate remains authoritative.

Permissions are least-privilege by job: the build-evidence job receives `packages: write` only for GHCR publication, while the real-target job receives `id-token: write` only for approved federated signing/attestation flows. Production secrets are never exposed to the hosted build job. Scanner container tags are fixed rather than `latest`; their resolved versions plus Python scanner package versions must remain part of the build evidence.

## Phase 63-65 hardening

Production acceptance supply-chain evidence now requires three distinct artifacts in addition to the scanner command results: a CycloneDX SBOM, a dependency license report generated by `pip-licenses`, and a semantic verification receipt produced by `scripts/external/verify_supply_chain_artifacts.py`. CI provenance hashes all three. A missing/empty/malformed SBOM or license report blocks the supply-chain group; local placeholder SBOMs do not qualify.

Real-target acceptance is also bound to the target environment. Set `ACCEPTANCE_ENVIRONMENT_ID` to a stable non-secret environment identifier and `ACCEPTANCE_TOPOLOGY_HASH` to the 64-hex SHA-256 of the reviewed deployment/topology configuration. The raw environment identifier is never stored; the runner records only its SHA-256. Every PASS profile in a merged release must come from the same environment-id hash and topology hash.

External evidence freshness is enforced per group as well as at bundle level. Operational groups (runtime, restart drills, PITR, HA, WORM, TESTNET/private stream and LIVE-shadow) default to a 24-hour evidence TTL; slower-changing build/supply-chain/campaign evidence defaults to 168 hours. An operator may explicitly override a group TTL with `verify_external_acceptance.py --group-ttl GROUP=HOURS`; the effective policy is recorded in verifier output. An override changes only verification policy and does not fabricate acceptance evidence.

The append-only evidence ledger now validates the existing chain before append and writes via an advisory lock, fsync and atomic replace. Invalid/tampered ledgers are never extended.

## Phase 67 — release-campaign challenge and safe profile retry

Release challenge schema 2.0 uses `release_campaign_bound=true`. The challenge is intentionally reusable across distinct acceptance profiles and the aggregate manifest for one release campaign; it is not a single-manifest token. Schema 1.0 challenge documents remain verifier-compatible for historical evidence.

Safe retries can reuse only a fresh challenge already verified against the current Git SHA:

```bash
python scripts/production_acceptance_orchestrator.py \
  --confirm-real-target \
  --reuse-current-challenge \
  --profiles runtime restart-drills
```

`--reuse-current-challenge` never creates a fallback challenge. Missing, stale, malformed, or wrong-Git challenges block before any external acceptance command executes. `--profiles` only controls which profiles are re-executed; final promotion still depends on the merged all-profile evidence and the canonical release gate. This allows a failed profile to be retried without invalidating successful profiles from the same release campaign.

## Phase 68–70 hardening

### Semantic runtime restart evidence
`restart-drills` no longer passes on container restart + ping/readiness alone. Real acceptance also requires `scripts/external/runtime_restart_drill.sh` with `RESTART_DRILL_COMMAND` and `RESTART_EVIDENCE_JSON`. The nested evidence must prove state persistence before/after Redis/PostgreSQL restart, application reconnection/reconciliation, zero duplicate orders, fail-closed risk behavior during outage, healthy recovery, source-artifact hashes, current release-challenge binding, and acceptance environment/topology binding. Templates are fail-closed and are not evidence.

### Release challenge trust hook
The production acceptance workflow sets `ACCEPTANCE_REQUIRE_CHALLENGE_TRUST=1` and requires `ACCEPTANCE_CHALLENGE_VERIFY_COMMAND`. The command receives the challenge path only through `ACCEPTANCE_CHALLENGE_PATH` and must exit zero to establish the external trust hook. A missing/rejecting verifier blocks real acceptance. Local/dev verification does not claim cryptographic or organizational trust when the hook is absent.

### Final package provenance
`python scripts/package_distribution.py` also writes `PACKAGE_PROVENANCE.json` next to the distribution archive. This detached file binds the final distribution archive SHA-256/size to source and evidence archive metadata, current Git SHA, `RELEASE_MANIFEST.json` hash, release status, and available build-provenance fields. Local runs are classified `LOCAL_PACKAGE_PROVENANCE_NOT_CI_PROVENANCE`; the file is not a substitute for signed CI provenance.

## Phase 72–76 — campaign truth, provenance gate, immutable workflow actions and nested TTL

Campaign/private-stream evidence is schema-versioned (`schema_version=1.0`) and all numeric fields are validated as finite values. `NaN`, positive/negative infinity, booleans masquerading as numbers, and fractional count fields fail closed. Missing or unknown campaign schema versions are not accepted.

The canonical release gate now explicitly requires the `ci_release_provenance` external acceptance group. Release-manifest `known_release_blockers` are derived from current P0/lock/external-acceptance state rather than a stale hardcoded list. This means successful evidence removes only the blocker it actually satisfies; missing CI run identity, lock/SBOM/license/container/frontend provenance remains a direct release blocker.

GitHub Actions references in repository workflows are required to be immutable. Run:

```bash
python scripts/verify_workflow_action_pins.py
```

Repository actions must use a full 40-hex commit SHA (including sub-path actions). Container actions must use an immutable `@sha256:<64-hex>` digest. Moving refs such as `@v4`, branches, or mutable Docker tags fail verification. Production acceptance runs this verifier before build/target evidence is trusted.

Evidence TTL applies recursively. The effective group-specific TTL used for an outer acceptance row is also passed to nested PITR/HA/WORM drills and campaign/private-stream semantic evidence. Refreshing only an outer wrapper cannot make stale nested evidence current. Explicit TTL overrides, when used, are applied consistently to both levels and recorded by the verifier.

## Phase 78 — committed lock promotion and source-compliant acceptance

Production acceptance MUST consume dependency locks committed in the candidate Git HEAD. It MUST NOT resolve or create `uv.lock` or `frontend/package-lock.json` during the acceptance job and then treat those generated files as source-compliant release inputs.

Use the manual `Lock Promotion` workflow to resolve both locks for review. Its output is review evidence only: inspect dependency changes, hashes, frontend build results and the generated lock files, then explicitly commit approved locks to the candidate branch/tag lineage. The production-acceptance workflow runs `scripts/verify_source_locks.py` before dependency installation and fails closed unless both lock files are tracked in Git HEAD and byte-for-byte identical to their HEAD versions.

Detached `PACKAGE_PROVENANCE.json` verification also cross-checks its source/evidence archive records against the `RELEASE_BUNDLE.json` embedded in the final distribution archive. A correct outer archive hash alone is insufficient if the detached provenance metadata was altered.

## Phase 80 — unified source-lock truth and release-consistency gate

Dependency-lock readiness is evaluated by one source rule everywhere: both `uv.lock` and `frontend/package-lock.json` must exist, be tracked in the candidate Git HEAD, and be byte-for-byte unchanged from HEAD. External preflight, the external `locks` profile, production handoff and the canonical release gate all consume that rule. A generated or untracked lock may be review evidence, but it is never release-compliant evidence.

The manual `Lock Promotion` workflow also requires an immutable `source_ref`: an exact 40-character commit SHA or an annotated tag resolving to the checked-out HEAD. Branches and moving refs are rejected before dependency resolution. The immutable-ref validation receipt is retained in the lock-review bundle.

`reports/PROJECT_STATUS.json` consumes test-count and coverage truth from the current `RELEASE_MANIFEST.json` rather than independently promoting a stale coverage file. `scripts/verify_release_consistency.py` compares `TEST_COUNT.txt`, release manifest, project status and local source provenance; packaging and production acceptance fail closed if these artifacts disagree. `reports/RELEASE_CONSISTENCY.json` is part of the canonical source/evidence package policy.

## Phase 82 — preflight CLI and trust/signing completeness

- `python scripts/external_acceptance_preflight.py` is a supported direct CLI from the repository root. The script bootstraps the repository root before importing sibling `scripts.*` modules; an import crash is a tooling defect, not an acceptable blocked-preflight result.
- Preflight now includes the production challenge-trust and provenance signing contracts: `ACCEPTANCE_CHALLENGE_VERIFY_COMMAND` and `PROVENANCE_SIGN_VERIFY_COMMAND`.
- Presence of these command contracts is reported only as `PRESENT_REDACTED`; command contents are never persisted to the preflight report.
- `all_external_prerequisites_ready=true` is impossible unless both trust/signing contracts are present. This remains prerequisite detection only and is never acceptance evidence.
- Dependency locks remain source-compliant only when tracked in Git HEAD and byte-identical to HEAD. A CI-generated or untracked lock cannot satisfy release readiness.

## Phase 83-84 supply-chain and cross-job evidence transfer hardening

Production acceptance resolves the gitleaks, Trivy, and Syft scanner image tags to immutable Docker RepoDigests before running them. The resulting `reports/external_acceptance/scanner_image_digests.json` receipt is semantically verified, hashed into real CI provenance, restored on the real-target runner, hash-checked, and semantically verified again. A mutable scanner tag is discovery input only; it is never the image reference used for the actual scan.

The CI build-evidence handoff is also protected independently of GitHub Artifact transport behavior. Before upload, `python scripts/ci_build_evidence_manifest.py create` records the candidate Git SHA and SHA-256/size of every transferred evidence file. Immediately after download on the self-hosted runner, `python scripts/ci_build_evidence_manifest.py verify --expected-git-sha <candidate-sha>` must pass before any restored build evidence can be used.

If a source workspace is reconstructed from a verified release source archive because original `.git` metadata is unavailable, `SOURCE_RECOVERY_LINEAGE.json` records the archive hashes and original Phase 82 commit identity. Its classification explicitly states that recovered history is not original Git history and is not production acceptance evidence. A newly reconstructed repository must establish its own Git identity and rerun canonical acceptance before producing a later release.

## Phase 88 hardening

Phase 88 tightens three fail-closed acceptance boundaries:

- `CI_BUILD_EVIDENCE_MANIFEST.json` verification recomputes the complete required transfer input set and rejects omitted required files or unexpected manifest entries.
- Scanner digest receipts bind each requested scanner repository to the repository named by its resolved `@sha256:` RepoDigest; a digest from a different repository is rejected.
- Real-target preflight and workflow wiring explicitly require `RESTART_DRILL_COMMAND` and `RESTART_EVIDENCE_JSON`.

These are evidence-integrity controls only. They do not turn local execution into real production acceptance and do not enable LIVE mode.

## Phase 99 source-package recovery and CI identity hardening

When restoring a delivered source ZIP, do not rely on Python `zipfile.ZipFile.extractall()` alone on Unix-like systems: it may not restore executable mode bits from ZIP metadata. Use:

```bash
python scripts/extract_source_package.py <source-zip> <destination>
```

The helper rejects path traversal entries and restores Unix mode bits recorded in the ZIP, including the executable bit on `install.sh`.

Phase 97–99 also harden the promotion/acceptance handoff:

- Production acceptance secret/variable contracts are machine-checked for workflow ↔ handoff ↔ preflight parity.
- Lock-promotion review bundles carry a source-SHA/toolchain/lock-hash manifest and are verified before upload.
- The GitHub Actions build artifact ID and `artifact-digest` are bound to the exact candidate SHA and to the independently verified file-level build-evidence manifest.
- These controls strengthen evidence identity; they do not convert a local run into production acceptance or enable LIVE mode.


## Phase 154 drill replay protection

PITR, HA/failover, and WORM semantic drill evidence uses schema `2.0` and is release-bound. A PASS-capable drill receipt must bind all of the following values: the current release challenge (`challenge_id` + challenge SHA-256), the acceptance environment identity hash, the topology hash, the exact Git commit, freshness window, and the hashed source artifacts. Evidence from a previous challenge, a different environment, or a different topology must be treated as BLOCKED even when the Git commit is unchanged and the evidence is still inside its TTL.

Generate templates only after the release challenge and `ACCEPTANCE_ENVIRONMENT_ID` / `ACCEPTANCE_TOPOLOGY_HASH` are configured. The template generator records these bindings but still defaults all real-execution booleans to false; a generated template is never acceptance evidence by itself.

### Phase 163 aggregate-schema and nested-artifact immutability hardening

Production PASS now has an explicit schema boundary. Individual acceptance profiles may claim PASS only with schema `3.2`. Aggregate `profile=all` PASS may be accepted only from the merge path using schema `4.1`, which is the path that appends the `all-merged` ledger entry and requires the externally verified signed ledger checkpoint. Direct real execution with `external_acceptance_runner.py --profile all --confirm-real-target` is blocked with `AGGREGATE_REAL_ACCEPTANCE_REQUIRES_MERGE` before acceptance commands execute.

Strict nested semantic/provenance artifacts are also required to be regular files inside the repository acceptance root. Symlink indirection is rejected before path resolution so the immutable artifact identity cannot be hidden by `resolve()`.

### Phase 164 immutable run-artifact binding

For schema `3.2` individual production PASS, every top-level hashed evidence artifact must come from the immutable runner directory `reports/external_acceptance/runs/<run_id>/<profile>/`. PASS manifests must include a valid `run_id`. Artifacts outside that run directory are rejected with `ARTIFACT_OUTSIDE_IMMUTABLE_RUN_DIR:*`; missing/invalid run IDs are rejected with `STRICT_PASS_RUN_ID_MISSING_OR_INVALID`.

This rule intentionally applies to the top-level runner artifacts. Nested semantic evidence may be produced by externally managed drill/provenance tooling, but it remains subject to Phase 163 regular-file, repository-containment, hash, challenge, environment and topology verification.

### Phase 165 canonical profile mapping and aggregate source re-verification

The profile-to-group mapping is now part of the canonical acceptance contract (schema `1.1`) and therefore contributes to `acceptance_contract_sha256`. A release challenge created before a profile/group semantic change cannot be reused afterward.

For schema `4.1` aggregate PASS, the final verifier independently re-verifies every canonical source profile manifest (`manifest_<profile>.json`): source status metadata must be VERIFIED, the canonical reference must match, the stored SHA-256 must match the current file, the file must be a regular non-symlink artifact, the individual manifest verifier must succeed, and all groups mapped to that source profile must remain PASS. Aggregate merge metadata alone is never trusted as proof of source-profile validity.

### Phase 166 aggregate environment/topology re-binding

Schema `4.1` aggregate PASS independently re-verifies every canonical source profile against the aggregate acceptance environment. A source profile whose `acceptance_environment_id_hash` or `topology_hash` differs from `manifest_all.json` is rejected even when its file hash and individual verifier result are otherwise valid. Cross-environment profile composition is never production acceptance.

### Phase 167 aggregate row provenance and signed/supply-chain replay protection

Schema `4.1` aggregate PASS now re-binds the exact aggregate evidence rows to the evidence rows contained in the individually verified source profile manifests. Command metadata, timestamps, status fields, artifact paths, artifact hashes, exit codes and other row fields must match exactly. A hand-edited aggregate row cannot become fresher or point at a substituted artifact while continuing to cite an unchanged valid source-profile manifest hash.

Production provenance signature evidence uses schema `2.0`. In strict external verification it must bind the exact Git commit, the current externally trusted release challenge (`challenge_id` and challenge SHA-256), the acceptance environment identity hash, the topology hash, the provenance artifact hash and detached signature artifact hash. Symlink indirection for signed artifacts is rejected. `PROVENANCE_SIGN_VERIFY_COMMAND` must create this schema-2.0 receipt; schema `1.0` remains parseable only for non-strict historical/unit verification and cannot satisfy the production external verifier.

Transferred CI supply-chain acceptance receipts also use schema `2.0` and are generated only after the current release challenge passes external trust verification. They carry the same acceptance environment/topology binding. The outer external verifier independently compares those bindings to the profile manifest before allowing the `supply_chain` group to remain PASS.

### Phase 168 source-package verifier CLI root binding

`scripts/verify_source_package_identity.py` accepts an explicit `--root <extracted-source-root>` argument and uses `argparse` strict parsing. Unknown CLI arguments are rejected with a non-zero exit code instead of being silently ignored. This prevents an operator or automation from intending to verify one extracted package while accidentally verifying the current working directory.

Recommended independent post-extraction check:

```bash
python scripts/verify_source_package_identity.py --root /path/to/extracted/crypto_trading_platform_v5_1
```

The result must report `verified=true`; this check complements `scripts/extract_source_package.py`, which verifies the archive before extraction and restores recorded executable mode bits.
