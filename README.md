# Crypto Trading Platform v5.1 — Production Hardening

Release snapshot: **0.3.0-local-acceptance**. This repository implements a conservative multi-asset crypto trading platform core whose priority follows the v5.1 source of truth: capital preservation → data correctness → execution correctness → risk control → statistical validity → operational reliability. It does **not** claim guaranteed profit or PROD LIVE readiness.

## Verified local state
- Default: `MODE=PAPER`, `MARKET_TYPE=SPOT`.
- `LIVE_TRADING_ENABLED=false`, `AUTO_EXECUTION=false`.
- Canonical test count, test verification, coverage freshness, requirement counts and release blockers are generated evidence; do not copy historical numbers from this README.
- `RELEASE_MANIFEST.json` is the canonical release snapshot and `reports/PROJECT_STATUS.json` must agree with it.
- `scripts/verify_release_consistency.py` fails closed on test-count, coverage, Git binding or release-state drift.
- Fresh coverage is reported only when a complete current-release coverage run exists; historical coverage is never promoted as current evidence.
- PROD LIVE remains blocked unless the canonical release gate independently passes every local and external acceptance requirement.

A green local test suite is not production readiness. See `RELEASE_MANIFEST.json`, `REQUIREMENTS_TRACEABILITY.md`, `reports/PROJECT_STATUS.json` and the production acceptance runbook.

## Canonical architecture
`ARCHITECTURE_DECISIONS.md` and `architecture_profile.yaml` are authoritative. Current profile:
- Python 3.12.14 + FastAPI.
- PostgreSQL 18.6, SQLAlchemy 2, psycopg 3, Alembic expand-contract.
- PostgreSQL transactional outbox for durable financial event truth.
- Redis 8.10.1 for bounded cache/coordination/fan-out; never sole financial truth.
- React 19.2.8, TypeScript 7.0.2 strict, Vite 8.2.2, MUI 9.3.1, TanStack Query 5.102.3.
- nginx 1.30.4, Prometheus 3.14.0, Grafana 13.2.0.
- Single-node production baseline; optional HA design is active-standby with fencing, not active-active execution.

## Installation
### Linux
```bash
cd crypto_trading_platform_v5_1
./install.sh
```

### Windows PowerShell
```powershell
cd crypto_trading_platform_v5_1
.\INSTALL_WINDOWS.ps1
```

The installers bootstrap configuration/secrets and perform available preflight operations. Before PROD use, run the real Docker/PostgreSQL/Redis, TLS, backup/PITR, security and exchange acceptance gates described below.

### Backend development
```bash
PYTHONPATH='backend:.' pytest -q -W error
PYTHONPATH=backend uvicorn app.main:app --reload
```

Local acceptance helpers:
```bash
python scripts/prohibited_scan.py
python scripts/secret_scan.py
PYTHONPATH='backend:.' python scripts/local_load_soak.py
bash scripts/local_fault_injection.sh
python scripts/release_gate.py
```

## Product modes
- `BACKTEST`: historical simulation; no exchange order.
- `PAPER`: simulated fills/positions; no real exchange order.
- `TESTNET`: real exchange test environment; **credentialed acceptance NOT_TESTED in this snapshot**.
- `LIVE`: guarded source path exists but PROD LIVE is **BLOCKED**.

First run is forced to PAPER. LIVE requires backend evidence gates, re-authentication, short-lived single-use confirmation and human approval. UI cannot override backend gates.

## Exchange and market data
The first adapter is Binance Spot. Runtime `exchangeInfo`/symbol filters are source of truth for precision, min/max quantity/notional and supported capabilities. Public REST/WebSocket code handles supported timeframes, reconnect/backoff, heartbeat/stale detection and bounded backpressure. Order mutation ambiguity becomes `UNKNOWN`/reconciliation instead of blind retry.

API keys must use minimum READ/TRADE permissions; withdrawal permission is rejected. Secrets are never intentionally returned to the frontend or logs. Credentialed TESTNET/private-stream acceptance remains required before any release promotion.

## Signal / multi-timeframe pipeline
Validated closed candles flow through data validation → mandatory indicators → market regime → multi-timeframe conflict analysis → composite signal/explainability → risk filters → sizing → protective levels → execution checks. The implementation includes falling-knife protection; an oversold indicator alone cannot create BUY. Bearish SPOT signals are directional exit/avoidance information and do not silently become leveraged shorts.

## Risk and execution
Locally tested controls include Decimal/fixed-precision normalization, fat-finger collar, cost-aware risk sizing, portfolio/daily/weekly/drawdown/exposure limits, quote/volatility-adjusted/consecutive-loss limits, circuit breakers, deterministic intent idempotency, self-trade/conflict checks, UNKNOWN isolation, persistent leader fencing/capital reservation, external-account drift detection, reconciliation and exchange-confirmed protective-stop coverage.

Emergency Stop blocks new risk while preserving protective intent where possible. Panic Close is separate and requires explicit human action.

## PAPER / research / backtest
PAPER supports modeled spread, fees, slippage, latency, partial entry and stop/TP lifecycle. Backtest uses next-bar entry, risk-budget sizing and conservative intrabar stop priority when tick order is unknowable. Walk-forward, purge/embargo, 10,000-path Monte Carlo, effective sample size, PSR/DSR/PBO calculation mechanics are locally tested.

**Synthetic/local results are mechanics evidence only.** They are not positive-expectancy or profitability evidence. Real point-in-time OOS/PAPER/TESTNET/LIVE_SHADOW evidence is still missing.

## Frontend
The React/TypeScript shell exposes the eight primary product areas: Dashboard, Market/Scanner, Analysis, Positions & Orders, Alerts, Backtest & Research, Performance & Risk, Settings/System. LIVE is labeled explicitly as `GERÇEK PARA`. It includes compatibility gating, auth/session/CSRF flow and first-run/MFA management source.

Reproducible frontend dependencies are committed in `frontend/package-lock.json`. The Phase 217 local candidate verified lock-bound dependency installation, Vitest and the TypeScript/Vite production build. A browser acceptance claim is still separate: the canonical runner must complete a fresh `npm ci` and render every required viewport in real Chromium for the exact candidate revision. Registry/DNS failure or an incomplete dependency tree remains fail-closed and cannot be promoted from source/build evidence alone.

## Security
Implemented/local-tested: Argon2id, RBAC, opaque sessions, HttpOnly/Secure/SameSite cookies in PROD, CSRF, login throttling, TOTP MFA, encrypted MFA/exchange secrets, hashed one-use recovery/reset tokens, session revocation, CORS/TrustedHost, HSTS/CSP/security headers, tamper-evident audit, secret provider abstraction, local secret scan and LIVE high-risk confirmation.

Full supply-chain acceptance (resolved locks, vulnerability scan, SAST, SBOM, license review, artifact signing/verification) remains a release blocker.

## Docker / deployment / backup
`docker-compose.yml` defines backend, frontend, PostgreSQL, Redis, reverse proxy, Prometheus, Grafana and watchdog. `docker-compose.prod.yml` adds PROD/TLS/WAL-PITR-oriented settings. This environment has no Docker daemon, so actual compose build/up and real service acceptance are **NOT_TESTED**.

`BACKUP_RESTORE_DRILL.md` documents RPO/RTO design targets, encrypted backup, PITR and mandatory restore drill. Backup encryption/tamper mechanics are locally tested; a real PostgreSQL PITR restore drill has not run.

## Documentation
- `ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `DATA_FLOW.md`
- `TRADING_STATE_MACHINE.md`, `RISK_STATE_MACHINE.md`, `ORDER_STATE_MACHINE.md`
- `SECURITY_MODEL.md`, `DEPLOYMENT_ARCHITECTURE.md`
- `INCIDENT_RUNBOOKS.md`, `BACKUP_RESTORE_DRILL.md`
- `EVENT_SCHEMA_REGISTRY.md`, `DATA_PROVIDER_REGISTRY.yaml`
- `docs/USER_GUIDE.md`, `docs/API_VERSIONING.md`, `docs/TROUBLESHOOTING.md`, `docs/DISASTER_RECOVERY.md`, `docs/STRATEGY_ASSUMPTIONS.md`

## Requirement traceability and release evidence
Machine-readable:
- `REQUIREMENTS_TRACEABILITY_MATRIX.yaml`
- `requirements_acceptance_matrix.yaml`
- `RELEASE_MANIFEST.json`

Human-readable:
- `REQUIREMENTS_TRACEABILITY.md`
- `reports/TEST_EVIDENCE_REPORT.md`
- other reports under `reports/`

PASS is assigned only by evidence-bound rules that reference a current test and evidence file. Mock/fake transport evidence does not convert credentialed TESTNET/LIVE requirements to PASS.

## Known blockers before PROD LIVE
1. 524 P0 requirements remain NOT_TESTED in the current conservative mapping.
2. `uv.lock` is unavailable; local offline resolution lacked required cached metadata.
3. `frontend/package-lock.json` and dependency-resolved frontend build/E2E are unavailable.
4. Docker compose and real PostgreSQL/Redis runtime integration have not run.
5. Real encrypted PITR/restore drill has not run.
6. Credentialed Binance TESTNET/private stream/protective-order/reconciliation acceptance has not run.
7. Real-market PAPER effective-sample and multi-regime campaign has not run.
8. Real point-in-time OOS/walk-forward/purged-embargo/multiple-testing profitability evidence is insufficient.
9. LIVE_SHADOW campaign and live execution-quality divergence evidence are missing.
10. A local unresolved dependency manifest (`reports/SBOM.local.json`) exists, but full resolved-lock vulnerability/SAST/license/signing supply-chain acceptance is still missing.

Until these gates are satisfied, **LIVE remains disabled and PROD LIVE release remains BLOCKED**.

## İlk kurulum ve entegrasyon rehberi
### Binance API anahtarı
1. Binance hesap güvenliği ve MFA etkinleştirildikten sonra yalnız bu platform için ayrı bir API anahtarı oluşturun.
2. En az yetki ilkesini kullanın: gereken profilde yalnız **READ** ve gerekiyorsa **SPOT TRADE** izni verin. **Withdrawal/çekim izni vermeyin**; platform bu yetkiyi reddeder.
3. Anahtarları frontend'e, kaynak koda, Git'e, ekran görüntüsüne veya loglara yazmayın. Kurulum sihirbazı/secret bootstrap yolunu kullanın.
4. TESTNET/LIVE kullanmadan önce permission discovery ve credentialed acceptance testlerini tamamlayın. Bu release snapshot'ında bunlar henüz NOT_TESTED'dir.

### Telegram bot
1. Telegram'da resmi BotFather üzerinden bot oluşturun ve bot tokenını secret provider üzerinden tanımlayın.
2. Chat ID / hedef kanal bilgisini bildirim ayarlarına ekleyin.
3. Test mesajını PAPER ortamında doğrulayın. Token log, API response veya frontend payload içinde görünmemelidir.
4. Kritik bildirimlerde Telegram tek kanal değildir; HTTPS webhook/e-posta yedek kanal politikası kullanılabilir.

### Environment variables ve ilk kurulum sihirbazı
`.env.example` yalnız şema/örnek değerler içindir. Gerçek secret değerleri `.env`, Git veya Docker image içine gömülmemelidir. İlk kurulum sihirbazı adımları sıralı ve restart-safe saklanır; secret alanları wizard snapshot'ına yazılmaz. Son preflight geçmeden kurulum tamamlanmaz ve ilk çalışma modu her durumda **PAPER** olur.

### Mobil / PWA / masaüstü kullanımı
Arayüz responsive web uygulaması olarak masaüstü ve mobil tarayıcıdan kullanılacak şekilde tasarlanmıştır. Bu snapshot'ta bağımsız native masaüstü istemcisi veya doğrulanmış installable PWA paketi yoktur. Kilitli frontend build'i yerel olarak doğrulanmış olsa da mobil/masaüstü browser acceptance, exact-candidate `npm ci` ve gerçek Chromium viewport matrisi tamamlanmadan PASS sayılmaz.

### Kullanıcı dostu hata / uyarı sözlüğü
- **Yeni işlemler durduruldu — piyasa verisi sağlıklı veya yeterince güncel değil:** veri freshness/health kapısı geçmedi; yeni risk açmayın.
- **Yeni işlemler durduruldu — exchange bağlantısı doğrulanamadı:** bağlantı/reconciliation düzelmeden yeni risk açmayın.
- **MANUAL_REVIEW_REQUIRED:** sistem otomatik ACTIVE durumuna dönmez; reconciliation ve insan onayı gerekir.
- **UNPROTECTED_POSITION:** koruyucu emir exchange üzerinde doğrulanmadı; yeni risk kısıtlanır ve recovery akışı çalışır.
- **UNKNOWN order:** emir sonucunun exchange gerçeği belirsizdir; kör retry yapılmaz, query/reconciliation gerekir.
- **PROD_LIVE_RELEASE=BLOCKED:** release gate tamamlanmamıştır; LIVE açılmamalıdır.

## Dependency lock bootstrap (Phase 174)

Production acceptance requires both `uv.lock` and `frontend/package-lock.json`. Generate them atomically with:

```bash
python scripts/bootstrap_dependency_locks.py
python scripts/verify_source_locks.py
```

For an intentionally network-isolated host, `--offline` may be used to prove whether local caches are sufficient. The bootstrap uses a **both-or-none** policy: if either Python or frontend resolution fails, neither canonical lock file is replaced. A machine-readable diagnostic is written to `reports/dependency_lock_bootstrap.json`. A failed resolver run is not acceptance evidence and must not be promoted to PASS.


### External acceptance return transport (Phase 178)

Real acceptance evidence generated on an isolated host can be returned with a deterministic, Git-bound transport bundle:

```bash
python scripts/external/acceptance_return_bundle.py build --output reports/EXTERNAL_ACCEPTANCE_RETURN.zip
python scripts/external/acceptance_return_bundle.py verify reports/EXTERNAL_ACCEPTANCE_RETURN.zip --expected-git-sha "$(git rev-parse HEAD)"
python scripts/external/acceptance_return_bundle.py stage reports/EXTERNAL_ACCEPTANCE_RETURN.zip
```

Staging is intentionally non-promoting: it never overwrites canonical acceptance manifests or turns a requirement PASS. Canonical semantic verifiers and merge gates remain mandatory. The return transport rejects secret-like values, unsafe ZIP members, symlinks, hash/size tampering, unexpected files, and source Git mismatches. It may carry CI-generated dependency locks only as checksum-bound staged artifacts; existing lock promotion controls remain authoritative.


### External acceptance promotion transaction (Phase 179)

A staged return bundle is still **not acceptance**. Assess it first, then require an explicit source-SHA confirmation before canonical promotion:

```bash
python scripts/external/acceptance_return_promotion.py assess reports/external_acceptance/incoming/<bundle_sha256>
python scripts/external/acceptance_return_promotion.py promote reports/external_acceptance/incoming/<bundle_sha256> \
  --confirm-source-sha "$(git rev-parse HEAD)"
```

Promotion revalidates staged hashes, source Git identity, secret policy, and release-relevant external manifests in an isolated detached worktree before changing canonical evidence. Canonical `reports/external_acceptance/` is replaced as a directory transaction with rollback-on-error behavior. Transport or promotion alone never creates PASS; canonical semantic verifiers, trusted challenge, evidence ledger/checkpoint and release gates remain authoritative.

Returned `uv.lock` and `frontend/package-lock.json` are **never auto-promoted into the source tree**. Both locks must arrive together with `reports/lock-promotion/LOCK_PROMOTION_MANIFEST.json`; they are quarantined under `reports/lock-promotion/candidates/<bundle-id>/` for explicit review and must be committed into a new immutable source candidate before `verify_source_locks.py` can regard them as source-compliant.

### Replay-safe acceptance import transaction (Phase 180)

External acceptance return promotion is now replay-safe and post-verified. `scripts/external/acceptance_return_promotion.py` records successful bundle-manifest hashes in a hash-chained `reports/acceptance_import/IMPORT_LEDGER.json`. A previously promoted bundle is rejected with `RETURN_BUNDLE_REPLAY`; a malformed or tampered import ledger fails closed.

After the canonical `reports/external_acceptance/` directory swap, semantic verifiers run again against the actual canonical files and the release gate is re-evaluated. If post-swap verification, lock-candidate quarantine, or import-ledger persistence fails, the canonical evidence directory is rolled back to its pre-transaction state. Release-gate eligibility is recorded as an observation only: promotion never bypasses P0, source-lock, challenge, ledger/checkpoint, provenance, or human-approval requirements.

Returned dependency locks remain review-only candidates. Browser/frontend, supply-chain, CI-build, trust-chain, dependency-lock, and canonical external evidence are classified under one import contract so operators can audit exactly what artifact classes were transported without conflating transport with acceptance.


### Crash-safe acceptance import and trust anchors (Phase 181)

External acceptance promotion now writes a fail-closed transaction journal at `reports/acceptance_import/TRANSACTION_JOURNAL.json` before the canonical directory swap. Before any later promotion, an interrupted transaction is recovered deterministically: if the bundle is absent from the hash-chained import ledger, canonical evidence is rolled back from the preserved backup; if the ledger already contains the bundle, the committed promotion is finalized and stale transaction artifacts are removed. An invalid journal blocks promotion rather than guessing.

Each successful import-ledger event also binds immutable trust-anchor observations from the returned external evidence: the external evidence-ledger SHA-256 and verified head, signed checkpoint SHA-256/head/signature binding, and release-challenge SHA-256 when present. These fields are part of the import event hash chain, so later modification is detected. The trust-anchor record is provenance metadata only; the canonical semantic verifier, externally trusted checkpoint verification, release gate, source locks, P0 matrix, and human LIVE approval remain authoritative.
