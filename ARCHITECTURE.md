# ARCHITECTURE.md

## System context
The platform is an always-on server-side trading system. Browser/PWA/desktop clients are control and observation surfaces only; closing a client cannot stop position protection or the execution state machine.

## Service boundaries
- **API/Auth service:** REST `/api/v1`, authenticated WebSocket, session/RBAC, high-risk confirmations.
- **Market Data service:** Binance public REST/WebSocket, `MarketDataCoordinator` multiplex/sharding registry, sequence/freshness validation, bounded priority backpressure, runtime rate-budget telemetry, REST reconciliation budget and timestamp provenance.
- **Universe/Metadata service:** point-in-time symbol eligibility, filter/version snapshots, listing/delisting lifecycle.
- **Quant service:** indicators, feature registry, regime, multi-timeframe analysis, deterministic strategies, explainability/calibration.
- **Scanner service:** cross-sectional ranking after eligibility and cost gates.
- **Risk service:** per-trade and portfolio budgets, explainable `CapitalAllocator` with cash/cost/open-order reserves and sequential candidate revalidation, capital reservation, correlation/concentration, drawdown/circuit breaker, risk state machine.
- **Execution service:** OrderIntent, pre-trade validation, idempotency, STP conflict checks, state machine, UNKNOWN handling, partial fills, protection, reconciliation.
- **Research service:** backtest, walk-forward, purged/embargo, Monte Carlo, multiple-testing metrics, benchmark and attribution.
- **Paper/Shadow service:** live-market simulated execution and shadow comparison.
- **Persistence service:** PostgreSQL ledger, outbox, event schemas, tamper-evident audit, snapshots.
- **Notification service:** Telegram plus fallback channels; never a trading-state source-of-truth.
- **Watchdog:** independent heartbeat/health observer.

## Canonical decision pipeline
`MarketData -> DataQuality -> PointInTimeUniverse -> Features -> Indicators -> Regime -> MTF -> StrategyEnsemble -> SignalScore -> Abstention/CostGate -> RiskFilter -> PositionSizing -> SL/TP -> ExecutionCheck -> OrderIntent -> Exchange -> Reconciliation -> PositionManagement -> Outcome/Attribution -> ModelHealth`

Every arrow has a timestamp/correlation id. Risk or execution may reject a signal; a signal is never equivalent to an order.

## Financial truth
1. Current exchange/private-stream reality when authenticated and reconciled.
2. PostgreSQL authoritative ledger/outbox.
3. Redis caches/fan-out.
4. UI projections.

Conflicts never get silently resolved in favor of a cache or browser state.

## Failure model
Stale market data, clock drift, DB outage, private stream drift, unknown orders, account drift, unresolved protective order, or leader ambiguity can only keep risk equal or lower. New risk is blocked under ambiguity.
