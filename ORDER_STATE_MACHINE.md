# ORDER_STATE_MACHINE.md

States: `CREATED -> VALIDATED -> SUBMITTED -> ACKNOWLEDGED -> PARTIALLY_FILLED -> FILLED`; cancellation uses `CANCEL_PENDING -> CANCELLED`; failures use `REJECTED`, `FAILED`, or `UNKNOWN`.

`UNKNOWN` is not `FAILED`. The same symbol is blocked from new risk-increasing intents until `client_order_id`/exchange order query and account reconciliation establish truth. Duplicate submit is prevented by an idempotency key and unique client-order namespace.
