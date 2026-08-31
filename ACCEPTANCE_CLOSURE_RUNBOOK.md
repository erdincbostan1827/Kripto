# Acceptance Closure Runbook

This runbook is intentionally fail-closed. `NOT_TESTED` means the production acceptance evidence is missing or has not been verified for the current release. A local simulation, mock, static contract test, or prerequisite check must never be promoted to `PASS` as a substitute for the required real evidence.

## One-command status refresh

```bash
python scripts/external_acceptance_preflight.py || true
python scripts/external/execution_map.py
python scripts/verify_external_execution_plan.py
python scripts/acceptance_closure_status.py
```

The operator-facing result is `reports/ACCEPTANCE_CLOSURE_STATUS.json`. It maps every unresolved requirement to exactly one execution profile, the required command, and the prerequisite(s) currently blocking execution.

## Closure order

1. Generate and source-control both dependency locks (`uv.lock` and `frontend/package-lock.json`) using the atomic bootstrap path.
2. Run the dependency-resolved frontend build/browser acceptance on a real browser runner.
3. Run Docker/PostgreSQL/Redis runtime acceptance and restart drills on a host with Docker.
4. Execute credentialed Binance testnet and real-market PAPER/live-shadow campaigns using dedicated non-withdrawal credentials.
5. Execute PITR, HA and WORM drills in the intended acceptance topology.
6. Produce trusted CI supply-chain evidence, SBOM, vulnerability/license results, provenance, signing and ledger checkpoint evidence.
7. Merge only checksum-bound, release-bound, current-schema evidence through the repository acceptance verifier.
8. Keep production LIVE blocked until all mandatory gates are verified.

## Truth boundary

Preflight `READY` means only that a prerequisite was detected. It is not acceptance evidence. External evidence must be real-target, release-bound, schema-current and checksum-verified before any corresponding requirement may become `PASS`.

## Phase 176 diagnostic safety

Run `python scripts/phase176_readiness.py` to produce `reports/PHASE176_READINESS.json`. This is a prioritization/readiness artifact only and **never acceptance evidence**. External command output is sanitized through `scripts/acceptance_diagnostics.py`; known credential-bearing environment values, bearer/basic authentication material, URL user-info and common token/query assignments are redacted before evidence logs are written. Non-zero commands receive stable blocker categories such as `NETWORK_DNS_UNAVAILABLE`, `OFFLINE_CACHE_INCOMPLETE`, `AUTHENTICATION_FAILED`, or `CONTAINER_RUNTIME_UNAVAILABLE` instead of copying potentially sensitive error text into blocker fields.

## Phase 177 — external acceptance handoff

Create a deterministic, source-identity-bound handoff bundle before moving acceptance work to an isolated real target host:

```bash
python scripts/phase177_acceptance_capabilities.py
python scripts/external/acceptance_handoff_bundle.py
python scripts/external/acceptance_handoff_bundle.py --verify reports/PHASE177_EXTERNAL_ACCEPTANCE_HANDOFF.zip
```

The handoff ZIP contains runbooks and acceptance contracts only. It is explicitly **not** acceptance evidence, never transports `.env`/credential values, rejects secret-like assignments, and cannot promote any requirement or release gate to `PASS`. Evidence produced on the real host must return through the canonical checksum-bound verifier/merge path.
