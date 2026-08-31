# API Versioning Policy

Release: `0.3.0-local-acceptance`.

REST endpoints are under `/api/v1`. WebSocket messages carry `schema_version`, `message_type` and monotonic/semantic sequence information where applicable. The frontend checks `/api/v1/compatibility` before enabling authenticated risk-changing actions.

A breaking change is one that removes/renames required fields, changes financial semantics, changes state-machine meaning, or invalidates a supported client without an upcaster/compatibility window. Additive optional fields are permitted when readers tolerate unknown fields. Breaking changes require a new API/schema version, migration notes, contract tests and a documented compatibility window.

An incompatible frontend must fail closed for state-changing actions. Deprecation warnings are exposed before a supported version is removed. This local release does not claim external-client compatibility beyond the bundled frontend/source contract.
