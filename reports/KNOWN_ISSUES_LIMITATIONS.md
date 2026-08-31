# Known Issues / Limitations

Release: `0.3.0-local-acceptance`

Release classification: `LOCAL_ACCEPTANCE_NOT_PRODUCTION_READY`. PROD LIVE: **BLOCKED**; default mode: **PAPER**; live_enabled: **False**.

Current evidence snapshot: **1180 tests collected**, backend coverage **None** (fresh=False, classification=COVERAGE_NOT_FRESH_OR_INCOMPLETE). Requirements: **2691 total / 2591 PASS / 100 NOT_TESTED / 0 UNSUPPORTED**. P0: **1511 total / 1469 PASS / 42 NOT_TESTED**.

## Current production blockers

1. P0 requirements not all PASS ({'PASS': 1469, 'NOT_TESTED': 42})
2. frontend_dependency_resolved_build=NOT_TESTED
3. docker_runtime=NOT_TESTED
4. postgres_runtime_migration=NOT_TESTED
5. redis_runtime_integration=NOT_TESTED
6. redis_restart_drill=NOT_TESTED
7. postgres_restart_drill=NOT_TESTED
8. pitr_restore_drill=NOT_TESTED
9. ha_failover_drill=NOT_TESTED
10. worm_audit_storage=NOT_TESTED
11. credentialed_binance_testnet=NOT_TESTED
12. credentialed_private_stream=NOT_TESTED
13. real_market_paper_campaign=NOT_TESTED
14. live_shadow_campaign=NOT_TESTED
15. real_pit_profitability_evidence=NOT_TESTED
16. supply_chain_scans_and_sbom=NOT_TESTED
17. ci_release_provenance=NOT_TESTED
18. source lock non-compliant: frontend/package-lock.json:MISSING
19. source lock non-compliant: uv.lock:MISSING

This file is generated from the acceptance matrix and release manifest; edit the source evidence/status, not these counts manually.
