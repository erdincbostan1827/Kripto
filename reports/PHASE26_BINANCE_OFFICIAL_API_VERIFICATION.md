# Phase 26 — Binance Official API Reference Verification

Verification date: **2026-08-29**

Official documentation references reviewed:

- https://developers.binance.com/en/docs/introduction
- https://developers.binance.com/en/docs/products/spot/rest-api
- https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-api/user-data-stream

The official Spot REST documentation identifies `/api/v3/exchangeInfo` as the exchange metadata/rate-limit source and documents the supported REST API behavior. The official developer portal also documents authenticated user-data streaming interfaces.

## Runtime source-of-truth policy

This document is a dated documentation verification only. Runtime exchange capabilities, symbol filters, order types, precision, rate limits, and account permissions must be discovered from the live/testnet exchange responses and validated by the runtime capability layer. Static documentation must never override runtime `exchangeInfo` or authenticated capability responses.

If documentation, cached metadata, configured assumptions, and runtime exchange responses disagree, the platform must **fail safe**: block the affected action, refresh capabilities, and require reconciliation rather than guessing.

This verification is **not credentialed TESTNET acceptance**, is not evidence that private endpoints were exercised, and does not enable LIVE trading. Credentialed TESTNET/private-stream acceptance remains a separate external release gate.
