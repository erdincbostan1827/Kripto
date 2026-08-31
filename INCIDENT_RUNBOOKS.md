# INCIDENT_RUNBOOKS.md

Production incident evidence uses `SEV1` for capital/execution/security integrity risk, `SEV2` for trading-stopping or materially degraded service, and `SEV3` for limited-function/UX issues. Every incident records an incident id, detection time, affected account/symbol/service, automatic action, risk state, operator actions, correlation evidence, resolution time, and recovery validation.

## UNKNOWN order
**Severity:** SEV1. Block new risk for the symbol/account as appropriate. Query the exchange by deterministic `client_order_id`; inspect private-stream events, open orders and fills. Never blindly retry an order mutation. If truth cannot be established, remain `MANUAL_REVIEW_REQUIRED`. Resume only after reconciliation PASS and audit evidence.

## Orphan order
**Severity:** SEV1 when exchange exposure is uncertain. Stop new risk for the symbol; determine whether the local order is stale, cancelled externally or missing from exchange history. Reconcile fills/balance/position before altering ledger truth. Operator acceptance requires a reason and immutable audit evidence.

## Unprotected position
**Severity:** SEV1. Enter `HALTED` or `REDUCING_ONLY`. Verify exchange-native protective stop order by order type, side, quantity and acknowledged state. A local database record is not proof of protection. If protection cannot be established, follow the configured emergency/panic-close policy and page critical alerts.

## External/manual account activity
**Severity:** SEV1 for unexplained risk-increasing activity. Classify UNKNOWN_ORDER, UNKNOWN_FILL, UNKNOWN_BALANCE_CHANGE or UNKNOWN_POSITION_CHANGE. Never silently absorb external activity into the platform ledger. Require explicit operator reconcile/accept with reason and tamper-evident audit evidence.

## Stale private stream
**Severity:** SEV1 if order/fill/account truth can be delayed. Block new risk, reconnect with bounded exponential backoff, query REST account/order truth, replay idempotently and reconcile. Resume only after a configured healthy interval and consistency checks.

## Venue divergence
**Severity:** SEV1 if exchange REST/private-stream/book truth conflicts. Freeze affected execution, invalidate unsafe market data/order-book state, refresh capability/filter metadata and reconcile. Do not synthesize fills or prices from a different venue/instrument.

## Database outage
**Severity:** SEV1. New risk is blocked because financial truth/outbox/audit cannot be durably persisted. Preserve exchange-native protective orders. Recover DB, run migration/schema/read-only checks, reconcile account truth, verify audit/outbox backlog, then require recovery validation before resume.

## Redis outage
**Severity:** SEV2 by default. Redis is not financial truth; bounded cache/fan-out/coordination may degrade while PostgreSQL/exchange truth remains authoritative. If leadership/coordination safety cannot be proven without Redis in a future profile, escalate to SEV1 and block risk. Verify cache reset and no stale coordination state before recovery.

## Disk full
**Severity:** SEV1 when DB/log/audit persistence may fail. Block new risk, preserve protective orders, stop non-essential writers, free/expand capacity without deleting audit/financial evidence, verify filesystem/DB integrity and reconcile before resuming.

## Security compromise / key rotation
**Severity:** SEV1. Disable LIVE, revoke user sessions and exchange credentials, rotate secret-provider material, reconcile the account, verify audit chain/checkpoints, inspect external activity and deployment provenance. New credentials must have minimum READ/TRADE permissions and withdrawal disabled. Security gate and human approval are required before resume.

## Bad deployment
**Severity:** SEV1 if execution/data/security integrity is affected; otherwise SEV2. Stop risk increase, identify immutable release id/hash, roll back or roll forward using the approved artifact, validate schema compatibility, health/readiness, reconciliation and protective orders. Do not rebuild a different artifact from source for PROD recovery.

## Data corruption
**Severity:** SEV1. Quarantine affected data/event ranges; block decisions that depend on them. Verify checksums, event hash/schema/replay compatibility and point-in-time provenance. Restore or reconstruct only from trusted evidence, then run reconciliation and no-lookahead/data-quality smoke checks.

## Backup restore
**Severity:** SEV1 recovery procedure. Restore into an isolated environment first. Validate checksum, schema/migrations, order/fill/ledger referential integrity, audit evidence and read-only application smoke test. Production promotion requires reconciliation and protective-order verification; a backup file merely existing is not recovery proof.

## SEV1 postmortem and return-to-LIVE gate
A SEV1 may require RCA/postmortem before LIVE resumes. Record concrete root cause, contributing conditions, automatic containment, operator actions, corrective/preventive actions, owners and validation evidence. Return to LIVE requires unresolved critical incidents = 0, reconciliation PASS, protective-order safety PASS and all applicable release/security gates.
