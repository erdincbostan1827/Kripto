# DATA_FLOW.md

1. Public trade/ticker/book/kline messages arrive through the MarketDataCoordinator/combined-stream layer with exchange timestamp and received-at timestamp; subscriptions are sharded deterministically when capacity requires it.
2. Sequence and freshness validators reject stale/out-of-order/incomplete state; REST snapshots are used for documented repair paths.
3. Validated observations are normalized to canonical Asset/Symbol identities and a metadata version.
4. Candles/features are computed only from finalized or explicitly partial data according to strategy policy.
5. Signal snapshots persist the exact data/universe/metadata/config/strategy versions used.
6. The risk engine reads authoritative account/risk reservations; the CapitalAllocator applies cash reserve, open-order reserve, cost buffer, portfolio heat and risk-budget constraints across the candidate cycle before approve/reject/reduce-only decisions.
7. Approved intents are normalized against current symbol filters immediately before submit and risk is recomputed.
8. Submission produces deterministic client order ids. Ambiguous transport results enter UNKNOWN and are queried/reconciled; blind retry is prohibited.
9. Private order/fill events update the ledger transactionally and emit outbox events.
10. Reconciliation compares exchange account, open orders/positions/balances and local ledger. Unexplained drift blocks risk increase.
11. UI consumes REST snapshots plus versioned WebSocket deltas; it does not own trading state.
