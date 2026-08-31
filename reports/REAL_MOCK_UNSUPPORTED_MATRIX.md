# REAL / MOCK / UNSUPPORTED Matrix

Release: `0.3.0-local-acceptance`

Local full-suite evidence: **285/285 PASS**, backend coverage **93%**. Requirement status: **364 PASS / 2300 NOT_TESTED / 27 UNSUPPORTED**; P0: **263 PASS / 1248 NOT_TESTED**. PROD LIVE is **BLOCKED**.

| Capability | Classification | Local evidence |
|---|---|---|
| Decimal/filter/risk/execution state machines | REAL | PASS |
| Authentication/RBAC/MFA/session/audit | REAL | PASS |
| PostgreSQL schema/Alembic offline SQL | REAL source | PASS offline; runtime NOT_TESTED |
| Binance Spot REST/WebSocket adapter contract | REAL source | PASS with mock/fake transport; credentialed NOT_TESTED |
| PAPER execution engine | REAL simulator using MOCK/PAPER market truth | PASS mechanics |
| Backtest/research statistics | REAL calculation code | PASS mechanics; real-market evidence NOT_TESTED |
| Frontend React source | REAL source | syntax PASS; resolved build/E2E NOT_TESTED |
| Docker/PROD compose | REAL configuration | static contract PASS; runtime NOT_TESTED |
| Binance Spot TESTNET | REAL adapter path | NOT_TESTED |
| LIVE trading | REAL guarded code path | BLOCKED / NOT_TESTED |
| Binance Perpetual execution | UNSUPPORTED | UNSUPPORTED |
| On-chain/options/news provider layers | UNSUPPORTED in this release | UNSUPPORTED |
