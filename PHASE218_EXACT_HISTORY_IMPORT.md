# Phase 218 Exact Git History Import Handoff

Status date: 2026-09-02

This bootstrap branch exists only to hand off the **exact recovered Phase 218 Git object graph**. Do not treat the current `main` commit as the canonical Phase 218 source identity.

## Canonical recovered identity

- Exact candidate commit: `82c7a7b7f621f488422fb549af3ea32356a0c63d`
- Exact annotated tag: `v0.3.0-phase218-local`
- Exact source branch in the bundle: `continuation-phase218`
- Commit count in recovered bundle: **24**
- Annotated tag count: **18**
- Tracked files at Phase 218 HEAD: **739**
- Git bundle SHA-256: `ee81b54d496a124cc75c2d49b150ffab63cfdab9704fce11e72b46d16e4f6861`
- Bundle filename: `crypto_trading_platform_v5_1_phase218_git.bundle`

The recovered history is explicitly a local/reconstructed verification lineage, not the original upstream repository history before recovery.

## Exact import procedure

Run these commands on a machine that has the verified bundle and authenticated GitHub access:

```bash
sha256sum crypto_trading_platform_v5_1_phase218_git.bundle
# must equal:
# ee81b54d496a124cc75c2d49b150ffab63cfdab9704fce11e72b46d16e4f6861

rm -rf phase218-import-check
git clone crypto_trading_platform_v5_1_phase218_git.bundle phase218-import-check
cd phase218-import-check

test "$(git rev-parse continuation-phase218)" = "82c7a7b7f621f488422fb549af3ea32356a0c63d"
test "$(git rev-parse v0.3.0-phase218-local^{})" = "82c7a7b7f621f488422fb549af3ea32356a0c63d"
test "$(git rev-list --all --count)" = "24"
test "$(git tag | wc -l | tr -d ' ')" = "18"

git remote remove origin
git remote add origin https://github.com/erdincbostan1827/Kripto.git

# Replace the bootstrap snapshot with the exact recovered history.
git push --force-with-lease origin continuation-phase218:main
# Push the recovered annotated tags exactly as stored in the bundle.
git push origin --tags
```

After import, verify from a fresh clone:

```bash
git clone https://github.com/erdincbostan1827/Kripto.git verify-kripto
cd verify-kripto
test "$(git rev-parse HEAD)" = "82c7a7b7f621f488422fb549af3ea32356a0c63d"
test "$(git rev-parse v0.3.0-phase218-local^{})" = "82c7a7b7f621f488422fb549af3ea32356a0c63d"
test "$(git rev-list --all --count)" = "24"
```

## Why this is not rewritten through the GitHub Contents API

The Contents API creates new commits and therefore changes commit object IDs, authorship/committer metadata, parent graph identity and annotated tag targets. Reconstructing the files through that API and calling it the same history would be false provenance. The exact bundle must be imported as Git objects.

## Current acceptance boundary

Verified Phase 218 local evidence:

- 1,251 tests / 251 test files.
- Full regression: 24/24 shards PASS, source-bound to `82c7a7b7f621f488422fb549af3ea32356a0c63d`.
- Fresh coverage: 90.13513060389633%, 48/48 shards PASS.
- Both `uv.lock` and `frontend/package-lock.json` are tracked in HEAD and source-compliant.
- Dependency-lock prerequisites are READY; they are not a substitute for the fresh trusted release challenge required by external acceptance.
- PROD LIVE remains BLOCKED.

Still-required real external evidence includes Docker/PostgreSQL/Redis runtime and restart acceptance, real Chromium dependency-resolved browser matrix in a networked runner, Binance TESTNET/private stream credentials, PITR/HA/WORM drills, real-market PAPER/LIVE_SHADOW campaigns, trusted CI supply-chain/SBOM/license evidence, and trusted signing/provenance/ledger checkpoint verification.
