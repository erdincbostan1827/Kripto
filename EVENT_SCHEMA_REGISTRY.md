# EVENT_SCHEMA_REGISTRY.md

All persisted domain events include: event_id, event_type, schema_version, aggregate_id, correlation_id, causation_id, sequence, event_time, received_at, producer_version, payload_hash, payload.

Schema `1` events implemented in this release: MarketDataReceived, SignalGenerated, RiskDecision, OrderIntentCreated, OrderStateChanged, FillReceived, PositionUpdated, RiskStateChanged, AccountDriftDetected, AuditCheckpoint, OutboxDispatchResult.

Readers ignore unknown additive fields. Required semantic changes must use an explicit upcaster or hard-fail into quarantine; financial events are never silently dropped.
