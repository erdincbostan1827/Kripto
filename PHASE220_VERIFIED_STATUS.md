# Phase 220 verified candidate

Date: 2026-09-02

## Exact source identity

- Git SHA: `8f369aaf135ae86d31872353b7c68f2555c18089`
- Annotated tag: `v0.3.0-phase220-local`
- Exact Git bundle SHA-256: `1d8381546a8dfad3bff165b82cea135c8f28092d70fde9f609e5a7e41219cd20`
- Recovered Git graph: 25 commits, 19 annotated phase tags, 740 tracked files at HEAD.

## Local verification

- Full regression: 24/24 shards PASS, 1,252 tests, 252/252 test files.
- Fresh coverage: 48/48 shards PASS, 90.13693126653051%.
- Secret scan: 355 files / 0 findings.
- Local static analysis: 327 files / 0 findings / 0 high-or-critical.
- Prohibited-pattern scan: PASS.
- Workflow immutable action pins: 20/20 PASS.
- Source locks: PASS; `uv.lock` and `frontend/package-lock.json` are tracked and match HEAD.
- Release consistency: verified=true, problems=[].
- Source package safe extraction: PASS, 741 files; extracted package identity verified.
- Requirement matrix: 2,597 PASS / 94 NOT_TESTED / 2,691 total. P0: 1,473 PASS / 38 NOT_TESTED / 1,511 total.

## External acceptance truth

All 94 remaining NOT_TESTED requirements currently have external prerequisites. The unresolved profiles are real frontend/browser, desktop build/signing, Docker/PostgreSQL/Redis runtime and restart, credentialed TESTNET/private stream/campaigns, PITR, HA, WORM, trusted CI supply-chain, trusted signing, and trusted release provenance.

Real Chromium 144.0.7559.96 is present on the local host, but dependency-resolved browser acceptance remains BLOCKED because `npm ci` cannot reach registry.npmjs.org (`EAI_AGAIN`). No browser PASS is claimed.

`PROD_LIVE_RELEASE=BLOCKED`, `live_enabled=false`, default mode `PAPER`.

The current GitHub `main` branch must not be treated as this exact source identity until the exact bundle objects have been imported and `main` resolves to the SHA above.
