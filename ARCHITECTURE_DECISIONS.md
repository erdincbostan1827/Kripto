# ARCHITECTURE_DECISIONS.md

## Status
Canonical implementation profile for release `0.3.0`. Production code must not silently switch to an alternative technology. Any deviation requires an ADR update, regression evidence, and a new architecture-profile hash.

## Decision precedence
1. Capital/open-position safety
2. Exchange/account reality and execution correctness
3. Data integrity and point-in-time correctness
4. Identity/secret/access security
5. Ledger/audit correctness
6. Deterministic recovery/replay
7. Statistical validity
8. Usability/performance/UX

## ADR-001 — Python dependency/runtime
- **ADR_ID:** `ADR-001`
- **selected_option:** Python 3.12.14-compatible runtime; `pyproject.toml`; uv-compatible dependency declaration; FastAPI/AnyIO async request and I/O layer; deterministic synchronous financial core.
- **alternatives_considered:** Poetry; pip-tools; synchronous WSGI runtime.
- **rationale:** FastAPI-native I/O with explicit dependency boundaries while keeping money/state transitions deterministic.
- **operational_tradeoff:** Async lifecycle and cancellation require explicit shutdown discipline; a fully resolved lock is still a release blocker in this environment.
- **security_tradeoff:** Fewer runtime layers reduce attack surface, but dependency provenance still requires lock/SBOM/security scans before PROD promotion.
- **rollback/migration impact:** Packaging-tool changes may be isolated; changing the runtime concurrency model requires state-machine, cancellation, load and failover regression.

## ADR-002 — Core eventing
- **ADR_ID:** `ADR-002`
- **selected_option:** PostgreSQL transactional outbox plus typed in-process domain events; Redis is bounded cache/coordination/fan-out only.
- **alternatives_considered:** Redis Streams, Kafka, RabbitMQ as primary financial event truth.
- **rationale:** Order/fill/risk events must survive cache/broker failure; state and outbox commit atomically.
- **operational_tradeoff:** Lower throughput than a dedicated log broker, acceptable for the selected account/execution profile.
- **security_tradeoff:** Financial truth is kept in the access-controlled database rather than an ephemeral cache; DB availability becomes a new-risk gate.
- **rollback/migration impact:** A durable broker can be introduced only with replay, idempotency, dual-read/write migration and poison-event evidence.

## ADR-003 — Trading engine scheduling
- **ADR_ID:** `ADR-003`
- **selected_option:** Long-lived asyncio loops for market data, private stream, reconciliation, risk and execution; Celery/Redis reserved for non-execution-critical research/report jobs.
- **alternatives_considered:** Celery for every trading task; APScheduler as execution scheduler.
- **rationale:** Order state and account ownership must not depend on arbitrary queue latency.
- **operational_tradeoff:** More explicit lifecycle/heartbeat/reconnect logic is required.
- **security_tradeoff:** Separating execution-critical work from general task workers reduces the blast radius of worker compromise/misconfiguration.
- **rollback/migration impact:** Scheduler changes require execution ordering, leader fencing, reconciliation and fault-injection regression.

## ADR-004 — Database
- **ADR_ID:** `ADR-004`
- **selected_option:** PostgreSQL 18.6 canonical production profile; psycopg 3; SQLAlchemy 2 synchronous transaction boundary; Alembic expand-contract; PostgreSQL native partitioning where required.
- **alternatives_considered:** Mandatory TimescaleDB; SQLite production; document database as financial ledger.
- **rationale:** Strong transactions, constraints, JSON support, WAL/PITR and mature operational tooling.
- **operational_tradeoff:** Higher operational complexity than embedded storage; PostgreSQL outage blocks new risk.
- **security_tradeoff:** Centralized access controls/encryption/backup policy are stronger, but credentials and backups require explicit secret/access governance.
- **rollback/migration impact:** Managed PostgreSQL is compatible; database-engine replacement is unsupported. Schema changes follow expand → migrate/backfill → switch → contract.

## ADR-005 — Authentication/session
- **ADR_ID:** `ADR-005`
- **selected_option:** Opaque server-side session id in `HttpOnly; Secure; SameSite=Strict` cookie, Argon2id password hashing, TOTP MFA/recovery codes, RBAC, CSRF protection, high-risk re-authentication/one-time confirmation.
- **alternatives_considered:** Long-lived browser-local JWT; reversible password storage; Telegram-only authorization.
- **rationale:** Revocation, inactivity timeout and high-risk-action confirmation are first-class controls.
- **operational_tradeoff:** Session persistence and MFA recovery require database availability and recovery procedures.
- **security_tradeoff:** Browser never receives exchange secrets or reusable long-lived auth material; compromised web sessions are revocable.
- **rollback/migration impact:** Any token model replacement must preserve revocation, CSRF/browser security, MFA and audit semantics.

## ADR-006 — Exchange integration
- **ADR_ID:** `ADR-006`
- **selected_option:** Binance Spot first; runtime capability/filter discovery; exchange/account represented separately; official documented exchange contracts are authoritative.
- **alternatives_considered:** CCXT as source-of-truth abstraction; hard-coded order/filter capabilities.
- **rationale:** Execution correctness requires exchange-native order/filter/private-stream semantics.
- **operational_tradeoff:** More adapter code and contract tests per venue.
- **security_tradeoff:** API permission snapshots, encrypted credentials and withdrawal rejection are explicit rather than hidden by a generic adapter.
- **rollback/migration impact:** A library may wrap transport but cannot suppress capability discovery, idempotency, UNKNOWN-order reconciliation or account-boundary checks.

## ADR-007 — Precision
- **ADR_ID:** `ADR-007`
- **selected_option:** `Decimal` for prices, quantities, balances, fees, PnL and notionals; explicit tick/step rounding; risk re-check after normalization.
- **alternatives_considered:** Binary floating point for financial values.
- **rationale:** Prevents silent financial rounding and normalization drift.
- **operational_tradeoff:** Slightly lower arithmetic throughput, negligible relative to network/exchange latency.
- **security_tradeoff:** Reduces fat-finger/overflow/non-finite-value paths that can create unintended exposure.
- **rollback/migration impact:** No rollback to binary float is permitted for financial truth.

## ADR-008 — Frontend
- **ADR_ID:** `ADR-008`
- **selected_option:** React 19.2.8, TypeScript 7.0.2 strict mode, Vite 8.2.2, MUI 9.3.1, TanStack Query 5.102.3, bounded local UI state, Lightweight Charts 5.x-compatible integration.
- **alternatives_considered:** Global Redux for all state; Next.js SSR; client-owned trading state.
- **rationale:** Trading engine remains server-side source-of-truth while the client remains a responsive product UI.
- **operational_tradeoff:** No SSR dependency; frontend dependency lock/build remains a release gate until registry-resolved evidence exists.
- **security_tradeoff:** Cookies/CSRF and compatibility gating avoid browser-stored exchange secrets and block incompatible state-changing clients.
- **rollback/migration impact:** Framework-major changes require compatibility, component, accessibility and E2E regression.

## ADR-009 — Deployment
- **ADR_ID:** `ADR-009`
- **selected_option:** Docker Compose `SINGLE_NODE_PRODUCTION` baseline with nginx, app/worker, PostgreSQL, Redis, Prometheus, Grafana and independent watchdog; optional HA is active-standby with database-backed fencing.
- **alternatives_considered:** Active-active execution engines; single process with no watchdog; mutable `latest` tags.
- **rationale:** Two active LIVE leaders for one account are prohibited and host/process failure must be externally detectable.
- **operational_tradeoff:** Single-node profile can experience host downtime; HA requires tested failover before being advertised.
- **security_tradeoff:** Non-root/read-only/capability-dropped containers reduce host blast radius; production secrets remain external to images/source.
- **rollback/migration impact:** Kubernetes/managed services may replace the platform layer only if leader fencing, reconciliation, immutable promotion and secret isolation remain equivalent.

## ADR-010 — LIVE policy
- **ADR_ID:** `ADR-010`
- **selected_option:** First boot `PAPER`; LIVE disabled; release-pinned validation manifest plus security/reconciliation/protective-order/statistical gates and one-time human approval are mandatory.
- **alternatives_considered:** Toggle-only LIVE; Telegram command alone; automatic promotion after a fixed trade count.
- **rationale:** Capital preservation and evidence quality outrank convenience.
- **operational_tradeoff:** Activation is intentionally slower and requires accumulated evidence.
- **security_tradeoff:** Configuration mistakes or compromised notification channels cannot independently enable unrestricted LIVE risk.
- **rollback/migration impact:** No rollback to toggle-only enablement is permitted; gate schema changes require backward-compatible evidence migration.
