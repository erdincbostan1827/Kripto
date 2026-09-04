# Phase 262 final-main push dispatch

The Issue #47 comment router remains fail-closed, but connector-originated issue comments did not produce a GitHub Actions `issue_comment` run in the observed environment. This document does not treat that absence as acceptance evidence.

The final-main push router therefore closes only the dispatch transport gap:

1. It is triggered only by a push to `main` that introduces/changes the router workflow itself.
2. `candidate_ref` is the exact 40-character `github.sha` of that main push.
3. It polls GitHub Actions for the same candidate SHA and requires SUCCESS from CI, Phase223, Phase224, Phase225, and the backend full-tree type-debt ratchet.
4. Any completed non-success gate fails closed.
5. Only after all five gates PASS does it request the existing Phase245 Binance Spot TESTNET acceptance with `symbol=AUTO`, `max_notional=15`, and `partial_price=AUTO`.
6. Router success or dispatch acceptance is never Phase245 evidence and never authorizes real-money LIVE trading.
