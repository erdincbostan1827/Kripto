# Troubleshooting

## `/ready` 503
PROD'da DB, Redis, exchange/clock veya diğer kritik probe'lar hazır değilse yeni risk fail-closed engellenir. Önce health/correlation ID ile root cause'u bulun; yalnız servisi tekrar başlatmak reconciliation ihtiyacını ortadan kaldırmaz.

## `UNKNOWN` order
Aynı intent'i körlemesine yeniden göndermeyin. Exchange query/private stream ve reconciliation ile gerçek order state'ini belirleyin. Aynı symbol/account yeni riskini bloke edin.

## Frontend build
`frontend/package-lock.json` ve `uv.lock` kaynakta commitlidir ve kabul edilen candidate revizyonuyla eşleşmelidir. Phase 217 local candidate üzerinde kilitli frontend test/build doğrulandı. Bununla birlikte canonical browser acceptance her candidate için yeniden `npm ci` çalıştırır; registry/DNS erişimi yoksa veya npm yarım bir `node_modules` ağacı bırakırsa koşu fail-closed BLOCKED olur ve yarım dependency ağacı temizlenir. Gerçek Chromium viewport matrisi ayrıca PASS olmalıdır.

## Docker/PostgreSQL/Redis
Bu çalışma ortamında Docker daemon acceptance çalıştırılmadı. Compose tanımı ve offline Alembic SQL mevcut olsa da gerçek migration/Redis failure/PITR restore sonucu `NOT_TESTED` olarak değerlendirilmelidir.

## Binance TESTNET/private stream
Credential olmadan public contract/parser/reconnect testleri çalışır; authenticated TESTNET/private stream/protective-order/reconciliation acceptance ayrı yapılmalıdır.

## Phase 147 — dependency resolution diagnostic

Run `python scripts/dependency_resolution_diagnostic.py` before attempting lock promotion. It writes `reports/DEPENDENCY_RESOLUTION_DIAGNOSTIC.json` and distinguishes missing manifests/tooling from unavailable PyPI/NPM DNS. The result is prerequisite evidence only; it never upgrades release readiness. If registries are unavailable locally, use the existing trusted `lock-promotion.yml` workflow, review the generated lockfiles, and commit them before production acceptance.

## Phase 150 — external acceptance execution-plan consistency

Before running production acceptance, verify that every unresolved requirement has exactly one non-ambiguous execution profile and that P0 blocker categories agree with that profile:

```bash
python scripts/external/execution_map.py
python scripts/verify_external_execution_plan.py
python scripts/production_readiness_dossier.py
```

`reports/EXTERNAL_EXECUTION_PLAN_VERIFICATION.json` must report `verified=true`, an empty `problems` list, and an empty `ambiguous_p0_requirement_ids` list. This is planning/consistency evidence only; it cannot convert a runtime, TESTNET, recovery, supply-chain, or signing requirement to PASS.

## Phase 151 — acceptance command/source integrity guards

Production acceptance evidence is now bound to a canonical command contract and a release challenge that checks the Git tree plus release-relevant worktree cleanliness.

- Evidence bundle schema `3.2` carries `command_contract_sha256`; merged bundle schema `4.1` carries the `all` profile contract hash.
- `scripts/verify_external_acceptance.py` rejects command substitution, unknown evidence keys, and command-contract hash mismatches for these schemas.
- Release challenge schema `2.1` records `git_tree_sha` and `source_worktree_clean_at_creation`.
- A tracked source modification, or an untracked executable/build-affecting source file outside runtime evidence locations, blocks challenge verification with `CHALLENGE_SOURCE_WORKTREE_DIRTY`.
- Runtime evidence outputs under `reports/`, `frontend/dist/`, caches, coverage data, and non-executable log/JSON receipts are not treated as source substitutions.

If production acceptance blocks on source cleanliness, discard or commit the source change, regenerate the release challenge, and rerun the campaign. Do not bypass the guard or manually rewrite evidence manifests.

## Phase 153 — Real acceptance requires Git-bound source identity

Production acceptance challenges are intentionally stricter than source-package handoff identity.
A source ZIP may be verified with `PACKAGE_MANIFEST.json` for distribution/handoff, but a real-target
acceptance campaign must run from a clean Git worktree with both `HEAD` commit and `HEAD^{tree}`
available. Challenge schema 2.2 records whether that identity was available at creation and fails
closed when it was not.

If `production_acceptance_orchestrator.py --confirm-real-target` reports
`NEW_CHALLENGE_NOT_VERIFIED` with `CHALLENGE_GIT_IDENTITY_UNAVAILABLE`, do not bypass the gate.
Checkout the exact candidate SHA in the trusted acceptance runner, configure the external challenge
trust verifier, and rerun. The orchestrator now performs this verification before any acceptance
profile command executes.
