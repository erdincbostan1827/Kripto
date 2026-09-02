# Phase 221 Exact Git History Method

Canonical candidate: `8f369aaf135ae86d31872353b7c68f2555c18089`  
Bundle SHA-256: `1d8381546a8dfad3bff165b82cea135c8f28092d70fde9f609e5a7e41219cd20`

The bundle is the authoritative transport because it contains the original Git objects. Do **not** recreate commits with the Contents API, `create_commit`, squash/import snapshots, or any process that changes commit metadata or parentage.

Verified locally: 25 commits, 19 annotated phase tags, complete history, branch `continuation-phase218` at the canonical candidate SHA.

Current GitHub main is not the canonical candidate. Exact-history closure is FAIL until GitHub `refs/heads/main` is exactly `8f369aaf135ae86d31872353b7c68f2555c18089`.

Safe native import requires an environment that can read the bundle bytes and authenticate to GitHub. Run `scripts/import_exact_phase221.sh <repo-url> <bundle-path>`. The script verifies bundle SHA, bundle completeness, candidate HEAD, commit count and annotated tag count before pushing the exact branch object to `refs/heads/main` and the exact tag objects to `refs/tags/*`.

After import, compare GitHub against `PHASE221_EXACT_REFERENCE.json`. Exact-history closure is PASS only if every commit SHA, parent list, tree SHA, annotated tag object SHA and tag target SHA matches, and GitHub main equals the canonical candidate.
