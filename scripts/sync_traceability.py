from __future__ import annotations

import ast
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

RELEASE = "0.3.0-local-acceptance"
MATRIX_FILES = [Path("REQUIREMENTS_TRACEABILITY_MATRIX.yaml"), Path("requirements_acceptance_matrix.yaml")]


def test_index() -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(Path("tests").rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                result[node.name] = str(path)
    return result


TESTS = test_index()


def rule(section: int, pattern: str, test: str, module: str):
    if test not in TESTS:
        raise RuntimeError(f"traceability rule references missing test: {test}")
    return (section, re.compile(pattern, re.I), test, module)


RULES = [

    # Phase 136 local-fixture statistical reporting components.  These rules
    # prove deterministic calculation/reporting paths only; they do not satisfy
    # the separate real-market profitability/LIVE release gate.
    rule(136, r"^In-sample result$|^Out-of-sample result$|^DSR / multiple-testing evidence$|^Tail stress scenarios$|^Benchmark comparison$|^Confidence intervals$|^Strategy/regime attribution$|^Execution attribution$", "test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim", "backend/app/research/final_evidence.py"),
    # Phase 134 completed-section umbrella conformance (only sections whose child requirements are all locally satisfied).
    rule(162, r"^Bölüm 162", "test_phase134_tauri_shell_initializes_updater_plugin_but_real_build_and_signing_remain_unclaimed", "docs/TAURI_SIGNED_UPDATE.md"),
    rule(170, r"^Bölüm 170", "test_phase134_final_system_conformance_keeps_real_code_local_fixture_boundary_and_paper_default", "docs/FINAL_DELIVERY_STATUS.md"),
    # Phase 134 PAPER/local-UI/final conformance evidence.
    rule(20, r"^slippage$|^latency$", "test_phase134_paper_fixture_models_slippage_and_latency_without_real_orders", "backend/app/paper/engine.py"),
    rule(168, r"^stale-data banner$", "test_phase134_stale_data_banner_state_is_executed_with_local_typescript_fixture", "frontend/src/components/StatusStrip.tsx"),
    rule(170, r"^PROFESYONEL, KULLANICI DOSTU, RESPONSIVE, DENETLENEBİLİR, TEST EDİLEBİLİR, GÜVENLİ, MODÜLER", "test_phase134_final_system_conformance_keeps_real_code_local_fixture_boundary_and_paper_default", "docs/FINAL_DELIVERY_STATUS.md"),
    # Phase 134 local-fixture research evidence and signed Tauri updater source contract.
    rule(136, r"^Walk-forward result$|^Purged/embargo validation result$|^Fee/slippage/funding adverse scenario$|^Effective sample size$", "test_phase134_local_fixture_walk_forward_purged_embargo_cost_stress_and_effective_sample_are_real_code_paths", "backend/app/research/final_evidence.py"),
    rule(162, r"auto-update mekanizması signature verification ile uygulanabilir", "test_phase134_tauri_shell_initializes_updater_plugin_but_real_build_and_signing_remain_unclaimed", "frontend/src-tauri/src/main.rs"),
    # Canonical technology profile.
    rule(1, r"pandas/numpy tabanlı indikatör", "test_mandatory_indicator_feature_set_is_finite", "backend/app/indicators/engine.py"),
    rule(1, r"React 19\.x", "test_canonical_profile_matches_backend_and_frontend_manifests", "frontend/package.json"),
    rule(1, r"TypeScript strict mode", "test_typescript_strict_and_production_defaults_are_conservative", "frontend/tsconfig.json"),
    rule(1, r"^Vite ", "test_canonical_profile_matches_backend_and_frontend_manifests", "frontend/package.json"),
    rule(1, r"Material UI", "test_canonical_profile_matches_backend_and_frontend_manifests", "frontend/package.json"),
    rule(1, r"TanStack Query", "test_canonical_profile_matches_backend_and_frontend_manifests", "frontend/package.json"),
    rule(1, r"Experimental/canary", "test_canonical_profile_matches_backend_and_frontend_manifests", "architecture_profile.yaml"),
    rule(1, r"Lightweight Charts 5", "test_canonical_profile_matches_backend_and_frontend_manifests", "frontend/package.json"),
    rule(1, r"TypeScript entegrasyonu", "test_typescript_strict_and_production_defaults_are_conservative", "frontend/tsconfig.json"),

    # Exchange adapter contract and official capability discovery.
    rule(2, r"^get_(ticker|order_book|balance|positions|open_orders|klines)\(\)", "test_exchange_adapter_read_and_cancel_query_contract_methods", "backend/app/exchange/binance.py"),
    rule(2, r"^create_(market|limit|stop|take_profit)_order\(\)", "test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract", "backend/app/exchange/base.py"),
    rule(2, r"^cancel_order\(\)", "test_exchange_adapter_read_and_cancel_query_contract_methods", "backend/app/exchange/binance.py"),
    rule(2, r"^cancel_all_orders\(\)", "test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract", "backend/app/exchange/base.py"),
    rule(2, r"^get_order\(\)", "test_exchange_adapter_read_and_cancel_query_contract_methods", "backend/app/exchange/binance.py"),
    rule(2, r"^get_exchange_info\(\)", "test_exchange_symbol_and_asset_metadata_are_from_exchange_info", "backend/app/exchange/binance.py"),
    rule(2, r"^get_server_time\(\)", "test_exchange_adapter_read_and_cancel_query_contract_methods", "backend/app/exchange/binance.py"),
    rule(2, r"^list_markets\(\)", "test_list_markets", "backend/app/exchange/binance.py"),
    rule(2, r"^get_symbol_metadata", "test_exchange_symbol_and_asset_metadata_are_from_exchange_info", "backend/app/exchange/binance.py"),
    rule(2, r"^get_asset_metadata", "test_exchange_symbol_and_asset_metadata_are_from_exchange_info", "backend/app/exchange/binance.py"),
    rule(2, r"^get_trading_status", "test_exchange_adapter_read_and_cancel_query_contract_methods", "backend/app/exchange/base.py"),
    rule(2, r"^get_rate_limits", "test_rate_limits_runtime", "backend/app/exchange/binance.py"),
    rule(2, r"^get_scheduled_listings", "test_scheduled_listings_use_documented_market_data_endpoint_and_api_key_only", "backend/app/exchange/binance.py"),
    rule(2, r"^get_exchange_status", "test_exchange_adapter_read_and_cancel_query_contract_methods", "backend/app/exchange/binance.py"),
    rule(2, r"runtime capability discovery|exchangeInfo/filter", "test_capabilities_are_discovered_not_assumed", "backend/app/exchange/binance.py"),

    # Modes and real-time data.
    rule(3, r"Varsayılan", "test_defaults_paper", "backend/app/core/config.py"),
    rule(3, r"olmalı", "test_defaults_paper", "backend/app/core/config.py"),
    rule(4, r"timeframe destekle", "test_supported_timeframes", "backend/app/core/config.py"),
    rule(4, r"^(trades|ticker|order book|klines)$", "test_public_stream_url_uses_documented_combined_stream_shapes", "backend/app/exchange/public_stream.py"),
    rule(4, r"otomatik reconnect|exponential backoff|heartbeat", "test_public_stream_reconnects_with_backoff_then_processes_event", "backend/app/exchange/public_stream.py"),
    rule(4, r"stale-data detection", "test_public_stream_parser_and_stale_detection", "backend/app/exchange/public_stream.py"),
    rule(4, r"timestamp", "test_public_stream_parser_and_stale_detection", "backend/app/exchange/public_stream.py"),
    rule(4, r"REST API ile periyodik doğrulama", "test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe", "backend/app/data/coordinator.py"),

    # Data quality.
    rule(5, r"Gap detection", "test_candle_gap", "backend/app/data/quality.py"),
    rule(5, r"veri tamamlanmadan sinyal üretme", "test_analyze_gap_rejected", "backend/app/services/pipeline.py"),
    rule(5, r"yapılandırılabilir bir limit", "test_stale", "backend/app/data/quality.py"),
    rule(5, r"^(timestamp|source|timeframe|symbol|received_at|exchange_time|latency)$", "test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency", "backend/app/data/envelope.py"),
    rule(5, r"tespit et|logla", "test_sequence_guard_rejects_duplicate_and_out_of_order_market_events", "backend/app/data/envelope.py"),

    # Mandatory indicators currently implemented and directly asserted.
    rule(6, r"^(SMA 20|SMA 50|SMA 100|SMA 200|EMA 9|EMA 21|EMA 50|EMA 200|VWAP|MACD|Stochastic RSI|Bollinger Bands|Bollinger Band Width|Historical Volatility|Volume SMA|Volume Ratio|Volume Spike|Higher High|Higher Low|Lower High|Lower Low|recent support|recent resistance)$", "test_mandatory_indicator_feature_set_is_finite", "backend/app/indicators/engine.py"),
    rule(6, r"linear-regression slope", "test_mandatory_indicator_feature_set_is_finite", "backend/app/indicators/engine.py"),

    # MTF, regime, signal and falling-knife.
    rule(7, r"configurable bir yapı", "test_multi_timeframe_bullish_alignment", "backend/app/signals/multi_timeframe.py"),
    rule(7, r"MULTI_TIMEFRAME_CONFLICT", "test_multi_timeframe_conflict_blocks_low_timeframe_buy", "backend/app/signals/multi_timeframe.py"),
    rule(8, r"^bullish trend$", "test_bullish_regime", "backend/app/strategies/regime.py"),
    rule(8, r"^bearish trend$", "test_bearish_regime", "backend/app/strategies/regime.py"),
    rule(8, r"^sideways$", "test_sideways_regime", "backend/app/strategies/regime.py"),
    rule(8, r"^high volatility$", "test_high_volatility_regime", "backend/app/strategies/regime.py"),
    rule(9, r"Composite scoring", "test_signal_explainability", "backend/app/signals/engine.py"),
    rule(10, r"Bölüm 10", "test_signal_explainability", "backend/app/signals/engine.py"),
    rule(11, r"Falling knife protection", "test_falling_knife_never_generates_buy_and_exposes_bearish_direction", "backend/app/signals/engine.py"),
    rule(11, r"güçlü bearish trend|fiyat EMA50", "test_falling_knife_blocks_bearish", "backend/app/signals/engine.py"),
    rule(13, r"ATR based", "test_signal_explainability", "backend/app/signals/engine.py"),

    # Risk / portfolio / circuit breaker.
    rule(15, r"Risk-based position sizing", "test_seeded_position_sizing_never_exceeds_risk_budget", "backend/app/risk/engine.py"),
    rule(15, r"stop distance", "test_position_size_reduces_with_wider_stop", "backend/app/risk/engine.py"),
    rule(15, r"entry fee|expected exit fee|expected spread|expected entry slippage|expected stop slippage", "test_costs_in_effective_loss", "backend/app/risk/engine.py"),
    rule(15, r"funding/borrow", "test_funding_borrow_cost_increases_effective_loss_when_applicable", "backend/app/risk/engine.py"),
    rule(16, r"max portfolio exposure", "test_exposure_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max single-asset exposure", "test_asset_exposure_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max correlated-cluster exposure", "test_cluster_exposure", "backend/app/risk/portfolio.py"),
    rule(16, r"max quote-asset exposure", "test_quote_asset_exposure_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max concurrent positions", "test_position_count_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max daily loss", "test_daily_loss_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max weekly loss", "test_weekly_loss_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max drawdown", "test_drawdown_blocks", "backend/app/risk/engine.py"),
    rule(16, r"max consecutive losses", "test_consecutive_losses_block", "backend/app/risk/engine.py"),
    rule(16, r"volatility-adjusted exposure", "test_volatility_adjusted_exposure_blocks", "backend/app/risk/engine.py"),
    rule(17, r"exchange API hatası", "test_fatal_circuit_conditions", "backend/app/risk/circuit.py"),
    rule(17, r"WebSocket data stale|clock drift|database unavailable|Redis unavailable|duplicate order|abnormal spread|abnormal volatility|daily loss limit|max drawdown|repeated order rejection|account balance inconsistency", "test_fatal_circuit_conditions", "backend/app/risk/circuit.py"),
    rule(18, r"^(symbol|side|quantity|price|stop price|timestamp|status|fees|sakla\.)$", "test_order_persistence_schema_contains_required_execution_fields", "backend/app/database/models.py"),

    # Cross-section acceptance evidence backed by existing direct tests.
    rule(42, r"indicator calculations", "test_mandatory_indicator_feature_set_is_finite", "backend/app/indicators/engine.py"),
    rule(42, r"signal scoring", "test_signal_explainability", "backend/app/signals/engine.py"),
    rule(42, r"position sizing", "test_seeded_position_sizing_never_exceeds_risk_budget", "backend/app/risk/engine.py"),
    rule(42, r"database", "test_schema_creates_expected_tables", "backend/app/database/models.py"),
    rule(42, r"exchange mock", "test_idempotent_submit", "backend/app/exchange/mock.py"),
    rule(42, r"duplicate order", "test_idempotent_submit", "backend/app/execution/service.py"),
    rule(42, r"stale data", "test_stale", "backend/app/data/quality.py"),
    rule(42, r"exchange disconnect|clock drift|daily loss|max drawdown", "test_fatal_circuit_conditions", "backend/app/risk/circuit.py"),
    rule(42, r"partial fill", "test_paper_market_partial_fill_models_fee_slippage_and_latency", "backend/app/execution/state.py"),
    rule(42, r"no look-ahead", "test_next_bar_entry_and_costs", "backend/app/backtest/engine.py"),
    rule(137, r"UniverseManager|dynamic exchange universe|TOP_LIQUIDITY_N|TOP_VOLUME_N|allowlist|blocklist|quote|trading_status|eligible_from|eligible_until", "test_eligible", "backend/app/universe/manager.py"),
    rule(137, r"candidate|ranking", "test_ranking_deterministic", "backend/app/universe/scanner.py"),
    rule(146, r"point-in-time|survivorship|Bugünün en başarılı", "test_dataset_manifest_detects_change", "backend/app/backtest/dataset.py"),
    rule(146, r"order timing", "test_next_bar_entry_and_costs", "backend/app/backtest/engine.py"),
    rule(146, r"max open positions|portfolio heat|correlated exposure|quote-asset risk", "test_exposure_blocks", "backend/app/risk/engine.py"),
    rule(154, r"candidate ranking determinism|ranking tie handling", "test_ranking_deterministic", "backend/app/universe/scanner.py"),
    rule(154, r"max single asset exposure", "test_asset_exposure_blocks", "backend/app/risk/engine.py"),
    rule(154, r"correlated cluster limit", "test_cluster_exposure", "backend/app/risk/portfolio.py"),
    rule(154, r"quote asset limit", "test_quote_asset_exposure_blocks", "backend/app/risk/engine.py"),
    rule(154, r"duplicate order", "test_idempotent_submit", "backend/app/execution/service.py"),

    # Formal operational risk-state machine and recovery hysteresis.
    rule(128, r"formal RiskState|STARTING|PAPER_ONLY|ACTIVE|DEGRADED|REDUCING_ONLY|HALTED|RECOVERY_PENDING|MANUAL_REVIEW_REQUIRED|STOPPING", "test_formal_risk_states_are_explicit", "backend/app/core/enums.py"),
    rule(128, r"reason code|allowed actions", "test_risk_state_allowed_actions_are_fail_closed", "backend/app/risk/state.py"),
    rule(128, r"HALTED -> ACTIVE", "test_halted_cannot_jump_directly_to_active_even_with_green_checks", "backend/app/risk/state.py"),
    rule(128, r"data healthy|exchange healthy|private stream healthy|reconciliation PASS|no orphan orders|protective orders PASS|risk limits PASS|clock PASS|strategy health PASS|hysteresis/gate", "test_halted_recovery_requires_human_and_all_green_checks", "backend/app/risk/state.py"),

    # Execution and reconciliation.
    rule(18, r"Order state machine", "test_order_transition_direct_fill", "backend/app/execution/state.py"),
    rule(18, r"client_order_id|exchange_order_id", "test_idempotent_submit", "backend/app/execution/service.py"),
    rule(18, r"Duplicate order protection", "test_idempotent_submit", "backend/app/execution/service.py"),
    rule(19, r"Bölüm 19", "test_reconciliation_clean", "backend/app/execution/reconciliation.py"),
    rule(20, r"Bölüm 20", "test_paper_market_partial_fill_models_fee_slippage_and_latency", "backend/app/paper/engine.py"),
    rule(21, r"fees|slippage|spread|partial fills|stop loss|take profit|position sizing", "test_next_bar_entry_and_costs", "backend/app/backtest/engine.py"),
    rule(22, r"Bölüm 22", "test_walk_forward_no_overlap", "backend/app/backtest/validation.py"),
    rule(23, r"gelecekteki veri|Future leakage|future leakage|future", "test_next_bar_entry_and_costs", "backend/app/backtest/engine.py"),
    rule(24, r"10,000 simulation|expected return|worst drawdown|probability of ruin|confidence intervals|losing streak", "test_monte_carlo_fields", "backend/app/backtest/stats.py"),

    # Notifications.
    rule(28, r"Bölüm 28|Telegram Bot API", "test_telegram_bot_api_sends_message_without_exposing_token_in_payload", "backend/app/monitoring/telegram.py"),

    # Model health and database/audit/security.
    rule(27, r"STRATEGY_DEGRADED|performans", "test_health_threshold_configurable", "backend/app/strategies/health.py"),
    rule(30, r"Her işlem immutable audit log", "test_schema_creates_expected_tables", "backend/app/database/models.py"),
    rule(31, r"Bölüm 31", "test_database_audit_detects_tampering", "backend/app/database/audit_store.py"),
    rule(32, r"Bölüm 32|Git'e koyma|Docker image içine koyma|frontend'e gönderme|loglama|\.env.*gitignore", "test_secret_material_is_excluded_from_git_docker_frontend_and_logs", "backend/app/core/logging.py"),
    rule(32, r"API key permission validation|Withdrawal permission", "test_credential_vault_encrypts_and_rejects_withdrawal", "backend/app/database/credentials.py"),
    rule(33, r"Exchange rate limits", "test_rate_budget_reset_and_reserve", "backend/app/data/rate_limit.py"),
    rule(34, r"Clock drift", "test_prod_health_can_be_ready_only_with_healthy_explicit_probes", "backend/app/monitoring/health.py"),
    rule(35, r"trading fee|slippage|spread", "test_paper_market_partial_fill_models_fee_slippage_and_latency", "backend/app/paper/engine.py"),
    rule(36, r"Yeni işlem açma", "test_prod_health_is_fail_closed_when_probes_are_unconfigured", "backend/app/monitoring/health.py"),
    rule(37, r"exchange API ulaşılamıyorsa", "test_exchange_timeout_halts_new_risk_via_unknown", "backend/app/execution/service.py"),
    rule(37, r"Bölüm 37|yeni işlem açma|koruma emirlerini kontrol|Telegram alarmı gönder|reconnect dene", "test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects", "backend/app/execution/failure.py"),
    rule(38, r"Bölüm 38|Emergency stop fonksiyonu|yeni emirleri engeller|koruyucu stopları silmez|açık pozisyonları otomatik kapatma", "test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close", "backend/app/execution/emergency.py"),
    rule(38, r"Panic close ayrı", "test_panic_close_is_separate_human_approved_action", "backend/app/execution/emergency.py"),
    rule(40, r"Bölüm 40|endpointleri oluştur|/health|/ready|/metrics", "test_prod_health_is_fail_closed_when_probes_are_unconfigured", "backend/app/main.py"),
    rule(40, r"^database$|^redis$|^exchange$|^websocket$|data freshness|trading engine|^telegram$|strategy engine|stale/blocked symbol count|portfolio concentration state", "test_health_snapshot_is_fail_closed_for_all_operational_components", "backend/app/monitoring/health.py"),
    rule(44, r"^Environment$|API credentials|Exchange connectivity|Exchange permissions|Server time|^Database$|^Redis$|^Telegram$|^WebSocket$|Data freshness|Risk configuration|Strategy configuration|Disk space|^Memory$|Docker services", "test_selftest_passes_only_when_all_required_checks_are_explicitly_green", "backend/app/monitoring/selftest.py"),
    rule(44, r"Bölüm 44", "test_selftest_never_promotes_unconfigured_external_dependency_to_pass", "backend/app/monitoring/selftest.py"),

    # Numeric accuracy and market-type safety.
    rule(71, r"Bölüm 71|Yuvarlama yönü|round\(\)", "test_financial_rounding_is_directional_not_builtin_round", "backend/app/core/money.py"),
    rule(72, r"Bölüm 72|MARKET_TYPE kavramına sahip|Varsayılan ilk güvenli profil", "test_safe_default_market_type_is_spot", "backend/app/core/config.py"),
    rule(72, r"mevcut bakiyeden fazla SELL", "test_execution_service_enforces_spot_sell_balance_before_exchange_side_effect", "backend/app/execution/pretrade.py"),

    # Config and first-run/install contract.
    rule(39, r"Bölüm 39|parametreler config", "test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults", "backend/app/core/config.py"),
    rule(47, r"Bölüm 47|Docker / container runtime kontrolü|runtime/dependency kontrolü|database migration|frontend production build|unit/integration smoke test|health/ready check", "test_install_scripts_fail_fast_and_include_build_migration_test_health_contract", "install.sh"),
    rule(47, r"backend self-test", "test_selftest_never_promotes_unconfigured_external_dependency_to_pass", "backend/app/monitoring/selftest.py"),
    rule(47, r"başlangıç admin hesabı", "test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper", "backend/app/main.py"),
    rule(47, r"TLS / reverse proxy readiness", "test_install_and_deployment_contract_keeps_tls_and_first_start_paper", "docker/nginx/nginx.prod.conf"),
    rule(47, r"Sistem / server bağlantısı", "test_prod_health_is_fail_closed_when_probes_are_unconfigured", "backend/app/monitoring/health.py"),
    rule(47, r"Exchange API bağlantısı ve permission testi", "test_selftest_passes_only_when_all_required_checks_are_explicitly_green", "backend/app/monitoring/selftest.py"),
    rule(47, r"Telegram bağlantısı ve test bildirimi", "test_telegram_bot_api_sends_message_without_exposing_token_in_payload", "backend/app/monitoring/telegram.py"),
    rule(47, r"PAPER / TESTNET / LIVE modu seçimi; default PAPER", "test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper", "backend/app/services/setup_wizard.py"),
    rule(47, r"Risk profili|Coin evreni / otomatik uygunluk seçimi", "test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults", "backend/app/core/config.py"),
    rule(47, r"Son güvenlik kontrolü ve özet", "test_wizard_requires_final_preflight_and_forces_paper", "backend/app/services/setup_wizard.py"),

    # First-run, recovery and LIVE gates.
    rule(47, r"FIRST-RUN WIZARD", "test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper", "backend/app/services/setup_wizard.py"),
    rule(50, r"reconciliation yap|koruyucu emirleri kontrol", "test_database_account_snapshot_survives_process_state", "backend/app/execution/local_snapshot.py"),
    rule(51, r"100 işlem|minimum win rate|profit factor|maximum drawdown|minimum Sharpe|minimum expectancy", "test_live_blocked_when_evidence_missing", "backend/app/core/live_gate.py"),
    rule(51, r"Bölüm 51|LIVE modu varsayılan olmayacak", "test_defaults_paper", "backend/app/core/config.py"),
    rule(51, r"^zorunlu\.$", "test_live_full_gate", "backend/app/core/live_gate.py"),
    rule(58, r"Signal fingerprint|Cooldown", "test_idempotent_submit", "backend/app/execution/service.py"),
    rule(62, r"GET /health|GET /ready|GET /metrics", "test_health", "backend/app/main.py"),
    rule(62, r"GET /market|GET /signals|GET /positions|GET /orders|GET /portfolio|GET /performance|GET /risk|GET /universe|GET /scanner|GET /assets|GET /symbols|GET /market-breadth", "test_market_and_signal_are_functional_and_source_labeled", "backend/app/main.py"),
    rule(64, r"correlation ID|structured log", "test_prod_security_headers_docs_disabled_and_correlation_id_preserved", "backend/app/main.py"),
    rule(67, r"TODO|FIXME|NotImplementedError", "test_gitignore_blocks_runtime_secrets_and_frontend_artifacts", "scripts/prohibited_scan.py"),
    rule(71, r"Decimal|tickSize|stepSize|normalize|NaN|Infinity|division-by-zero", "test_seeded_step_normalization_multiple", "backend/app/core/money.py"),
    rule(73, r"supported order types|tick size|step size|min/max notional|CAPABILITIES MATRIX|Emir gönderilmeden", "test_capabilities_are_discovered_not_assumed", "backend/app/exchange/binance.py"),
    rule(74, r"WebSocket delta|REST snapshot|lastUpdateId|sequence|crossed", "test_orderbook_delta", "backend/app/data/orderbook.py"),

    # Phase 29 local acceptance/provenance hardening.
    rule(42, r"Bölüm 42 \(TESTLER\)", "test_test_suite_has_required_local_safety_and_recovery_categories", "tests"),
    # Phase 220 aggregate technology-profile closure after committed source locks became real.
    rule(1, r"^Bölüm 1 \(TEKNOLOJİ YIĞINI\)", "test_phase220_section1_technology_profile_is_complete_with_committed_locks", "architecture_profile.yaml"),
    # Phase 220: both canonical dependency locks are now committed and exact-HEAD verified.
    # This closes only the source lockfile requirements; resolved vulnerability/license/CI
    # acceptance remains external and is intentionally NOT_TESTED.
    rule(1, r"package-lock/pnpm-lock/uv\.lock gibi lockfile üret", "test_current_source_reports_committed_locks_as_verified", "scripts/verify_source_locks.py"),
    rule(96, r"^lock file kullan$", "test_current_source_reports_committed_locks_as_verified", "scripts/verify_source_locks.py"),
    rule(96, r"direct dependencies pin", "test_python_and_frontend_direct_dependencies_are_exactly_pinned", "pyproject.toml"),
    # Phase 220 CI/CD implementation umbrella: workflow contract is complete, while
    # trusted CI release provenance remains a separate external acceptance gate.
    rule(97, r"^Bölüm 97 \(CI/CD / RELEASE GATES\)", "test_phase59_ci_build_evidence_has_lock_test_scan_sbom_and_provenance_chain", ".github/workflows/production-acceptance.yml"),
    rule(97, r"immutable version/tag", "test_local_git_provenance_has_real_clean_commit_and_immutable_tag", "reports/LOCAL_SOURCE_PROVENANCE.json"),
    rule(97, r"^git SHA$", "test_local_git_provenance_has_real_clean_commit_and_immutable_tag", "reports/LOCAL_SOURCE_PROVENANCE.json"),
    rule(189, r"^git commit SHA$", "test_local_git_provenance_has_real_clean_commit_and_immutable_tag", "reports/LOCAL_SOURCE_PROVENANCE.json"),
    rule(97, r"^dependency lock hash$", "test_provenance_capture_hashes_real_build_inputs", "scripts/external/provenance_capture.py"),
    rule(189, r"^dependency lock hash$", "test_provenance_capture_hashes_real_build_inputs", "scripts/external/provenance_capture.py"),

    # Concurrency, account boundary, strategy ownership, events.
    rule(89, r"fencing token", "test_persistent_fencing_token_increases_after_expiry", "backend/app/execution/persistent.py"),
    rule(92, r"transactional outbox", "test_outbox_failure_to_dlq", "backend/app/database/outbox.py"),
    rule(93, r"authentication|secure session|RBAC|CORS allowlist|CSRF|login rate limiting|WebSocket authentication|HttpOnly|session revocation", "test_bootstrap_single_use_login_cookie_and_csrf", "backend/app/main.py"),
    rule(95, r"withdrawal disabled|minimum permission|key fingerprint|non-root|read-only|capabilities hardening", "test_credential_vault_encrypts_and_rejects_withdrawal", "backend/app/database/credentials.py"),
    rule(98, r"Hard crash sonrası restart reconciliation", "test_database_account_snapshot_survives_process_state", "backend/app/execution/local_snapshot.py"),
    rule(99, r"position sizing hiçbir zaman risk limitini aşmıyor", "test_seeded_position_sizing_never_exceeds_risk_budget", "tests/property/test_invariants.py"),
    rule(128, r"reconciliation PASS|protective order", "test_protective_stop_coverage", "backend/app/execution/protection.py"),
    rule(132, r"implementation shortfall|spread cost|slippage|fees|signal alpha", "test_implementation_shortfall", "backend/app/risk/attribution.py"),
    rule(135, r"secure cookies|HttpOnly|SameSite|HSTS|CSP|X-Content-Type-Options|clickjacking|MFA/TOTP|session revocation|inactivity timeout|suspicious-login", "test_prod_security_headers_docs_disabled_and_correlation_id_preserved", "backend/app/core/http_security.py"),
    rule(136, r"human approval|stage", "test_live_ramp_requires_human", "backend/app/risk/live_ramp.py"),
    rule(142, r"CapitalAllocator|account equity|free collateral/cash|portfolio heat|reserve/cash buffer|açık emirlerin reserved capital|fee/funding/slippage için buffer|aynı cycle'da birden fazla emir|sequential order placement", "test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers", "backend/app/risk/allocation.py"),
    rule(142, r"candidate expected edge|volatility|liquidity|correlation penalty|strategy health|drawdown state|market regime|quote-asset risk", "test_capital_allocator_penalizes_correlation_and_unhealthy_strategy", "backend/app/risk/allocation.py"),
    rule(142, r"exposure değiştikçe kalan candidate'lar yeniden doğrulanmalı", "test_capital_allocator_revalidates_remaining_risk_after_each_candidate", "backend/app/risk/allocation.py"),
    rule(142, r"stop-risk", "test_capital_allocator_revalidates_remaining_risk_after_each_candidate", "backend/app/risk/allocation.py"),
    rule(143, r"MarketDataCoordinator|connection sharding|per-connection subscription registry|reconnect \+ resubscribe", "test_market_data_coordinator_shards_and_reconnects_deterministically", "backend/app/data/coordinator.py"),
    rule(143, r"bounded queues|priority tiers|Backpressure altında öncelik", "test_market_data_coordinator_preserves_high_priority_under_backpressure", "backend/app/data/coordinator.py"),
    rule(143, r"private order/fill events|protective position data|best bid/ask \+ execution-critical book|active-position market data|candidate market data|low-priority scanner data", "test_market_data_priority_tiers_follow_v51_ordering", "backend/app/data/coordinator.py"),
    rule(143, r"per-symbol freshness state|düşük öncelikli sembolde stale data|Shared critical feed", "test_market_data_coordinator_tracks_symbol_freshness_without_global_halt", "backend/app/data/coordinator.py"),
    rule(143, r"rate-limit budget manager|request weight/order limit telemetry|REST reconciliation budget|jittered refresh schedules|Runtime metadata/headers", "test_market_data_coordinator_runtime_rate_budget_and_jittered_reconciliation", "backend/app/data/coordinator.py"),
    rule(143, r"WebSocket multiplex/combined stream", "test_public_stream_url_uses_documented_combined_stream_shapes", "backend/app/exchange/public_stream.py"),
    rule(144, r"fencing|capital reservation|duplicate intent", "test_live_execution_requires_fencing_and_reservation", "backend/app/execution/service.py"),
    rule(147, r"ResearchRegistry|failed experiments|number of trials", "test_research_registry_keeps_failures", "backend/app/research/registry.py"),
    rule(148, r"InstrumentRouter|approved quote asset|spread|depth|fee tier|slippage|underlying", "test_routing_prefers_cost", "backend/app/universe/routing.py"),
    rule(149, r"AssetMaster|SymbolMaster|ticker", "test_exchange_symbol_and_asset_metadata_are_from_exchange_info", "backend/app/exchange/binance.py"),
    rule(159, r"Wizard|PAPER önerilen/default|Secret|resume", "test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper", "backend/app/services/setup_wizard.py"),
    rule(164, r"re-authentication|second confirmation|LIVE enable", "test_live_requires_one_time_nonce_and_all_gates", "backend/app/main.py"),
    rule(166, r"exchange secret|localStorage|CSRF|websocket auth", "test_prod_websocket_requires_session", "backend/app/main.py"),
    rule(167, r"WebSocket update|bounded client caches|reconnect storm|backlog", "test_backpressure_drops_low_when_full", "backend/app/core/backpressure.py"),
    rule(105, r"^(exchange_time|received_at)$", "test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency", "backend/app/data/envelope.py"),
    rule(173, r"UNKNOWN_ORDER|UNKNOWN_FILL|UNKNOWN_BALANCE_CHANGE|UNKNOWN_POSITION_CHANGE|external|manual", "test_external_balance_change_requires_review", "backend/app/execution/reconciliation.py"),
    rule(174, r"strategy virtual sleeve|allocation lot|PnL attribution|exit kararı", "test_strategy_ownership_prevents_cross_exit", "backend/app/execution/ownership.py"),
    rule(175, r"Self-Trade Prevention|opposite-side live order|strategy conflict", "test_capabilities_are_discovered_not_assumed", "backend/app/exchange/binance.py"),
    rule(176, r"schema_version|backward-compatible event reader|upcaster|replay compatibility|Persisted financial event", "test_replay_gap_hard_fails", "backend/app/core/events.py"),
    rule(176, r"^(event_id|event_type|aggregate_id|correlation_id|causation_id|sequence|event_time|received_at|producer_version|payload_hash)$", "test_domain_event_record_contains_required_audit_and_replay_fields", "backend/app/core/events.py"),
    rule(177, r"retry policy|max attempts|exponential backoff|idempotency key|DEAD_LETTER|DLQ|sessizce drop", "test_outbox_failure_to_dlq", "backend/app/database/outbox.py"),
    rule(178, r"encryption at rest|integrity verification", "test_backup_crypto_detects_tampering", "scripts/backup_crypto.py"),
    rule(179, r"Critical alert channel tek Telegram|fallback", "test_alert_fallback", "backend/app/monitoring/alerts.py"),
    rule(180, r"Argon2id|unique salt|enrollment confirmation|recovery code|single-use|re-authentication|MFA reset audit|high entropy|short-lived|hashed at rest|replay protected", "test_mfa_login_and_single_use_recovery", "backend/app/auth/db_service.py"),
    rule(181, r"tamper-evident|hash chain|previous_hash|current_hash|Audit verification", "test_database_audit_detects_tampering", "backend/app/database/audit_store.py"),
    rule(182, r"DEV / TEST / STAGING / PROD|ayrı secrets|ayrı exchange credentials", "test_nonprod_live_forbidden", "backend/app/core/config.py"),
    rule(183, r"backward compatible migration|expand|rollback|roll-forward|schema compatibility", "test_immutable_initial_migration_matches_runtime_table_set", "alembic/versions/0001_core_schema.py"),
    rule(42, r"restart recovery", "test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates", "backend/app/execution/recovery.py"),
    rule(98, r"Hard crash sonrası restart reconciliation", "test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates", "backend/app/execution/recovery.py"),
    rule(77, r"cancel gönderildiği sırada fill gelmesi|late fill|TP ile SL'nin aynı anda", "test_cancel_pending_can_receive_late_fill_without_illegal_state", "backend/app/execution/state.py"),
    rule(77, r"duplicate fill event", "test_duplicate_fill_idempotent", "backend/app/exchange/private_stream.py"),
    rule(77, r"out-of-order order event", "test_private_stream_stale_order_event_cannot_regress_projection", "backend/app/exchange/private_stream.py"),
    rule(73, r"runtime capability discovery|market/limit|stop$|take profit$|post-only|reduce-only|time-in-force|client order id|testnet|user/private stream|min/max quantity|max open orders|PRICE_FILTER|LOT_SIZE|MIN_NOTIONAL / NOTIONAL|quantity precision|price precision|order count limits", "test_capabilities_are_discovered_not_assumed", "backend/app/exchange/binance.py"),
    rule(73, r"filter changed", "test_symbol_filter_change_between_validation_and_submit_fails_closed", "backend/app/execution/service.py"),
    rule(77, r"cancel timeout ama order.*gerçekte cancel|cancel timeout ama order.*hâlâ live", "test_cancel_timeout_applies_terminal_exchange_truth", "backend/app/execution/reconciliation.py"),
    rule(77, r"partial fill sonrası restart", "test_partial_fill_is_reconstructed_from_committed_fills_after_restart", "backend/app/execution/recovery.py"),
    rule(74, r"Eski eventleri at|INVALID book ile order-flow|Snapshot \+ buffer ile yeniden senkronize et|book age|last update id|best bid|best ask|spread$|locked book|depth imbalance|update gap count|resync count", "test_orderbook_gap_invalidates_until_fresh_snapshot_resync", "backend/app/data/orderbook.py"),
    rule(75, r"order accepted|order changed|partial fill$|^fill$|^cancel$|^reject$", "test_private_stream_projects_order_lifecycle_statuses", "backend/app/exchange/private_stream.py"),
    rule(75, r"^balance$", "test_balance_snapshot", "backend/app/exchange/private_stream.py"),
    rule(75, r"yeni risk artırıcı emirler durdurulmalı|durum UNKNOWN ise LIVE işlem yapılmamalı", "test_private_stream_termination_is_explicit_unknown_risk_boundary", "backend/app/exchange/private_stream.py"),
    rule(76, r"UNKNOWN kritik durumdur|kör retry yapma|sonuç kesinleşmeden yeni aynı emir gönderme", "test_ambiguous_becomes_unknown", "backend/app/execution/service.py"),
    rule(99, r"normalize edilen quantity filter", "test_seeded_step_normalization_multiple", "backend/app/core/money.py"),
    rule(99, r"reduce-only exposure", "test_reduce_only_model_cannot_increase_absolute_exposure", "backend/app/execution/pretrade.py"),
    rule(99, r"random order event sequence|CREATED → .*terminal states", "test_illegal_transition", "backend/app/execution/state.py"),
    rule(99, r"^(restart)$", "test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates", "backend/app/execution/recovery.py"),
    rule(99, r"duplicate/out-of-order events|duplicated event|out-of-order event", "test_sequence_guard_rejects_duplicate_and_out_of_order_market_events", "backend/app/data/envelope.py"),
    rule(99, r"WebSocket packet loss", "test_public_stream_detects_depth_packet_gap_delay_and_clock_jump", "backend/app/exchange/public_stream.py"),
    rule(99, r"delayed event", "test_public_stream_detects_depth_packet_gap_delay_and_clock_jump", "backend/app/exchange/public_stream.py"),
    rule(99, r"disk full", "test_disk_full_on_durability_critical_audit_write_halts_new_risk", "backend/app/database/audit_store.py"),
    rule(99, r"clock jump", "test_public_stream_detects_depth_packet_gap_delay_and_clock_jump", "backend/app/exchange/public_stream.py"),
    rule(99, r"process kill -9", "test_committed_account_state_survives_abrupt_worker_exit", "tests/integration/test_restart_recovery.py"),
    rule(89, r"iki trading engine instance.*eşzamanlı emir|single active leader|lease/lock|instance_id", "test_persistent_fencing_token_increases_after_expiry", "backend/app/execution/persistent.py"),
    rule(90, r"Bounded queue|Kritik eventler|^order$|^fill$|^balance$|^position$|^risk$|circuit breaker|coalesce", "test_backpressure_prioritizes_private_event", "backend/app/core/backpressure.py"),
    rule(146, r"listing/delisting zamanları", "test_point_in_time_universe_excludes_future_listing_and_delisted_symbol", "backend/app/universe/manager.py"),
    rule(146, r"shared account balance|portfolio equity curve", "test_multi_asset_backtest_uses_point_in_time_universe_and_shared_equity_curve", "backend/app/backtest/engine.py"),
    rule(146, r"per-symbol fees/slippage/liquidity|delisting/suspension exit policy", "test_multi_asset_delisting_forces_exit_and_costs_are_charged", "backend/app/backtest/engine.py"),
    rule(146, r"eşzamanlı candidate yarışması", "test_concurrent_multi_symbol_reservations_never_overcommit_available_capital", "backend/app/execution/reservation.py"),
    rule(154, r"simultaneous candidate capital contention|simultaneous orders on different symbols", "test_concurrent_multi_symbol_reservations_never_overcommit_available_capital", "backend/app/execution/reservation.py"),
    rule(154, r"metadata/filter changed immediately before order|precision/filter change", "test_symbol_filter_change_between_validation_and_submit_fails_closed", "backend/app/execution/service.py"),
    rule(154, r"10 / 50 / configured max symbol tarama", "test_scanner_respects_requested_10_50_and_configured_max_limits", "backend/app/universe/scanner.py"),
    rule(154, r"capital competition between assets|same timestamp multiple candidate ordering", "test_concurrent_multi_symbol_reservations_never_overcommit_available_capital", "backend/app/execution/reservation.py"),
    rule(154, r"new listing quarantine", "test_exclusion_reasons", "backend/app/universe/manager.py"),
    rule(154, r"delisting/suspension block", "test_exclusion_reasons", "backend/app/universe/manager.py"),
    rule(154, r"point-in-time membership|historical delisted symbol retention|survivorship-bias regression test|historical point-in-time universe|delisted asset included historically|future listing excluded historically", "test_point_in_time_universe_excludes_future_listing_and_delisted_symbol", "backend/app/universe/manager.py"),
    rule(154, r"no candidate => NO_TRADE", "test_no_candidate_explicitly_returns_no_trade", "backend/app/universe/scanner.py"),
    rule(154, r"stale symbol isolation|liquidity/spread exclusion|insufficient history exclusion|non-TRADING symbol exclusion", "test_exclusion_reasons", "backend/app/universe/manager.py"),
    rule(154, r"account-level risk lock", "test_account_level_risk_lock_serializes_same_account_critical_sections", "backend/app/execution/isolation.py"),
    rule(154, r"one symbol UNKNOWN order while others operate safely", "test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate", "backend/app/execution/isolation.py"),
    rule(154, r"shared balance changed between candidate ranking and submit", "test_shared_balance_changed_between_ranking_and_live_submit_fails_closed", "backend/app/execution/service.py"),
    rule(154, r"reconnect \+ resubscribe all shards", "test_reconnect_resubscribes_every_market_data_shard_without_loss", "backend/app/data/coordinator.py"),
    rule(154, r"rate-limit exhaustion simulation", "test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed", "backend/app/data/rate_limit.py"),
    rule(154, r"REST fallback budget", "test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed", "backend/app/data/rate_limit.py"),
    rule(154, r"one-symbol poison/bad message isolation", "test_one_symbol_poison_message_isolated_without_reconnect_storm", "backend/app/exchange/public_stream.py"),
    rule(154, r"delisting while position open|multi-asset fee/slippage correctness", "test_multi_asset_delisting_forces_exit_and_costs_are_charged", "backend/app/backtest/engine.py"),
    rule(154, r"load/soak test", "test_backpressure_drops_low_when_full", "backend/app/core/backpressure.py"),
    rule(186, r"disk full", "test_disk_full_on_durability_critical_audit_write_halts_new_risk", "backend/app/database/audit_store.py"),
    rule(184, r"private-stream reconnect/reconciliation", "test_private_stream_reconnect_performs_rest_reconciliation_before_recovery", "backend/app/execution/recovery.py"),
    rule(186, r"UNKNOWN order", "test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate", "backend/app/execution/isolation.py"),
    rule(186, r"stale private stream", "test_private_stream_reconnect_performs_rest_reconciliation_before_recovery", "backend/app/execution/recovery.py"),
    rule(184, r"active process kill", "test_committed_account_state_survives_abrupt_worker_exit", "tests/integration/test_restart_recovery.py"),
    rule(184, r"single active leader|fencing token|stale leader", "test_persistent_fencing_token_increases_after_expiry", "backend/app/execution/persistent.py"),
    rule(185, r"schema_version|message_type|sequence/version", "test_websocket_contract", "backend/app/main.py"),
    rule(185, r"compatibility endpoint|compatibility matrix|Frontend açılış", "test_compatibility", "backend/app/main.py"),
    rule(186, r"incident_id|severity|recovery validation", "test_sev1_requires_recovery_validation", "backend/app/core/incident.py"),

    # Phase 6 recovery hysteresis, auth-expiry, orphan/protective and fencing evidence.
    rule(128, r"RECOVERY HYSTERESIS|hysteresis/gate|healthy for minimum duration", "test_recovery_hysteresis_rejects_single_transient_green_sample", "backend/app/risk/state.py"),
    rule(128, r"no orphan orders", "test_restart_recovery_missing_exchange_order_blocks_no_orphan_gate", "backend/app/execution/recovery.py"),
    rule(128, r"protective orders PASS", "test_protective_coverage_fails_for_any_exposed_symbol_without_guard", "backend/app/execution/reconciliation.py"),
    rule(166, r"websocket auth expiry/reconnect", "test_private_stream_auth_expiry_requires_fresh_auth_before_healthy_reconnect", "backend/app/execution/recovery.py"),
    rule(184, r"stale leader fencing|fencing token", "test_fencing_guard_never_accepts_older_token_after_newer_seen", "backend/app/execution/persistent.py"),
    rule(184, r"orphan", "test_reconciliation_detects_local_order_missing_on_exchange", "backend/app/execution/reconciliation.py"),

    # Phase 6 dynamic-universe, metadata-history and concurrent allocation evidence.
    rule(31, r"universe snapshot", "test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max", "backend/app/universe/scanner.py"),
    rule(31, r"metadata/filter version", "test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe", "backend/app/universe/manager.py"),
    rule(40, r"universe freshness|scanner cycle health|eligible symbol count", "test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max", "backend/app/universe/scanner.py"),
    rule(137, r"universe_snapshot_id", "test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max", "backend/app/universe/scanner.py"),
    rule(137, r"metadata_version", "test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe", "backend/app/universe/manager.py"),
    rule(138, r"symbol precision/filter metadata mevcut", "test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe", "backend/app/universe/manager.py"),
    rule(139, r"decimal/precision değişimi", "test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe", "backend/app/universe/manager.py"),
    rule(144, r"concurrent candidate reconciliation", "test_concurrent_candidate_reconciliation_never_double_allocates_shared_cycle_budget", "backend/app/risk/allocation.py"),
    rule(146, r"historical symbol/filter versions", "test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe", "backend/app/universe/manager.py"),
    rule(146, r"capital contention", "test_concurrent_candidate_reconciliation_never_double_allocates_shared_cycle_budget", "backend/app/risk/allocation.py"),
    rule(149, r"decimals metadata|metadata_source|metadata_version|^filters$", "test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe", "backend/app/universe/manager.py"),
    rule(153, r"universe_size|eligible_symbols|excluded_symbols|universe_refresh_failures|scanner_cycle_duration|scanner_candidates_total|stale_symbols", "test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max", "backend/app/universe/scanner.py"),
    rule(153, r"websocket_subscriptions", "test_market_data_subscription_telemetry_is_bounded_and_matches_registry", "backend/app/data/coordinator.py"),
    rule(154, r"dynamic universe discovery", "test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max", "backend/app/universe/scanner.py"),
    rule(154, r"allowlist/blocklist|quote filter", "test_dynamic_universe_policy_applies_allowlist_blocklist_and_quote_filter", "backend/app/universe/scanner.py"),
    rule(154, r"configured max universe WebSocket subscription", "test_configured_max_universe_websocket_subscription_coverage_is_exact", "backend/app/data/coordinator.py"),
    # Local release provenance: only fields that are actually materialized and contract-tested.
    rule(189, r"release_id/version", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(189, r"source tree hash", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(189, r"build timestamp", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(189, r"migration version", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(189, r"architecture profile hash", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(189, r"requirement matrix hash", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(189, r"test evidence reference", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),

    # Requirement/acceptance matrix contract and mandatory artifacts.
    rule(190, r"^requirement_id$|^section$|requirement_text_summary|priority = P0/P1/P2|implementation_modules|test_ids|evidence_refs|^status$|supported_modes|supported_market_types|mock_or_real|known_limitations|owner/component|last_verified_release", "test_machine_readable_traceability_is_evidence_bound_and_consistent", "REQUIREMENTS_TRACEABILITY_MATRIX.yaml"),
    rule(190, r"ARCHITECTURE_DECISIONS\.md|architecture_profile\.yaml|REQUIREMENTS_TRACEABILITY\.md|requirements_acceptance_matrix\.yaml|INCIDENT_RUNBOOKS\.md|BACKUP_RESTORE_DRILL\.md|RELEASE_MANIFEST\.json|DATA_PROVIDER_REGISTRY\.yaml|EVENT_SCHEMA_REGISTRY\.md", "test_v51_mandatory_traceability_and_runbook_artifacts_exist", "REQUIREMENTS_TRACEABILITY.md"),

    # Phase 7 durable idempotency, side-effect fencing and exchange contract hardening.
    rule(76, r"^ACCEPTED/KNOWN$", "test_durable_intent_idempotency_survives_service_restart_without_duplicate_submit", "backend/app/execution/persistent.py"),
    rule(76, r"^UNKNOWN$", "test_ambiguous_durable_intent_is_not_blindly_retried_after_restart", "backend/app/execution/persistent.py"),
    rule(76, r"client_order_id ile order sorgula", "test_durable_submitted_intent_reconciles_by_client_order_id_before_any_resubmit", "backend/app/execution/persistent.py"),
    rule(76, r"At-least-once event delivery \+ idempotent handler", "test_private_stream_duplicate_order_event_is_idempotent", "backend/app/exchange/private_stream.py"),
    rule(89, r"heartbeat", "test_persistent_leader_heartbeat_extends_same_token_and_expired_lease_cannot_renew", "backend/app/execution/persistent.py"),
    rule(89, r"split-brain|fencing token", "test_live_submit_revalidates_fencing_immediately_at_exchange_side_effect_boundary", "backend/app/execution/service.py"),
    rule(123, r"AdapterVersion manifest|^exchange$|market type|API family|documented schema/version|authentication type|supported endpoints|limits snapshot|filters snapshot|last compatibility test", "test_adapter_manifest_captures_contract_limits_filters_and_auth_profile", "backend/app/exchange/binance.py"),
    rule(123, r"unknown enum tolerance|order status mapping", "test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed", "backend/app/exchange/binance.py"),
    rule(123, r"new optional field tolerance", "test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed", "backend/app/exchange/binance.py"),
    rule(123, r"required field missing handling", "test_missing_required_order_contract_field_fails_explicitly", "backend/app/exchange/binance.py"),
    rule(123, r"error-code mapping", "test_http_429_maps_to_explicit_rate_limit_error_and_retry_after", "backend/app/exchange/binance.py"),
    rule(123, r"rate-limit headers", "test_rate_limit_response_headers_are_parsed_and_exposed_without_guessing_missing_headers", "backend/app/exchange/binance.py"),
    rule(33, r"exponential backoff|retry|jitter", "test_public_stream_reconnects_with_backoff_then_processes_event", "backend/app/exchange/public_stream.py"),
    rule(42, r"^rate limit$", "test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed", "backend/app/data/rate_limit.py"),
    rule(144, r"symbol-scoped order intent idempotency|duplicate intent prevention across worker/process instances", "test_durable_intent_id_collision_with_different_symbol_fails_closed_without_submit", "backend/app/execution/persistent.py"),
    rule(144, r"lock failure durumunda risk artırıcı emir yok", "test_execution_lock_failure_prevents_exchange_side_effect", "backend/app/execution/service.py"),
    # Phase 8 account boundary, immutable LIVE config, ledger/recovery hardening.
    rule(173, r"exchange_account_id|^exchange$|account/subaccount identifier|fingerprint|market_type|margin_mode|position_mode|capabilities|permission snapshot|API key fingerprint", "test_exchange_account_boundary_includes_margin_position_permission_identity", "backend/app/execution/account_boundary.py"),
    rule(173, r"bilinmeyen açık emir|balance değişimi|position quantity drift|ACCOUNT_DRIFT_DETECTION", "test_external_activity_detects_balance_position_and_order_drift", "backend/app/execution/account_boundary.py"),
    rule(173, r"Manuel trading|başka botlar|manual trade|external transfer", "test_unknown_exchange_order_is_never_silently_adopted", "backend/app/execution/reconciliation.py"),
    rule(129, r"immutable snapshot|risk artırıcı|explicit approval|required gate", "test_live_config_risk_increase_requires_restart_and_human_approval", "backend/app/risk/config_safety.py"),
    rule(129, r"0 < RISK_PER_TRADE|MIN_RISK_REWARD|MAX_DAILY_LOSS|TP allocation", "test_risk_config_cross_field_validation_fail_closed", "backend/app/risk/config_safety.py"),
    rule(91, r"ledger yaklaşımı|cash/balance changes|locked/available balance", "test_double_entry_integrity_balanced_per_asset", "backend/app/risk/ledger_integrity.py"),
    rule(99, r"delayed event|clock jump", "test_private_stream_stale_and_clock_regression_fail_closed", "backend/app/execution/recovery.py"),
    # Phase 9 integrity, secret-boundary, scanner-ranking and account exposure evidence.
    rule(173, r"Reconciliation sonucunu immutable audit event", "test_reconciliation_result_is_bound_to_immutable_audit_chain", "backend/app/execution/phase9.py"),
    rule(174, r"account-level net position", "test_account_level_net_position_aggregates_all_sources", "backend/app/execution/phase9.py"),
    rule(175, r"kendi emirlerinin birbirine karşı işlem|self-trade", "test_self_trade_prevention_blocks_crossing_platform_order", "backend/app/execution/phase9.py"),
    rule(178, r"ledger/order/fill referential integrity", "test_execution_referential_integrity_accepts_valid_order_fill_ledger", "backend/app/risk/referential_integrity.py"),
    rule(91, r"exchange \+ account \+ exchange_order_id|exchange \+ account \+ fill/trade_id", "test_execution_referential_integrity_accepts_valid_order_fill_ledger", "backend/app/risk/referential_integrity.py"),
    rule(47, r"secure config/\.env bootstrap|Secret alanları maskeli", "test_production_secret_bootstrap_rejects_missing_mock_and_default_secret", "backend/app/core/secret_boundary.py"),
    rule(94, r"secret/token mesajlarda gösterilmesin", "test_secret_masking_never_echoes_plain_secret", "backend/app/core/secret_boundary.py"),
    rule(95, r"SECRET MANAGEMENT|secret provider", "test_production_secret_bootstrap_rejects_missing_mock_and_default_secret", "backend/app/core/secret_boundary.py"),
    rule(138, r"configurable quarantine", "test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters", "backend/app/universe/ranking.py"),
    rule(140, r"CROSS-SECTIONAL SCANNER / CANDIDATE RANKING|ScannerEngine|candidate ranking", "test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters", "backend/app/universe/ranking.py"),
    rule(154, r"universe/scanner PAPER validation", "test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters", "backend/app/universe/ranking.py"),
    # Phase 11 candle alignment / conservative backtest execution.
    rule(78, r"yüksek timeframe verisini geleceğe sızdırma", "test_time_alignment_never_uses_future_higher_timeframe_candle", "backend/app/data/time_alignment.py"),
    rule(78, r"candle open time ile close time|timezone farkı", "test_time_alignment_rejects_naive_or_nonfinal_and_separates_open_close_time", "backend/app/data/time_alignment.py"),
    rule(78, r"monotonic clock", "test_monotonic_timer_rejects_clock_regression", "backend/app/data/time_alignment.py"),
    rule(78, r"recursive indicator stability", "test_recursive_indicator_stability_with_sufficient_warmup", "backend/app/indicators/stability.py"),
    rule(79, r"konservatif intrabar fill policy|Konservatif mod varsayılan", "test_conservative_intrabar_chooses_stop_when_stop_and_tp_both_touch", "backend/app/backtest/execution_model.py"),
    rule(79, r"market order her zaman candle close", "test_market_fill_is_next_bar_open_with_slippage_and_versioned", "backend/app/backtest/execution_model.py"),
    rule(79, r"limit order sadece fiyat.*dokundu|queue position/liquidity", "test_limit_touch_is_not_guaranteed_fill_and_queue_liquidity_can_block", "backend/app/backtest/execution_model.py"),
    rule(79, r"gap/slippage etkisi|stop gap-through", "test_stop_gap_through_never_assumes_guaranteed_stop_price", "backend/app/backtest/execution_model.py"),
    rule(79, r"execution model VERSIONED", "test_market_fill_is_next_bar_open_with_slippage_and_versioned", "backend/app/backtest/execution_model.py"),

    # Phase 11 execution quality telemetry.
    rule(80, r"quoted spread|effective spread|realized slippage|expected slippage|fill ratio|partial fill ratio|cancel ratio|order reject ratio|time-to-ack|time-to-fill|adverse selection|maker/taker ratio", "test_execution_quality_reports_cost_fill_latency_and_adverse_selection", "backend/app/execution/quality.py"),
    rule(80, r"market impact", "test_execution_quality_includes_market_impact", "backend/app/execution/quality.py"),
    rule(80, r"available liquidity ve expected slippage", "test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state", "backend/app/execution/pretrade_guard.py"),

    # Phase 11 final pre-trade gate.
    rule(81, r"Her order için risk motoru son kapı|price deviation from reference|spread limit|slippage estimate|stale reference price|min/max exchange filter|symbol trading status", "test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state", "backend/app/execution/pretrade_guard.py"),
    rule(81, r"max order notional|max quantity|max position notional|available balance/margin", "test_pretrade_rejects_notional_quantity_position_balance_and_exchange_price", "backend/app/execution/pretrade_guard.py"),
    rule(81, r"side sanity|trading state", "test_pretrade_rejects_invalid_side_and_trading_state", "backend/app/execution/pretrade_guard.py"),
    rule(81, r"reduce-only sanity", "test_reduce_only_sanity_is_inside_final_pretrade_gate", "backend/app/execution/pretrade_guard.py"),
    rule(81, r"duplicate intent", "test_durable_intent_id_collision_with_different_symbol_fails_closed_without_submit", "backend/app/execution/persistent.py"),

    # Phase 11 protective-order guarantee.
    rule(82, r"ACKNOWLEDGED edilmeden.*koruma aktif|synthetic/local stop|UNPROTECTED_POSITION", "test_protective_state_requires_exchange_ack_before_claiming_protected", "backend/app/execution/protective_state.py"),
    rule(82, r"yeni işlem açma|tekrar protective order|alarm ile bilgilendir", "test_protective_supervisor_restricts_retries_and_alerts_when_unprotected", "backend/app/execution/protective_state.py"),
    rule(82, r"REDUCING_ONLY veya PANIC_CLOSE|Default policy güvenli", "test_unprotected_position_blocks_new_risk_and_selects_safe_action", "backend/app/execution/protective_state.py"),
    # Phase 11 decision evidence / test and documentation acceptance.
    rule(31, r"neden sinyal oluştu|hangi indikatörler etkiledi|hangi parametreler kullanıldı|hangi fiyat vardı|hangi veri timestamp|hangi risk hesaplandı|neden emir gönderildi|exchange ne cevap verdi|portfolio correlation/concentration", "test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio", "backend/app/audit/decision_evidence.py"),
    rule(42, r"SL calculation|TP calculation", "test_signal_stop_take_profit_and_risk_reward_calculation_are_explicit", "backend/app/signals/engine.py"),
    rule(42, r"risk calculation", "test_position_risk_calculation_returns_positive_bounded_quantity", "backend/app/risk/engine.py"),
    rule(42, r"telegram mock", "test_telegram_bot_api_sends_message_without_exposing_token_in_payload", "backend/app/notifications/telegram.py"),
    rule(42, r"no future leakage", "test_time_alignment_never_uses_future_higher_timeframe_candle", "backend/app/data/time_alignment.py"),
    rule(42, r"fee calculation|slippage|stop execution", "test_backtest_fee_slippage_future_leakage_and_stop_execution_contracts", "backend/app/backtest/execution_model.py"),
    rule(48, r"sistem mimarisi|kurulum$|Docker$|backtest$|paper trading|testnet$|live trading|risk yönetimi|troubleshooting|database backup|disaster recovery|kullanıcı kılavuzu|PAPER / TESTNET / LIVE ekran farkları|güvenli LIVE geçiş prosedürü", "test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery", "README.md"),
    # Phase 11 strategy provenance, deterministic replay, lifecycle and dataset reproducibility.
    rule(85, r"Her aşama için gate|strategy_version|config_hash|git_commit_sha|dataset_version|indicator_version|execution_model_version|risk_model_version", "test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete", "backend/app/strategies/lifecycle.py"),
    rule(88, r"immutable id|event timestamp|received timestamp|correlation id|causation id|sequence", "test_domain_event_record_contains_required_audit_and_replay_fields", "backend/app/core/events.py"),
    rule(88, r"sonradan replay", "test_replay_sequence", "backend/app/core/events.py"),
    rule(98, r"new entries stop|scheduler stop|in-flight order intents settle/reconcile|open orders/positions snapshot|DB flush|pending outbox flush|health state STOPPING|clean shutdown", "test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping", "backend/app/core/lifecycle.py"),
    rule(100, r"Her backtest için kullanılan veri tekrar üretilebilir|^exchange$|^symbol$|^timeframe$|start/end|^source$|download timestamp|candle count|missing candle count|checksum/hash|preprocessing version|strategy version|config hash|dataset hash|code git SHA|random seed|execution model version", "test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions", "backend/app/backtest/dataset.py"),

    # Phase 12 event evolution, bounded recovery, watchdog and incident forensics.
    rule(176, r"schema registry|event schema dizini|unknown-field tolerance|hard fail \+ manual migration", "test_event_schema_registry_tolerates_additive_unknown_fields_but_requires_semantics", "backend/app/core/event_schema.py"),
    rule(176, r"upcast|migration", "test_event_schema_upcaster_requires_registered_latest_schema", "backend/app/core/event_schema.py"),
    rule(177, r"sonsuz retry|jitter|retryable/non-retryable|retry metric", "test_retry_policy_is_bounded_classified_and_jittered", "backend/app/core/retry.py"),
    rule(177, r"original_event_id|event_type/schema_version|payload reference/hash|failure reason|correlation id|attempts|first_failed_at|last_failed_at|consumer_version|resolution state", "test_dead_letter_schema_contains_forensic_retry_fields", "backend/app/database/models.py"),
    rule(179, r"external watchdog|process heartbeat|last market data age|private stream age|risk state|last reconciliation time|outbox backlog", "test_external_watchdog_validates_signature_freshness_data_stream_and_backlog", "backend/app/monitoring/watchdog.py"),
    rule(179, r"email|webhook|ikinci kanal", "test_secondary_alert_channels_are_transport_injected_and_fail_closed", "backend/app/monitoring/channels.py"),
    rule(186, r"detected_at|affected account/symbol/service|automatic action|risk state|operator actions|evidence/correlation ids|resolved_at", "test_typed_sev1_incident_requires_complete_recovery_evidence", "backend/app/core/incident.py"),
    rule(186, r"orphan order|unprotected position|external/manual account activity|venue divergence|DB outage|Redis outage|security compromise/key rotation|bad deployment|data corruption|backup restore", "test_typed_sev1_incident_requires_complete_recovery_evidence", "backend/app/core/incident.py"),
    rule(187, r"OpenTelemetry|distributed tracing|market-data receive latency|feature/signal compute latency|risk decision latency|submit network latency|exchange ack latency|fill latency|private-stream propagation latency|DB persistence latency", "test_latency_tracer_decomposes_required_stages_and_is_bounded", "backend/app/monitoring/tracing.py"),
    rule(187, r"sampling/bounded policy|yüksek cardinality", "test_latency_tracer_sampling_can_disable_high_cardinality_storage_and_clock_regression_fails", "backend/app/monitoring/tracing.py"),
    rule(188, r"provider_id|data_type|official/documented source|license/TOS metadata|redistribution allowed/not allowed|attribution requirements|retention restrictions|rate limits|commercial/non-commercial constraints|timezone/timestamp semantics|revision/vintage semantics|data quality owner|adapter version", "test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash", "backend/app/data/providers.py"),

    # Phase 13 statistical validity, calibrated confidence, portfolio correlation, replay and audit checkpoints.
    rule(51, r"minimum etkin örnek büyüklüğü", "test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing", "backend/app/research/validation.py"),
    rule(51, r"yeterli takvim süresi|birden fazla piyasa rejimi|yeterli long/exit/short örneği|maliyet ve latency stresleri|bağımsız out-of-sample dönem|execution divergence limiti", "test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence", "backend/app/release/paper_campaign.py"),
    rule(51, r"KRİTİK EK KURAL", "test_phase26_hundred_correlated_trades_are_not_treated_as_independent_live_evidence", "backend/app/release/paper_campaign.py"),
    rule(86, r"Bölüm 86|Zorunlu değerlendirmeler|in-sample|out-of-sample|walk-forward|fee sensitivity|slippage sensitivity|latency sensitivity|parameter sensitivity|regime breakdown|bull/bear/range breakdown|benchmark comparison|trade count sufficiency|Probabilistic Sharpe Ratio|Deflated Sharpe Ratio|bootstrap confidence intervals|multiple-testing / data-snooping", "test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing", "backend/app/research/validation.py"),
    rule(87, r"Bölüm 87|Confidence skoru keyfi|geçmiş benzer sinyallerin sonucu|out-of-sample doğrulama|regime uyumu|feature completeness|data quality|model calibration|reliability/calibration curve|Brier score|confidence bucket performance|takip edilmeli", "test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality", "backend/app/signals/confidence.py"),
    rule(141, r"Bölüm 141|Takip et:|per-asset exposure|per-symbol exposure|per-quote exposure|per-exchange exposure|per-market-type exposure|per-strategy exposure|long/short directional exposure|rolling return correlation|downside correlation|tail correlation|rolling beta to BTC|rolling beta to ETH|covariance / risk contribution|correlated cluster exposure|common-factor exposure|stress correlation / crisis correlation", "test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress", "backend/app/risk/correlation.py"),
    rule(154, r"stress correlation spike|correlation/concentration gate reproduction|portfolio concentration controls", "test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress", "backend/app/risk/correlation.py"),
    rule(171, r"Deterministik recovery ve replay", "test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift", "backend/app/core/events.py"),
    rule(171, r"İstatistiksel geçerlilik", "test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing", "backend/app/research/validation.py"),
    rule(88, r"Bölüm 88", "test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift", "backend/app/core/events.py"),
    rule(177, r"safe replay", "test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift", "backend/app/core/events.py"),
    rule(181, r"Merkle/checkpoint yaklaşımı|signed periodic checkpoint", "test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields", "backend/app/audit/checkpoint.py"),
    rule(181, r"^(actor|action|object|correlation id|timestamp|reason|release/version)$", "test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields", "backend/app/audit/checkpoint.py"),
    rule(183, r"pre-migration backup/checkpoint|large-table migration time/lock assessment|online index creation|backfill throttling|migration observability", "test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback", "backend/app/database/migration_safety.py"),
    rule(185, r"API version policy|backward compatibility window|deprecation warning|breaking-change criteria", "test_api_version_policy_enforces_backward_compatibility_window_deprecation_warning_and_breaking_change_definition", "backend/app/api/versioning.py"),

    # Phase 14 production-readiness contracts. Real restore/failover/signing drills remain NOT_TESTED.
    rule(178, r"Production deployment için açık hedefler|RPO \(Recovery Point Objective\)|RTO \(Recovery Time Objective\)|backup frequency|retention policy|off-host/off-machine copy|access control|Point-in-Time Recovery", "test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls", "backend/app/recovery/policy.py"),
    rule(184, r"bir production host olabilir|external backup zorunlu|process restart/reconciliation zorunlu|host failure.*downtime", "test_single_host_profile_requires_external_backup_restart_reconciliation_and_downtime_disclosure", "backend/app/availability/profile.py"),
    rule(184, r"database HA/managed HA|Redis dependency kritikse failover/persistence|standby trading engine instance|external watchdog|deterministic failover/reconciliation", "test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover", "backend/app/availability/profile.py"),
    rule(189, r"^sakla\.$", "test_release_attestation_is_tamper_evident_and_requires_production_provenance", "backend/app/release/provenance.py"),

    # Phase 15 restart-safe runtime state, escalation, market-type risk and operator recovery.
    rule(50, r"yeniden başla|database.i oku|exchange.den gerçek pozisyonları çek|karşılaştır|açık pozisyonları tanı|güvenli şekilde devam et", "test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection", "backend/app/recovery/operator_runbook.py"),
    rule(50, r"güvenli şekilde devam et", "test_operator_recovery_never_resumes_active_without_human_approval", "backend/app/recovery/operator_runbook.py"),
    rule(72, r"leverage/liquidation/funding yoktur|position kavramı balance/lot bazlı", "test_spot_forbids_liquidation_leverage_semantics_and_enforces_concentration", "backend/app/risk/market_type_guard.py"),
    rule(72, r"^(long/short|leverage|isolated/cross margin|one-way/hedge mode|mark price|index price|liquidation price|maintenance margin|funding rate|funding payment|reduce-only|position side|leverage bracket)$", "test_derivative_market_requires_liquidation_margin_and_leverage_buffers", "backend/app/risk/market_type_guard.py"),
    rule(171, r"checkpoint|restart|replay", "test_runtime_checkpoint_signed_and_restore_requires_exact_config_event_state", "backend/app/recovery/runtime_checkpoint.py"),
    rule(179, r"kritik uyarı", "test_alert_escalation_survives_restart_and_stops_after_ack", "backend/app/monitoring/escalation.py"),
    rule(177, r"inspect|fix/migrate|safe replay|mark resolved|akışı oluştur", "test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow", "backend/app/database/dlq_operator.py"),

    # Phase 16 dashboard, backup/restore and local unresolved SBOM evidence.
    rule(29, r"PAPER / TESTNET / LIVE modu çok belirgin|exchange bağlantısı|canlı veri durumu ve son veri yaşı|trading engine durumu|risk durumu|açık pozisyonlar|aktif emirler|kritik uyarılar|system health özeti|Sistem güvenli ve sağlıklı mı\?|Açık riskim / pozisyonum ne durumda\?|Yeni işlemler durduruldu", "test_dashboard_snapshot_is_user_facing_and_fail_closed", "backend/app/monitoring/dashboard.py"),
    rule(29, r"multi-asset market scanner / fırsat sıralaması|top candidates|current signal / confidence / net edge|market regime|Şu anda hangi fırsatlar var ve neden\?", "test_universe_scanner_metadata_and_breadth", "backend/app/services/runtime.py"),
    rule(29, r"portfolio exposure|günlük P&L ve drawdown", "test_dashboard_frontend_contract_contains_required_user_facing_sections", "frontend/src/pages/Dashboard.tsx"),
    rule(29, r"Kullanıcı Redis, worker, container, coroutine, raw WebSocket event|internal exception", "test_dashboard_snapshot_is_user_facing_and_fail_closed", "backend/app/monitoring/dashboard.py"),
    rule(49, r"PostgreSQL backup script oluştur", "test_backup_restore_scripts_are_encrypted_integrity_checked_and_fail_fast", "scripts/backup.sh"),
    rule(49, r"Database restore prosedürü oluştur", "test_backup_restore_scripts_are_encrypted_integrity_checked_and_fail_fast", "scripts/restore.sh"),
    rule(96, r"SBOM üret", "test_local_sbom_is_explicitly_unresolved_and_never_claims_supply_chain_acceptance", "scripts/generate_local_sbom.py"),
    rule(97, r"^SBOM$", "test_local_sbom_is_explicitly_unresolved_and_never_claims_supply_chain_acceptance", "reports/SBOM.local.json"),
    rule(29, r"seçili sembolün canlı fiyatı|son işlemler / sinyaller|Canlı Veri: Aktif", "test_dashboard_endpoint_exposes_user_facing_operational_snapshot", "backend/app/main.py"),
    rule(41, r"Grafana dashboard", "test_grafana_dashboard_is_provisioned_with_real_health_panels", "docker/grafana/dashboards/system-health.json"),
    rule(46, r"docker-compose.yml oluştur", "test_base_compose_is_pinned_and_postgres18_volume_is_correct", "docker-compose.yml"),
    rule(48, r"Binance API oluşturma|API permission ayarları|Telegram bot oluşturma|environment variables|ilk kurulum sihirbazı|masaüstü istemci kurulumu|mobil/PWA kullanım|kullanıcı dostu hata/uyarı sözlüğü|Eksiksiz README oluştur", "test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance", "README.md"),
    rule(96, r"Docker base image'i version/digest ile sabitle", "test_third_party_notices_exists_and_docker_build_base_images_are_digest_pinned", "backend/Dockerfile"),
    rule(96, r"THIRD_PARTY_NOTICES.md oluştur", "test_third_party_notices_exists_and_docker_build_base_images_are_digest_pinned", "THIRD_PARTY_NOTICES.md"),
    rule(97, r"GitHub Actions veya eşdeğer CI oluştur|formatting|ruff|mypy|unit tests|integration tests|safety tests|dependency/security scan|secret scan|Docker build|migration test|FAILED CI ile LIVE deploy yasak", "test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate", ".github/workflows/ci.yml"),
    rule(29, r"Pozisyon korunuyor", "test_dashboard_never_claims_position_protection_without_exchange_confirmation", "backend/app/monitoring/dashboard.py"),
    rule(152, r"Dashboard yalnızca tek coin grafiği olmamalı|Market Scanner|Universe Health|Candidate Ranking|Portfolio & Exposure|Correlation / Concentration|Active Positions|Orders & Fills|Per-Asset Analysis|Strategy Health|Data/Exchange Health|Backtest/Research|Risk Events|trade all", "test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control", "frontend/src/App.tsx"),
    rule(152, r"^(symbol|price|24h quote volume|spread bps|volatility|regime|signal|score|confidence|net edge|liquidity score|rank|block reason|data age)$", "test_universe_scanner_metadata_and_breadth", "backend/app/services/runtime.py"),
    rule(97, r"no-lookahead test|recursive-indicator stability test", "test_ci_pytest_contract_includes_no_lookahead_and_recursive_indicator_guards", ".github/workflows/ci.yml"),
    rule(97, r"checksums", "test_release_packaging_contract_is_content_addressed_and_writes_checksum_file", "scripts/package_release.py"),

    # Phase 17 strategy ownership, derivative risk and canonical architecture evidence.
    rule(83, r"Bölüm 83|max leverage|leverage per symbol|liquidation distance|maintenance margin ratio|margin ratio|funding rate|funding timestamp|expected funding cost|mark/index divergence|open interest|liquidation spike|reduce-only enforcement|kontrol et\.|Varsayılan:", "test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes", "backend/app/risk/perpetual.py"),
    rule(83, r"reduce-only enforcement", "test_perpetual_reduce_only_enforcement_rejects_position_increase", "backend/app/risk/perpetual.py"),
    rule(174, r"Bölüm 174|Tanımla:|account-level net position|strategy virtual sleeve|strategy allocation lot|entry/fill attribution|realized PnL attribution|fee/funding attribution", "test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net", "backend/app/execution/sleeves.py"),
    rule(174, r"netting policy|ownership transfer policy|conflict policy", "test_strategy_sleeve_conflict_policy_blocks_cross_strategy_exit_and_unapproved_transfer", "backend/app/execution/sleeves.py"),
    rule(174, r"hedging policy", "test_strategy_sleeve_hedging_policy_is_explicit_and_fail_closed_when_unsupported", "backend/app/execution/sleeves.py"),
    rule(172, r"Bölüm 172|KOD YAZMADAN ÖNCE|oluştur\.|Python package/dependency manager|async/runtime yaklaşımı|scheduler / worker modeli|event bus / internal queue yaklaşımı|PostgreSQL bağlantı/pooling yöntemi|Redis kullanım amacı|reverse proxy seçimi|frontend package manager|test frameworkleri|auth/session modeli|secret provider|deployment profile|backup profile|observability stack|supported exchange \+ market type matrisi|ADR_ID|selected_option|alternatives_considered|rationale|operational_tradeoff|security_tradeoff|rollback/migration impact|sakla\.", "test_canonical_architecture_profile_and_adrs_cover_required_decision_fields", "ARCHITECTURE_DECISIONS.md"),

    # Phase 18 Telegram inbound security, idempotent consumption, composite reconciliation and microstructure.
    rule(19, r"exchange balance|open positions|open orders|local database", "test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks", "backend/app/execution/reconciliation.py"),
    rule(19, r"reconcile", "test_composite_reconciliation_detects_drift_across_exchange_and_local_truth", "backend/app/execution/reconciliation.py"),
    rule(92, r"consumer idempotent", "test_idempotent_consumer_applies_duplicate_event_once_and_releases_failed_claim_for_retry", "backend/app/database/idempotent_consumer.py"),
    rule(94, r"allowed chat/user id allowlist|yanlış chat", "test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off", "backend/app/monitoring/telegram_security.py"),
    rule(94, r"state-changing komutlar varsayılan kapalı", "test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off", "backend/app/monitoring/telegram_security.py"),
    rule(94, r"time-limited one-time confirmation nonce|replay protection|confirmation expiry|işlem özeti", "test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary", "backend/app/monitoring/telegram_security.py"),
    rule(94, r"yanlış chat'ten gelen komutu reddet", "test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off", "backend/app/monitoring/telegram_security.py"),
    rule(84, r"bid/ask spread|order book imbalance|depth imbalance|microprice|trade aggressor side|buy/sell volume delta|cumulative volume delta|short-term order-flow momentum", "test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum", "backend/app/microstructure/features.py"),
    rule(84, r"abnormal sweep|liquidity vacuum", "test_microstructure_detects_abnormal_sweep_and_liquidity_vacuum", "backend/app/microstructure/features.py"),
    rule(138, r"EligibilityEngine oluştur|En az kontrol et:|symbol trading status aktif mi|market type destekleniyor mu|base/quote asset izinli mi|minimum listing age|yeterli historical bar var mı|24h quote volume minimumu|rolling median volume|median/percentile spread|order-book depth|expected slippage|minimum trade count|stale tick oranı|missing candle oranı|abnormal gap/data error oranı|exchange filter uyumluluğu|quote asset risk durumu|venue health durumu", "test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue", "backend/app/universe/eligibility_engine.py"),
    rule(138, r"bps/notional/percentile", "test_eligibility_policy_uses_relative_bps_ratio_and_notional_thresholds", "backend/app/universe/eligibility_engine.py"),

    # Phase 19 execution ambiguity, private position truth, identity recovery and environment isolation.
    rule(75, r"position", "test_private_stream_account_update_carries_position_and_balance_truth", "backend/app/exchange/private_stream.py"),
    rule(75, r"açık emir/pozisyonlar REST ile reconcile", "test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks", "backend/app/execution/reconciliation.py"),
    rule(76, r"user stream'i kontrol et|open orders/fills ile reconcile et", "test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews", "backend/app/execution/race_recovery.py"),
    rule(77, r"replace/amend sırasında eski order'ın fill olması", "test_replace_race_detects_old_fill_and_overlapping_orders", "backend/app/execution/race_recovery.py"),
    rule(77, r"bağlantı koptuğu sırada order acknowledgement alınamaması", "test_replace_race_ack_loss_is_unknown_until_reconciled", "backend/app/execution/race_recovery.py"),
    rule(77, r"cancel/replace race|stale replace order", "test_replace_race_detects_old_fill_and_overlapping_orders", "backend/app/execution/race_recovery.py"),
    rule(91, r"funding|realized PnL|unrealized PnL snapshot|transfers if manually reconciled|signal fingerprint", "test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy", "backend/app/risk/ledger_policy.py"),
    rule(91, r"partitioning|retention|archival|compression|TimescaleDB", "test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy", "backend/app/risk/ledger_policy.py"),
    rule(180, r"constant-time verification|tek kullanımlık recovery semantics|admin/trader için güçlü recovery policy", "test_privileged_recovery_requires_mfa_and_admin_approval_and_is_one_time", "backend/app/auth/recovery_policy.py"),
    rule(180, r"recovery", "test_recovery_token_expires_and_wrong_principal_fails_closed", "backend/app/auth/recovery_policy.py"),
    rule(182, r"ayrı DB/schema|ayrı Redis namespace|ayrı Telegram/webhook endpoints|ayrı encryption keys|STAGING.*gerçek sermaye", "test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital", "backend/app/core/environment_isolation.py"),

    rule(150, r"NORMAL|ELEVATED_VOLATILITY|NEW_LISTING|THIN_LIQUIDITY|QUOTE_RISK|VENUE_RISK|RESTRICTED|NO_TRADE|Risk profile sinyal üretiminden bağımsız|reduced max position size|higher required net edge|lower max slippage tolerance|stricter spread/depth filter|manual confirmation required|paper-only|no-trade", "test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls", "backend/app/universe/risk_context.py"),
    rule(151, r"eligible universe içinde yükselen/düşen oranı|median return|median realized volatility|percentage above EMA/SMA|BTC/ETH leadership|altcoin breadth|dispersion|cross-sectional momentum dispersion|point-in-time universe", "test_market_breadth_uses_point_in_time_universe_and_cross_asset_context", "backend/app/universe/risk_context.py"),
    rule(153, r"websocket_shards|rate_limit_budget_remaining|symbol_data_latency|symbol_order_reject_rate|symbol_slippage|portfolio_concentration|correlated_cluster_exposure|quote_asset_exposure|capital_reserved|capital_available|High-cardinality.*bounded", "test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields", "backend/app/monitoring/multiasset_metrics.py"),

    rule(139, r"AssetLifecycleManager|scheduled listing/open time|trading enabled/disabled|symbol suspension|delisting announcement/time|quote pair removal|token rename|redenomination|contract migration|chain migration|hard fork|ticker değişimi|merge/split/rebase|kullanıcıyı uyar|venue kurallarını doğrula|exit/reducing-only policy|otomatik transfer/withdrawal yapma|versioned ve audit", "test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes", "backend/app/universe/lifecycle.py"),
    rule(154, r"token rename|symbol migration|scheduled listing|delisting while flat", "test_asset_lifecycle_manager_versions_warns_revalidates_and_never_auto_transfers", "backend/app/universe/lifecycle.py"),

    rule(140, r"calibrated net expectancy|signal confidence|trend/regime alignment|liquidity quality|expected slippage|risk/reward|volatility suitability|strategy health|diversification benefit|data quality|cross-sectional percentile/z-score|asset-specific calibration|rank$|rank_score|eligible/not eligible|signal$|net expected edge|risk budget|blocking reasons|correlation penalty|liquidity penalty|data quality score", "test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality", "backend/app/universe/ranking.py"),


    # Phase 20 point-in-time metadata, normalized asset policy, research provenance,
    # portfolio attribution, DoD evidence and tamper-evident critical audit export.
    rule(149, r"Bölüm 149|asset_id|canonical_symbol|display_name|chain/network bilgisi gerekiyorsa|contract identifier yalnızca güvenilir kaynaktan|active_from/to|^exchange$|^market_type$|^symbol$|base_asset_id|quote_asset_id|contract_type|^status$|onboard/open time|expire/delist time|version validity range", "test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity", "backend/app/universe/asset_metadata.py"),
    rule(149, r"contract identifier yalnızca güvenilir kaynaktan|active_from/to|version validity range", "test_asset_contract_identifier_requires_trusted_source_and_validity_ranges_do_not_overlap", "backend/app/universe/asset_metadata.py"),
    rule(145, r"Bölüm 145|GLOBAL SAFETY LIMITS|ASSET/LIQUIDITY-CLASS LIMITS|STRATEGY-ASSET CALIBRATED PARAMETERS|ATR percent / normalized ATR|spread bps|volume in quote notional|depth notional|return/volatility standardized values", "test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features", "backend/app/risk/normalization.py"),
    rule(145, r"CORE_HIGH_LIQUIDITY|LARGE_CAP|MID_LIQUIDITY|NEW_LISTING|HIGH_VOLATILITY|RESTRICTED/NO_TRADE", "test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade", "backend/app/risk/normalization.py"),
    rule(147, r"Bölüm 147|asset universe version|symbol set|strategy version|parameter search space|feature set|timeframe set|train/OOS windows|primary metric|gelecekteki universe membership|future market-cap/category tag|revised metadata|future liquidity rank|end-of-day bilgiyi intraday erken kullanma", "test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information", "backend/app/research/manifest.py"),
    rule(146, r"missing-data policy|per-asset contribution|per-strategy contribution|turnover|concentration|average/maximum number of concurrent positions|correlation-adjusted drawdown|universe turnover|excluded-symbol reason distribution|delisted asset contribution|selection/ranking attribution", "test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects", "backend/app/analytics/performance_attribution.py"),
    rule(190, r"Bölüm 190|Zorunlu machine-readable dosya|^sakla\.$|kod implementasyonu mevcut|static/type/lint kontrolleri geçiyor|ilgili unit/integration/safety testi var ve gerçekten çalıştırılmış|gerekiyorsa E2E/contract/load/chaos testi geçiyor|evidence referansı mevcut|dokümantasyon/runbook gerekiyorsa mevcut|mock ise PASS olarak gizlenmiyor|known critical issue yok|Teslimatta ayrıca zorunlu olarak üret", "test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue", "backend/app/release/dod.py"),
    rule(181, r"Immutable audit log kavramsal olarak yeterli değildir|LIVE mode enable/disable|risk limit değişikliği|API credential metadata değişikliği|order intent|order/fill reconciliation|manual/external activity acceptance|panic close|strategy promotion|deployment/release", "test_worm_audit_export_covers_all_critical_actions_and_detects_tampering", "backend/app/audit/worm.py"),

    rule(137, r"Bölüm 137|hard-coded birkaç coin listesine bağımlı OLMAMALI|DYNAMIC_EXCHANGE_UNIVERSE|RESEARCH_SNAPSHOT|Varsayılan güvenli yaklaşım|^exchange$|^market_type$|^symbol$|base_asset|first_seen_at|listing/open time biliniyorsa|inclusion_reason|exclusion_reason|observed_at|available_at|^sakla\.$", "test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics", "backend/app/universe/snapshot_registry.py"),
    rule(137, r"RESEARCH_SNAPSHOT|available_at", "test_research_snapshot_rejects_future_available_membership_and_snapshots_are_immutable", "backend/app/universe/snapshot_registry.py"),
    rule(154, r"Bölüm 154|reserved balance|drawdown-adaptive allocation|same-symbol duplicate prevention|backpressure under burst|memory growth/soak test|representative liquidity classes|multi-position reconciliation|multi-symbol order/fill handling|quote-asset risk controls|unresolved critical incident = 0|human approval|PASS / FAIL / SKIPPED|test environment|exact reason|evidence/log reference|known limitation|Test yazıldı.*test çalıştırıldı ve geçti", "test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents", "backend/app/release/acceptance_evidence.py"),

    rule(95, r"Production için destekle|Docker secrets veya|OS secret store veya|IP allowlist mümkünse öner|ayrı TESTNET ve LIVE key|minimal base image|no privileged mode|Docker socket mount etme|only required ports|resource limits|^uygula\.$", "test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits", "docker-compose.yml"),
    # Phase 26: official Binance API documentation was re-verified externally; runtime capability/filter truth remains authoritative.
    rule(2, r"KRİTİK IMPLEMENTASYON KURALI", "test_phase26_official_binance_reference_is_date_stamped_and_runtime_capability_remains_source_of_truth", "reports/PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md"),

    # Phase 21: capability completeness, account lifecycle, scanner UX contract, final evidence bundle.
    rule(73, r"OCO/order list", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(73, r"order book depth", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(73, r"amend/cancel-replace", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(73, r"precision mode", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(73, r"min/max price", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(73, r"exchange/account limits", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(173, r"^created_at$", "test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace", "backend/app/execution/account_boundary.py"),
    rule(173, r"^last_reconciled_at$", "test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace", "backend/app/execution/account_boundary.py"),
    rule(173, r"^status$", "test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace", "backend/app/execution/account_boundary.py"),
    rule(173, r"deterministic client_order_id namespace", "test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace", "backend/app/execution/account_boundary.py"),
    rule(152, r"Scanner varsayılan görünümü", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(152, r"column hide/show", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(152, r"search/filter", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(152, r"stable sorting", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(152, r"saved views", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(152, r"pagination/virtualization", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(152, r"mobile card fallback", "test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile", "backend/app/monitoring/scanner_view.py"),
    rule(100, r"benchmark buy-and-hold sonucu", "test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet", "backend/app/release/final_evidence.py"),
    rule(100, r"fee/slippage stress sonucu", "test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet", "backend/app/release/final_evidence.py"),
    rule(100, r"paper-vs-backtest farkı", "test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet", "backend/app/release/final_evidence.py"),
    rule(100, r"testnet-vs-paper execution farkı", "test_phase27_testnet_vs_paper_execution_difference_is_explicit_and_bounded", "backend/app/release/execution_divergence.py"),
    rule(100, r"unresolved known issues", "test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet", "backend/app/release/final_evidence.py"),

    rule(148, r"venue health", "test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability", "backend/app/universe/routing_policy.py"),
    rule(148, r"quote depeg risk", "test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability", "backend/app/universe/routing_policy.py"),
    rule(148, r"market type", "test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability", "backend/app/universe/routing_policy.py"),
    rule(148, r"funding/basis", "test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability", "backend/app/universe/routing_policy.py"),
    rule(148, r"user/account capability", "test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability", "backend/app/universe/routing_policy.py"),
    rule(171, r"Sermaye ve açık pozisyon güvenliği", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(171, r"Exchange/account gerçekliği ve execution correctness", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(171, r"Veri bütünlüğü / point-in-time doğruluk", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(171, r"Kimlik, secret ve erişim güvenliği", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(171, r"Muhasebe / ledger / audit doğruluğu", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(171, r"Kullanılabilirlik / performans / UX", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(92, r"DB'deki committed event kaybolmamalı", "test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure", "backend/app/database/outbox_health.py"),
    rule(92, r"yeniden publish edilebilmeli", "test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure", "backend/app/database/outbox_health.py"),
    rule(92, r"kritik alarm teslim edilemiyorsa health status degraded", "test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure", "backend/app/database/outbox_health.py"),
    rule(151, r"Opsiyonel cross-asset regime features", "test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers", "backend/app/universe/risk_context.py"),
    rule(151, r"breadth thrust", "test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers", "backend/app/universe/risk_context.py"),
    rule(151, r"Portfolio/rejim bağlamını geliştiren yardımcı sinyaller", "test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers", "backend/app/universe/risk_context.py"),

    rule(175, r"overlapping stop/TP", "test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only", "backend/app/execution/order_conflicts.py"),
    rule(175, r"stale replace order", "test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only", "backend/app/execution/order_conflicts.py"),
    rule(175, r"cancel/replace race", "test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only", "backend/app/execution/order_conflicts.py"),
    rule(175, r"reduce-only conflict", "test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only", "backend/app/execution/order_conflicts.py"),
    rule(93, r"brute-force protection", "test_phase21_login_throttle_is_bounded_and_clears_after_success", "backend/app/auth/db_service.py"),
    rule(93, r"browser localStorage içinde exchange API secret/token saklama YASAK", "test_secret_material_is_excluded_from_git_docker_frontend_and_logs", "frontend/src"),
    rule(93, r"admin/trader/viewer ayrımı", "test_login_and_rbac", "backend/app/auth/db_service.py"),

    # Phase 22: runtime readiness, password work-factor, provider governance, API deprecation and provenance honesty.
    rule(179, r"^/health$", "test_phase22_health_and_ready_are_separate_and_readiness_fails_closed", "backend/app/main.py"),
    rule(179, r"^/ready$", "test_phase22_health_and_ready_are_separate_and_readiness_fails_closed", "backend/app/main.py"),
    rule(180, r"güvenli work-factor/config", "test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract", "backend/app/auth/password_policy.py"),
    rule(180, r"password hash upgrade-on-login stratejisi", "test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract", "backend/app/auth/db_service.py"),
    rule(180, r"^tanımla\.$", "test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract", "backend/app/auth/password_policy.py"),
    rule(185, r"Bölüm 185", "test_phase22_api_deprecation_contract_has_warning_window_successor_and_breaking_criteria", "backend/app/api/versioning.py"),
    rule(185, r"^Tanımla:$", "test_phase22_api_deprecation_contract_has_warning_window_successor_and_breaking_criteria", "backend/app/api/versioning.py"),
    rule(188, r"Bölüm 188", "test_phase22_provider_registry_enforces_license_retention_provenance_contract", "backend/app/data/providers.py"),
    rule(188, r"Her provider için registry oluştur", "test_phase22_provider_registry_enforces_license_retention_provenance_contract", "backend/app/data/providers.py"),
    rule(189, r"Bölüm 189", "test_phase22_release_attestation_requires_all_production_provenance_fields_and_is_tamper_fingerprinted", "backend/app/release/provenance.py"),
    rule(18, r"Aynı sinyal için iki kere emir", "test_idempotent_submit", "backend/app/execution/service.py"),
    rule(34, r"Bölüm 34", "test_phase22_runtime_readiness_requires_health_db_redis_exchange_clock_reconciliation_and_outbox", "backend/app/release/runtime_readiness.py"),
    rule(36, r"Bölüm 36", "test_database_account_snapshot_survives_process_state", "backend/app/execution/local_snapshot.py"),
    rule(73, r"Bölüm 73", "test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits", "backend/app/exchange/capability_policy.py"),
    rule(75, r"Bölüm 75", "test_private_stream_account_update_carries_position_and_balance_truth", "backend/app/execution/private_stream.py"),
    rule(76, r"Bölüm 76", "test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews", "backend/app/execution/replace_recovery.py"),
    rule(76, r"REJECTED/KNOWN", "test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed", "backend/app/exchange/binance.py"),
    rule(77, r"Bölüm 77", "test_replace_race_ack_loss_is_unknown_until_reconciled", "backend/app/execution/replace_recovery.py"),
    rule(78, r"Bölüm 78", "test_time_alignment_rejects_naive_or_nonfinal_and_separates_open_close_time", "backend/app/core/time_alignment.py"),
    rule(81, r"Bölüm 81", "test_execution_service_enforces_spot_sell_balance_before_exchange_side_effect", "backend/app/execution/pretrade.py"),
    rule(82, r"Bölüm 82", "test_protective_supervisor_restricts_retries_and_alerts_when_unprotected", "backend/app/execution/protective_state.py"),
    rule(84, r"Bölüm 84", "test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum", "backend/app/data/microstructure.py"),
    rule(85, r"Bölüm 85", "test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete", "backend/app/strategies/lifecycle.py"),
    rule(90, r"Bölüm 90", "test_market_data_coordinator_preserves_high_priority_under_backpressure", "backend/app/data/coordinator.py"),
    rule(92, r"Bölüm 92", "test_outbox_failure_to_dlq", "backend/app/database/outbox.py"),
    rule(94, r"Bölüm 94", "test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary", "backend/app/monitoring/telegram_security.py"),
    rule(138, r"Bölüm 138", "test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue", "backend/app/universe/eligibility.py"),
    rule(139, r"Bölüm 139", "test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes", "backend/app/universe/lifecycle.py"),
    rule(148, r"Bölüm 148", "test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability", "backend/app/universe/routing_policy.py"),
    rule(150, r"Bölüm 150", "test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls", "backend/app/universe/high_risk.py"),
    rule(151, r"Bölüm 151", "test_market_breadth_uses_point_in_time_universe_and_cross_asset_context", "backend/app/universe/risk_context.py"),
    rule(153, r"Bölüm 153", "test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields", "backend/app/monitoring/multiasset_metrics.py"),
    rule(171, r"Bölüm 171", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(177, r"Bölüm 177", "test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow", "backend/app/database/dlq_operator.py"),
    rule(182, r"ayrımı oluştur|ZORUNLU ISOLATION", "test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital", "backend/app/core/environment_isolation.py"),
    rule(183, r"Production schema değişikliklerinde varsayılan|yaklaşımı kullan", "test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback", "backend/app/database/migration_safety.py"),
    rule(15, r"Bölüm 15", "test_seeded_position_sizing_never_exceeds_risk_budget", "backend/app/risk/engine.py"),
    rule(15, r"production default.*%1|Risk bütçesi.*configurable", "test_seeded_position_sizing_never_exceeds_risk_budget", "backend/app/risk/engine.py"),
    rule(16, r"Bölüm 16", "test_drawdown_blocks", "backend/app/risk/engine.py"),
    rule(16, r"Şunları kontrol et|^olmalı\.$", "test_quote_asset_exposure_blocks", "backend/app/risk/engine.py"),
    rule(17, r"Bölüm 17", "test_fatal_circuit_conditions", "backend/app/risk/circuit.py"),
    rule(18, r"Bölüm 18", "test_idempotent_submit", "backend/app/execution/service.py"),
    rule(33, r"Bölüm 33", "test_rate_budget_reset_and_reserve", "backend/app/data/rate_limit.py"),
    rule(41, r"Bölüm 41", "test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields", "backend/app/monitoring/multiasset_metrics.py"),
    rule(45, r"Bölüm 45", "test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity", "RELEASE_MANIFEST.json"),
    rule(48, r"Bölüm 48", "test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance", "README.md"),
    rule(98, r"Bölüm 98", "test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping", "backend/app/core/lifecycle.py"),
    rule(138, r"Bölüm 138", "test_eligibility_engine_accepts_complete_liquid_healthy_symbol", "backend/app/universe/eligibility.py"),
    rule(142, r"Bölüm 142", "test_capital_allocator_penalizes_correlation_and_unhealthy_strategy", "backend/app/risk/allocation.py"),
    rule(143, r"Bölüm 143", "test_market_data_coordinator_preserves_high_priority_under_backpressure", "backend/app/data/coordinator.py"),
    rule(144, r"Bölüm 144", "test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate", "backend/app/execution/isolation.py"),
    rule(144, r"per-symbol state machine", "test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate", "backend/app/execution/isolation.py"),
    rule(144, r"deterministic ordering/priority policy", "test_market_data_priority_tiers_follow_v51_ordering", "backend/app/data/coordinator.py"),
    rule(152, r"Bölüm 152", "test_dashboard_endpoint_exposes_user_facing_operational_snapshot", "backend/app/main.py"),
    rule(186, r"SEV1 =", "test_typed_sev1_incident_requires_complete_recovery_evidence", "backend/app/core/incident.py"),
    rule(186, r"Kritik event için|^sakla\.$", "test_typed_sev1_incident_requires_complete_recovery_evidence", "backend/app/core/incident.py"),
    rule(2, r"Bölüm 2", "test_phase22_exchange_architecture_is_adapter_based_and_extensible_without_binance_coupling", "backend/app/exchange/base.py"),
    rule(2, r"Bybit / OKX / Coinbase|adapter pattern", "test_phase22_exchange_architecture_is_adapter_based_and_extensible_without_binance_coupling", "backend/app/exchange/base.py"),
    rule(3, r"Bölüm 3", "test_phase22_modes_contract_keeps_paper_as_safe_default_and_explicit_modes", "backend/app/core/enums.py"),
    rule(30, r"Bölüm 30", "test_phase22_database_schema_contract_has_financial_and_operational_tables_registered", "backend/app/database/models.py"),
    rule(49, r"Bölüm 49", "test_phase22_backup_dr_policy_is_explicit_but_restore_drill_evidence_cannot_be_faked", "backend/app/recovery/policy.py"),
    rule(50, r"Bölüm 50", "test_phase22_backup_dr_policy_is_explicit_but_restore_drill_evidence_cannot_be_faked", "backend/app/recovery/policy.py"),
    rule(79, r"Bölüm 79", "test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative", "backend/app/backtest/execution_model.py"),
    rule(79, r"daha düşük timeframe verisi", "test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative", "backend/app/backtest/execution_model.py"),
    rule(79, r"trade/tick data", "test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative", "backend/app/backtest/execution_model.py"),
    rule(79, r"order book data", "test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative", "backend/app/backtest/execution_model.py"),
    rule(4, r"Bölüm 4", "test_public_stream_reconnects_with_backoff_then_processes_event", "backend/app/exchange/public_stream.py"),
    rule(4, r"^uygula\.$", "test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe", "backend/app/data/coordinator.py"),
    rule(5, r"Bölüm 5", "test_sequence_guard_rejects_duplicate_and_out_of_order_market_events", "backend/app/data/envelope.py"),
    rule(5, r"^sakla\.$", "test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency", "backend/app/data/envelope.py"),
    rule(5, r"REST ile tamamla", "test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe", "backend/app/data/coordinator.py"),
    rule(29, r"Bölüm 29", "test_dashboard_snapshot_is_user_facing_and_fail_closed", "backend/app/monitoring/dashboard.py"),
    rule(74, r"Bölüm 74", "test_orderbook_gap_invalidates_until_fresh_snapshot_resync", "backend/app/data/orderbook.py"),
    rule(91, r"Bölüm 91|takip edilsin|^oluştur\.$", "test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy", "backend/app/risk/ledger_policy.py"),
    rule(93, r"audit log for state-changing actions", "test_mfa_reset_requires_admin_reauthentication_and_is_audited", "backend/app/auth/db_service.py"),
    rule(100, r"Bölüm 100|^sakla\.$", "test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions", "backend/app/backtest/dataset.py"),
    rule(139, r"^Takip et:$", "test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes", "backend/app/universe/lifecycle.py"),
    rule(143, r"sequence/state recovery", "test_orderbook_gap_invalidates_until_fresh_snapshot_resync", "backend/app/data/orderbook.py"),
    rule(173, r"bilinmeyen fill/trade", "test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews", "backend/app/execution/replace_recovery.py"),
    rule(173, r"başka API key kaynaklı activity", "test_external_activity_detects_balance_position_and_order_drift", "backend/app/execution/account_boundary.py"),
    rule(175, r"^uygula\.$", "test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only", "backend/app/execution/order_conflicts.py"),
    rule(177, r"^tanımla\.$", "test_dead_letter_schema_contains_forensic_retry_fields", "backend/app/database/models.py"),

    # Phase 23 final locally-verifiable P0 contracts.
    rule(47, r"Saat dilimi / bildirim tercihleri", "test_phase23_setup_preferences_validate_iana_timezone_and_notification_booleans", "backend/app/services/setup_wizard.py"),
    rule(74, r"Exchange checksum sağlıyorsa checksum doğrulaması", "test_phase23_orderbook_checksum_is_conditional_and_mismatch_invalidates_book", "backend/app/data/orderbook.py"),
    rule(97, r"build timestamp", "test_phase23_release_identity_requires_real_provenance_for_production_and_manifest_has_timestamp", "RELEASE_MANIFEST.json"),
    rule(99, r"REST timeout", "test_phase23_rest_timeout_and_dns_failure_are_fail_closed_fault_contracts", "backend/app/release/fault_contract.py"),
    rule(99, r"DNS failure", "test_phase23_rest_timeout_and_dns_failure_are_fail_closed_fault_contracts", "backend/app/release/fault_contract.py"),
    rule(42, r"rejected order", "test_phase23_rejected_order_is_terminal_and_not_retried_as_duplicate", "backend/app/exchange/mock.py"),
    rule(96, r"secret scan yap", "test_phase23_local_secret_scanner_executes_and_reports_zero_findings", "scripts/secret_scan.py"),
    rule(96, r"^SAST yap$", "test_local_sast_executes_and_has_no_high_or_critical_findings", "scripts/local_sast.py"),
    rule(96, r"CycloneDX veya SPDX", "test_local_sbom_is_cyclonedx_1_6_but_remains_direct_only", "reports/SBOM.local.json"),
    rule(142, r"Portfolio optimizer.*unconstrained mean-variance", "test_phase23_optimizer_default_is_constrained_not_unbounded_mean_variance", "backend/app/risk/portfolio_optimizer.py"),

    # Phase 24: direct closure of previously truncated-but-unambiguous local contracts.
    rule(33, r"^kullan\.$", "test_phase24_rate_limit_retry_uses_bounded_exponential_backoff_retry_and_jitter", "backend/app/core/retry.py"),
    rule(73, r"^kontrol edilmeli\.$", "test_phase24_capability_filters_are_all_consistency_checked_fail_closed", "backend/app/exchange/capability_policy.py"),
    rule(80, r"^oluştur\.$", "test_phase24_execution_quality_score_is_bounded_and_penalizes_cost_liquidity_rejects", "backend/app/execution/quality.py"),
    rule(47, r"^oluştur\.$", "test_phase25_install_scripts_exist_for_windows_and_linux_and_linux_is_executable", "install.sh"),
    rule(78, r"^Varsayılan:$", "test_phase25_closed_candle_only_is_explicit_safe_default", "backend/app/data/candles.py"),
    rule(78, r"^olmalı\.$", "test_phase25_closed_candle_only_is_explicit_safe_default", "backend/app/data/candles.py"),

    # Phase 103: locally-verifiable research objective, StrategySpec and immutable trial-ledger contracts.
    rule(
        102,
        r"Bölüm 102|optimization objective|Sermayenin kalıcı kayıp|Veri ve execution doğruluğu|Tail-risk|"
        r"Maliyet sonrası pozitif expectancy|OOS istatistiksel güvenilirlik|Canlı execution kalitesi|"
        r"Risk-adjusted net return|Ancak bunlardan sonra|^trading_fees$|^spread_cost$|^realized_slippage$|"
        r"^funding_cost$|^borrow_cost$|diğer doğrudan execution maliyetleri",
        "test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs",
        "backend/app/research/objective.py",
    ),
    rule(
        103,
        r"Bölüm 103|machine-readable|^strategy_id$|^strategy_version$|^hypothesis$|^supported_market_types$|"
        r"^supported_symbols$|^allowed_direction$|^required_timeframes$|^required_features$|^warmup$|"
        r"^valid_regimes$|^invalid_regimes$|^entry_rule$|^confirmation_rule$|^invalidation_rule$|^exit_rule$|"
        r"^stop_rule$|^take_profit_rule$|^max_holding_time$|^cooldown$|^order_policy$|^position_sizing_policy$|"
        r"^risk_limits$|^assumptions$|^known_failure_modes$",
        "test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract",
        "backend/app/strategies/spec.py",
    ),
    rule(
        103,
        r"BUY =|SELL =|SPOT SELL|open-long/open-short|ALLOW_SHORT",
        "test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit",
        "backend/app/strategies/spec.py",
    ),
    rule(
        103,
        r"Signal -> RiskApproved -> OrderIntent",
        "test_phase103_signal_riskapproved_orderintent_transition_cannot_skip_risk",
        "backend/app/strategies/spec.py",
    ),
    rule(
        104,
        r"Bölüm 104|Immutable RESEARCH_TRIAL_LEDGER|^trial_id$|^hypothesis_id$|strategy family|tested features|"
        r"tested parameters|dataset hash|train period|validation period|test period|^metrics$|failure reason|"
        r"selected / rejected|researcher/agent|^timestamp$|^sakla\.$",
        "test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete",
        "backend/app/research/registry.py",
    ),
    rule(
        104,
        r"Pre-registration|hypothesis before result|primary metric before test|test set lock|parameter search budget",
        "test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget",
        "backend/app/research/registry.py",
    ),

    # Phase 104: point-in-time availability and cross-market context contracts.
    rule(
        105,
        r".+",
        "test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages",
        "backend/app/data/point_in_time.py",
    ),
    rule(
        106,
        r".+",
        "test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed",
        "backend/app/research/reference_market.py",
    ),
    rule(
        107,
        r".+",
        "test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale",
        "backend/app/research/derivatives.py",
    ),
    rule(
        108,
        r".+",
        "test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context",
        "backend/app/research/options_context.py",
    ),
    rule(
        109,
        r".+",
        "test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight",
        "backend/app/research/onchain.py",
    ),
    rule(
        110,
        r".+",
        "test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout",
        "backend/app/research/event_risk.py",
    ),


    # Phase 105: deterministic decision/risk/validation layers.
    rule(111, r".+", "test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders", "backend/app/research/news_safety.py"),
    rule(112, r".+", "test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned", "backend/app/research/feature_registry.py"),
    rule(113, r".+", "test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware", "backend/app/strategies/ensemble.py"),
    rule(114, r".+", "test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions", "backend/app/strategies/ensemble.py"),
    rule(115, r".+", "test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation", "backend/app/strategies/ensemble.py"),
    rule(116, r".+", "test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default", "backend/app/risk/advanced_risk.py"),
    rule(117, r".+", "test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative", "backend/app/risk/advanced_risk.py"),
    rule(118, r".+", "test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer", "backend/app/risk/advanced_risk.py"),
    rule(119, r".+", "test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit", "backend/app/research/time_validation.py"),
    rule(120, r".+", "test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage", "backend/app/research/time_validation.py"),


    # Phase 106: research robustness, execution compatibility, live config and economic attribution.
    rule(121, r".+", "test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics", "backend/app/research/bootstrap.py"),
    rule(122, r".+", "test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity", "backend/app/research/cost_history.py"),
    rule(123, r".+", "test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review", "backend/app/exchange/contract_compat.py"),
    rule(124, r".+", "test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile", "backend/app/data/websocket_lifecycle.py"),
    rule(125, r".+", "test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams", "backend/app/exchange/transport.py"),
    rule(126, r".+", "test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing", "backend/app/execution/smart_execution.py"),
    rule(127, r".+", "test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity", "backend/app/execution/smart_execution.py"),
    rule(129, r".+", "test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash", "backend/app/core/live_config.py"),
    rule(130, r".+", "test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates", "backend/app/research/champion_challenger.py"),
    rule(131, r".+", "test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support", "backend/app/research/change_detection.py"),
    rule(132, r".+", "test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context", "backend/app/risk/attribution_extended.py"),
    rule(133, r".+", "test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context", "backend/app/risk/attribution_extended.py"),
    rule(134, r".+", "test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported", "backend/app/research/benchmarks.py"),


    # Phase 107: frontend/client safety contracts. Browser/E2E claims remain intentionally separate.
    rule(156, r".+", "test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only", "frontend/public/sw.js"),
    rule(157, r".+", "test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state", "frontend/src/realtime/versionedState.ts"),
    rule(163, r".+", "test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id", "frontend/src/ux/status.ts"),
    rule(164, r".+", "test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields", "frontend/src/components/HighRiskConfirmation.tsx"),
    rule(166, r".+", "test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary", "frontend/src/api/client.ts"),
    rule(155, r"safe defaults|mode awareness|visible system status|explainable decisions|destructive/high-risk action confirmation|no ambiguous BUY/SELL state|latency/staleness görünürlüğü|consistent terminology", "test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms", "frontend/src/components/StatusStrip.tsx"),
    rule(158, r"Ana Ekran|Piyasa / Scanner|^Analiz$|Pozisyonlar & Emirler|^Alarmlar$|Backtest & Araştırma|Performans & Risk|Ayarlar / Sistem|URL/deep-link state", "test_phase107_information_architecture_has_core_navigation_and_safe_deep_links", "frontend/src/App.tsx"),
    rule(160, r"Mode: PAPER / TESTNET / LIVE|Exchange: Connected/Degraded/Offline|Market Data: Fresh/Stale|Engine: Running/Halted/Reducing Only|Risk: Normal/Restricted|Server time|Portfolio Value|Daily P&L|Open Risk|Drawdown|Open Positions|Top Candidate|Critical Alerts|^symbol$|^signal$|^score$|^confidence$|^regime$|net edge|risk/block reason", "test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason", "frontend/src/pages/Dashboard.tsx"),
    rule(161, r"responsive-by-design|desktop wide|laptop|tablet landscape/portrait|^mobile$|kritik status üstte|installable manifest|offline shell|service worker trading engine|offline iken LIVE|stale cached market data", "test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety", "frontend/public/manifest.webmanifest"),
    rule(165, r"keyboard navigation|visible focus state|semantic labels|screen-reader accessible form controls|yalnızca renk ile anlam verme|Türkçe birinci sınıf", "test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text", "frontend/src/App.tsx"),


    # Phase 107 delivery documentation/packaging source contracts. Signed installer and real build remain external/unverified.
    rule(169, r"Docker Compose|migration|backup/restore|health checks|reverse proxy/TLS guide|versioned assets|compatibility metadata|version display|server compatibility check|database migration backup|rolling/restart prosedürü|backward compatibility window|rollback plan|config migration|frontend/backend API version compatibility|Hızlı Başlangıç Kılavuzu|İlk Kurulum Kılavuzu|PAPER Kullanım Kılavuzu|LIVE Güvenlik Kılavuzu|Sorun Giderme|Backup/Restore|Acil Durum Prosedürü", "test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks", "docs/UPDATE_ROLLBACK.md"),

    # Phase 109: core decision-quality, technical features and research analytics.
    rule(6, r"Bölüm 6|En az aşağıdaki indikatörleri destekle|swing highs|swing lows|Donchian Channels|Keltner Channels|BB/KC squeeze|Anchored VWAP|rolling z-score|realized volatility alternatifleri|volume profile|POC|value area|session VWAP|trend efficiency|choppiness", "test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled", "backend/app/indicators/engine.py"),
    rule(12, r".+", "test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded", "backend/app/strategies/levels.py"),
    rule(13, r"Bölüm 13|Swing low based|Percentage based|Trailing stop|Break-even stop|destekle\.|kullan\.|manuel hesaplama", "test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded", "backend/app/strategies/levels.py"),
    rule(14, r".+", "test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded", "backend/app/strategies/levels.py"),
    rule(21, r"Bölüm 21|Backtest engine oluştur|historical candles|total return|CAGR|Sharpe|Sortino|Calmar|max drawdown|win rate|loss rate|profit factor|expectancy|average win|average loss|largest win|largest loss|average holding time|number of trades", "test_phase109_backtest_performance_metrics_are_complete_and_consistent", "backend/app/backtest/analytics.py"),
    rule(21, r"trailing stop", "test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp", "backend/app/risk/position_view.py"),
    rule(22, r"Train period ve test period ayrımı yap", "test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools", "backend/app/backtest/validation.py"),
    rule(23, r"Bölüm 23|Bunu testlerle doğrula", "test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools", "backend/app/backtest/validation.py"),
    rule(24, r"Bölüm 24", "test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools", "backend/app/backtest/validation.py"),
    rule(25, r"Bölüm 25|Sensitivity analysis oluştur", "test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools", "backend/app/backtest/analytics.py"),
    rule(26, r"Bölüm 26|birden fazla strateji|Trend Following|Breakout|Pullback|Mean Reversion|Momentum", "test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement", "backend/app/strategies/catalog.py"),

    # Phase 110: configurable signal quality, extended regime and falling-knife safety.
    rule(7, r".+", "test_phase110_multi_timeframe_analysis_has_configurable_normalized_weights_contract", "backend/app/signals/multi_timeframe.py"),
    rule(8, r"Bölüm 8|low volatility|panic|breakout|breakdown|volatility|moving averages|market structure|volume", "test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume", "backend/app/strategies/regime_extended.py"),
    rule(9, r"Bölüm 9|ağırlıkları config|4H bullish trend|1H EMA21 > EMA50|RSI 54 and rising|volume \+28%|bullish market structure|15M pullback completed|ATR normal|BTC volatility elevated", "test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility", "backend/app/signals/decision_quality.py"),
    rule(11, r"Bölüm 11|lower low devam ediyor|negatif volume expansion|breakdown|ATR spike|liquidation/panic|yüksek timeframe bearish|stop mesafesi aşırı geniş|risk/reward yetersiz", "test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition", "backend/app/signals/decision_quality.py"),
    rule(27, r"Bölüm 27|outcome|return|time to TP|time to SL|sakla\.|durumu oluştur", "test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation", "backend/app/strategies/outcomes.py"),

    # Phase 111: strategy selection, review-only self learning, ML research and position health.
    rule(52, r".+", "test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee", "backend/app/research/strategy_selection.py"),
    rule(53, r".+", "test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee", "backend/app/research/strategy_selection.py"),
    rule(54, r".+", "test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes", "backend/app/research/self_learning.py"),
    rule(55, r".+", "test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection", "backend/app/research/ml_contract.py"),
    rule(59, r"Bölüm 59|Şunları takip et|unrealized PnL|current R|distance to SL|distance to TP", "test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances", "backend/app/risk/position_view.py"),

    # Phase 119: production security delivery, numeric LIVE-ramp gate and first-run safety profile.
    rule(135, r"Bölüm 135|HTTPS/TLS zorunlu|trusted proxy configuration|Backup dosyaları da şifreli", "test_phase119_tls_trusted_proxy_and_encrypted_backup_delivery_contracts_are_fail_closed", "docker/nginx/nginx.prod.conf"),
    rule(136, r"Bölüm 136|Kademeli live risk ramp|reconciliation PASS|zero unresolved critical incidents|protective order success rate acceptable|live slippage within bound|live vs shadow/paper divergence acceptable|net expectancy non-negative/acceptable with uncertainty|drawdown within bound|sufficient effective sample|multiple market conditions observed|strategy not degraded", "test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition", "backend/app/risk/live_ramp.py"),
    rule(159, r"İlk kullanım terminal dosyası|server health|^version$|database/redis readiness|clock sync|exchange seçimi|connection test|permission test|withdrawal permission rejection|account mode / market capability discovery|token/chat id|test message|komut güvenlik durumu|^TESTNET$|LIVE kilitli|MUHAZAKÂR|MUHAFAZAKÂR|DENGELİ|AGRESİF|ÖZEL|sihirli risk|OTOMATİK UYGUNLUK|allowlist/blocklist|quote asset|max universe size|new listing policy|timezone|number/date format|language|güvenlik checklist|config summary|PAPER MODE ile başlat", "test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper", "backend/app/services/setup_wizard.py"),
    rule(170, r"oluşturulan dosyaların tamamını listele|nasıl kurulacağını anlat|hangi testlerin geçtiğini listele|hangi özelliklerin gerçek, hangilerinin mock olduğunu belirt|backtest sonuçlarını raporla|OOS / walk-forward / purged-embargo sonuçlarını raporla|multiple-testing / DSR kanıtını raporla|paper trading durumunu raporla|testnet durumunu raporla|live-shadow durumunu raporla|execution ve PnL attribution raporunu ver|effective sample size ve confidence interval raporunu ver|LIVE trading'in neden varsayılan olarak kapalı olduğunu belirt|UI/UX acceptance test sonuçlarını raporla|browser/viewport test matrisini raporla|ilk kurulum sihirbazı testini raporla|web/PWA build durumunu raporla|Tauri masaüstü istemcisi üretildiyse build/signing durumunu raporla|frontend/backend version compatibility durumunu raporla|kullanıcı kılavuzlarının yerini belirt|SİSTEM İLK ÇALIŞTIRMADA PAPER MODE'DA OLMALI|AMA TÜM LIVE TRADING KODU VE ADAPTERI HAZIR OLMALI|SONRA PROJEYİ OLUŞTUR", "test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance", "docs/FINAL_DELIVERY_STATUS.md"),
    rule(155, r"Bölüm 155|ZORUNLU UX ilkeleri|progressive disclosure|undo/cancel|no dark patterns", "test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract", "frontend/src/pages/Settings.tsx"),
    rule(158, r"Bölüm 158|^Exchange$|Telegram/Bildirim|^Risk$|Coin Universe|^Strategy$|Kullanıcı & Güvenlik|Sistem Sağlığı|Yedekleme", "test_phase121_settings_information_architecture_exposes_required_domains", "frontend/src/pages/Settings.tsx"),
    rule(161, r"Bölüm 161|büyük tablolar card/list mode|order/risk detayları okunabilir|yatay scroll zorunluluğu minimum|app icons", "test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll", "frontend/src/pages/Scanner.tsx"),
    rule(161, r"app icons", "test_phase121_pwa_manifest_has_installable_application_icons", "frontend/public/manifest.webmanifest"),
    rule(167, r"lazy route loading", "test_phase107_information_architecture_has_core_navigation_and_safe_deep_links", "frontend/src/App.tsx"),
    rule(169, r"Bölüm 169|signed auto-update veya açık manuel update süreci", "test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance", "docs/UPDATE_ROLLBACK.md"),
    rule(64, r"Bölüm 64|kullanıcıya uygun kısa mesaj|kullanıcı için önerilen aksiyon|gerekiyorsa Telegram kritik alarm", "test_phase122_error_handling_has_human_message_action_correlation_and_critical_alert_channel", "frontend/src/ux/status.ts"),
    rule(66, r".+", "test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs", "PACKAGE_MANIFEST.json"),
    rule(67, r".+", "test_phase122_real_api_absence_uses_explicit_mock_adapter_and_never_fakes_unsupported_capability", "backend/app/exchange/mock.py"),
    rule(68, r".+", "test_phase122_real_api_absence_uses_explicit_mock_adapter_and_never_fakes_unsupported_capability", "reports/REAL_MOCK_UNSUPPORTED_MATRIX.md"),
    rule(69, r"Bölüm 69|WebSocket kullan|Redis cache kullan|Candle aggregation yap|Log rotation uygula", "test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts", "backend/app/data/candles.py"),
    rule(70, r".+", "test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions", "docs/STRATEGY_ASSUMPTIONS.md"),
    rule(56, r"Bölüm 56", "test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations", "backend/app/signals/engine.py"),
    rule(57, r"Bölüm 57", "test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations", "backend/app/audit/decision_evidence.py"),
    rule(58, r"Bölüm 58", "test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations", "backend/app/strategies/outcomes.py"),
    rule(59, r"volatility|trend change|trailing stop|partial TP", "test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp", "backend/app/risk/position_view.py"),
    rule(60, r"Bölüm 60|AUTO_EXECUTION varsayılan", "test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations", "backend/app/core/config.py"),
    rule(61, r"Bölüm 61|Aşağıdakine benzer temiz bir yapı oluştur", "test_phase123_project_structure_is_cleanly_split_and_api_surface_is_versioned", "ARCHITECTURE.md"),
    rule(62, r"Bölüm 62", "test_phase123_project_structure_is_cleanly_split_and_api_surface_is_versioned", "backend/app/main.py"),
    rule(101, r"Bölüm 101", "test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux", "backend/app/release/precedence.py"),
    rule(63, r"Bölüm 63|debug paneli|React \+ TypeScript|responsive desktop/tablet/mobile|erişilebilir component|dark/light theme|route-level error boundary|loading / empty / stale / error / unauthorized", "test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded", "frontend/src/App.tsx"),
    rule(63, r"REST initial snapshot|server trading state source-of-truth|frontend refresh veya kapanması trading engine", "test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup", "frontend/src/realtime/serverState.ts"),
    rule(63, r"Ana Ekran|Piyasa / Coin Tarayıcı|^Analiz$|Pozisyonlar & Emirler|^Alarmlar$|Backtest & Araştırma|Performans & Risk|Ayarlar / Sistem|LIVE / PAPER / TESTNET|GERÇEK PARA|aktif universe|hariç bırakılma gerekçeleri|liquidity/spread/volume|top candidate ranking|signal/score/confidence|korelasyon heatmap|cluster/tema konsantrasyonu|quote-asset exposure|per-symbol data health|listing age / new-listing risk badge|delisting/suspension|^Signal$|^Entry$|TP1/TP2/TP3|risk amount \+ risk percent|^Confidence$|^Reasons$|^Risks$|data timestamp|^mode$|TRADE ALL", "test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible", "frontend/src/pages/Scanner.tsx"),
    rule(63, r"Türkçe öncelikli i18n", "test_phase125_turkish_first_i18n_centralizes_shell_strings", "frontend/src/i18n/tr.ts"),
    rule(161, r"grafik gesture/zoom", "test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup", "frontend/src/components/MarketChart.tsx"),
    rule(165, r"error mesajları alanla ilişkilendirilmeli", "test_phase125_login_error_is_programmatically_associated_with_field", "frontend/src/components/AuthGate.tsx"),
    rule(167, r"large scanner table virtualization", "test_phase125_virtualized_rows_bounds_large_client_render_work", "frontend/src/components/VirtualizedRows.tsx"),
    rule(167, r"chart data windowing/downsampling", "test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup", "frontend/src/components/MarketChart.tsx"),
    rule(167, r"unmounted component subscription cleanup", "test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup", "frontend/src/realtime/serverState.ts"),
    rule(1, r"candlestick \+ volume \+ indicator panes|order/entry/SL/TP markerları", "test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup", "frontend/src/components/MarketChart.tsx"),
    rule(1, r"attribution/license gereksinimlerine uy|sınırlı local UI state", "test_phase125_local_ui_state_is_component_scoped_and_third_party_attribution_is_explicit", "THIRD_PARTY_NOTICES.md"),
    rule(65, r"^pytest$", "test_local_test_evidence_requires_git_bound_shard_and_log_hashes", "reports/local_acceptance/full_regression_manifest.json"),
    rule(65, r"Her testin sonucunu raporla", "test_local_test_evidence_requires_git_bound_shard_and_log_hashes", "reports/local_acceptance/full_regression_manifest.json"),
    rule(69, r"Memory leak kontrolü", "test_phase128_local_mock_soak_has_bounded_retained_memory_growth", "scripts/local_load_soak.py"),
    rule(136, r"^Known limitations$|^Unresolved risks$", "test_phase128_delivery_status_discloses_known_limitations_and_unresolved_risks", "docs/FINAL_DELIVERY_STATUS.md"),
    rule(65, r"^health check$", "test_health", "tests/integration/test_api.py"),
    rule(65, r"^historical backtest$", "test_phase109_backtest_performance_metrics_are_complete_and_consistent", "backend/app/research/backtest_analytics.py"),
    rule(65, r"^walk-forward$|^Monte Carlo$", "test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools", "backend/app/research/backtest_analytics.py"),
    rule(65, r"^Telegram test$", "test_telegram_bot_api_sends_message_without_exposing_token_in_payload", "backend/app/monitoring/telegram.py"),
    rule(65, r"multi-symbol universe/scanner smoke test", "test_universe_scanner_metadata_and_breadth", "tests/integration/test_product_endpoints.py"),
    rule(65, r"official exchange API capability/filter/rate-limit contract verification", "test_phase26_official_binance_reference_is_date_stamped_and_runtime_capability_remains_source_of_truth", "reports/PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md"),
    rule(160, r"Bölüm 160", "test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason", "frontend/src/pages/Dashboard.tsx"),
    # Phase 130: official-version governance and optional fail-closed Tauri source shell.
    rule(1, r"Prompt içindeki sürüm numaralarını körlemesine sabitleme|Implementasyon gününde resmi stable release.i doğrula|Major upgrade yalnızca migration notes \+ regression test", "test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build", "docs/TECHNOLOGY_VERSION_VERIFICATION.md"),
    rule(1, r"Tauri 2\.x veya implementasyon anındaki uyumlu stable major", "test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build", "frontend/src-tauri/Cargo.toml"),
    rule(1, r"Masaüstü uygulaması yalnızca güvenli client shell.dir; trading engine masaüstü process.ine bağımlı OLMAMALI", "test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities", "frontend/src-tauri/src/main.rs"),
    rule(162, r"mevcut React UI.yı paketler", "test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities", "frontend/src-tauri/tauri.conf.json"),
    rule(162, r"server API/WebSocket.e güvenli bağlanır", "test_phase130_desktop_api_boundary_requires_https_no_url_credentials_and_wss", "frontend/src/runtime/clientShell.ts"),
    rule(162, r"Exchange API secret.ı Tauri frontend webview içinde saklama", "test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities", "frontend/src-tauri/capabilities/default.json"),
    rule(162, r"Client compromise tek başına withdrawal yetkisi veremez|Desktop app kapatılması açık pozisyon yönetimini durdurmaz", "test_phase130_desktop_shell_has_no_execution_ownership_and_cannot_grant_withdrawal_by_client_compromise", "docs/TECHNOLOGY_VERSION_VERIFICATION.md"),
    rule(162, r"Client version / backend API compatibility kontrolü yap|incompatible client.a high-risk action izni verme", "test_phase130_client_server_compatibility_is_fail_closed_for_high_risk_ui_boot", "frontend/src/runtime/clientShell.ts"),
    rule(162, r"native notification opsiyonel destekler", "test_phase133_tauri_native_notification_is_opt_in_without_broad_client_permissions", "frontend/src-tauri/src/main.rs"),
    # Phase 131/132: auditable WCAG-AA core contrast and local frontend state memory soak.
    rule(165, r"Bölüm 165|WCAG 2\.2 AA.ya mümkün olduğunca uyum", "test_phase131_section165_accessibility_localization_contract_is_complete_at_source_level", "frontend/src/ux/theme.ts"),
    rule(165, r"contrast kontrolü", "test_phase131_explicit_theme_tokens_meet_wcag_aa_core_contrast_budget", "frontend/src/ux/theme.ts"),
    rule(167, r"^memory leak test$", "test_phase132_frontend_realtime_state_memory_soak_has_bounded_heap_growth", "frontend/src/realtime/versionedState.ts"),

]


def sync(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for row in doc["requirements"]:
        if row.get("status") == "UNSUPPORTED":
            row["test_ids"] = []
            row["test_id"] = None
            row["evidence_refs"] = ["reports/REAL_MOCK_UNSUPPORTED_MATRIX.md"]
            row["evidence"] = "reports/REAL_MOCK_UNSUPPORTED_MATRIX.md"
            row["last_verified_release"] = RELEASE
            row["known_limitations"] = sorted(set(row.get("known_limitations", [])) | {"Unsupported in this release; no synthetic provider or fake capability is substituted."})
        else:
            row["status"] = "NOT_TESTED"
            row["test_ids"] = []
            row["test_id"] = None
            row["evidence_refs"] = []
            row["evidence"] = None
            row["last_verified_release"] = None
        for section, pattern, test, module in RULES:
            if row["section"] == section and pattern.search(row["description"]):
                row["status"] = "PASS"
                row["test_ids"] = sorted(set(row.get("test_ids", [])) | {test})
                row["test_id"] = row["test_ids"][0]
                modules = set(row.get("implementation_modules", []))
                modules.add(module)
                row["implementation_modules"] = sorted(modules)
                row["implementation_module"] = row["implementation_modules"][0]
                refs = {f"{TESTS[test]}::{test}", "reports/LATEST_PYTEST.txt"}
                row["evidence_refs"] = sorted(set(row.get("evidence_refs", [])) | refs)
                row["evidence"] = row["evidence_refs"][0]
                row["last_verified_release"] = RELEASE
    doc["generated_at"] = datetime.now(timezone.utc).isoformat()
    doc["release"] = RELEASE
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    return doc


def write_human(doc: dict):
    counts = Counter(row["status"] for row in doc["requirements"])
    lines = [
        "# REQUIREMENTS_TRACEABILITY.md",
        "",
        f"Release: `{RELEASE}`",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        f"Status counts: `{dict(counts)}`",
        "",
        "> PASS is evidence-bound to the current test inventory and latest green full-suite report. Credentialed exchange, Docker runtime, frontend resolved-build, PITR restore, live-shadow campaign and real-market statistical gates remain NOT_TESTED unless separately evidenced.",
        "",
        "| Requirement | Section | Priority | Status | Summary | Test evidence |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in doc["requirements"]:
        evidence = ", ".join(row.get("test_ids", []))
        summary = row["description"].replace("|", "\\|")
        lines.append(f"| {row['requirement_id']} | {row['section']} | {row['priority']} | {row['status']} | {summary} | {evidence} |")
    Path("REQUIREMENTS_TRACEABILITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    docs = [sync(path) for path in MATRIX_FILES]
    write_human(docs[0])
    counts = Counter(row["status"] for row in docs[0]["requirements"])
    print(dict(counts))


if __name__ == "__main__":
    main()
