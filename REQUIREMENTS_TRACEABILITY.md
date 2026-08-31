# REQUIREMENTS_TRACEABILITY.md

Release: `0.3.0-local-acceptance`
Generated: `2026-08-31T14:24:01.421769+00:00`
Status counts: `{'NOT_TESTED': 100, 'PASS': 2591}`

> PASS is evidence-bound to the current test inventory and latest green full-suite report. Credentialed exchange, Docker runtime, frontend resolved-build, PITR restore, live-shadow campaign and real-market statistical gates remain NOT_TESTED unless separately evidenced.

| Requirement | Section | Priority | Status | Summary | Test evidence |
|---|---:|---:|---|---|---|
| REQ-V51-001-001 | 1 | P1 | NOT_TESTED | Bölüm 1 (TEKNOLOJİ YIĞINI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-001-002 | 1 | P1 | PASS | Kurulum problemi yaratacaksa pandas/numpy tabanlı indikatör implementasyonlarını kullan. | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-001-003 | 1 | P1 | PASS | React 19.x veya implementasyon anındaki uyumlu güncel stable React major/minor | test_canonical_profile_matches_backend_and_frontend_manifests |
| REQ-V51-001-004 | 1 | P1 | PASS | TypeScript strict mode | test_typescript_strict_and_production_defaults_are_conservative |
| REQ-V51-001-005 | 1 | P1 | PASS | Vite veya eşdeğer modern build tool | test_canonical_profile_matches_backend_and_frontend_manifests |
| REQ-V51-001-006 | 1 | P1 | PASS | Material UI (MUI) implementasyon anındaki güncel stable production major'ı | test_canonical_profile_matches_backend_and_frontend_manifests |
| REQ-V51-001-007 | 1 | P1 | PASS | server-state için TanStack Query veya eşdeğer güvenilir çözüm | test_canonical_profile_matches_backend_and_frontend_manifests |
| REQ-V51-001-008 | 1 | P1 | PASS | sınırlı local UI state için Zustand/Redux Toolkit veya eşdeğeri; gereksiz global state kurma | test_phase125_local_ui_state_is_component_scoped_and_third_party_attribution_is_explicit |
| REQ-V51-001-009 | 1 | P1 | PASS | Prompt içindeki sürüm numaralarını körlemesine sabitleme. | test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build |
| REQ-V51-001-010 | 1 | P1 | PASS | Implementasyon gününde resmi stable release'i doğrula. | test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build |
| REQ-V51-001-011 | 1 | P1 | NOT_TESTED | package-lock/pnpm-lock/uv.lock gibi lockfile üret. |  |
| REQ-V51-001-012 | 1 | P1 | PASS | Major upgrade yalnızca migration notes + regression test sonrasında yapılmalı. | test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build |
| REQ-V51-001-013 | 1 | P1 | PASS | Experimental/canary paketler production default'u olamaz. | test_canonical_profile_matches_backend_and_frontend_manifests |
| REQ-V51-001-014 | 1 | P1 | PASS | TradingView Lightweight Charts 5.x veya implementasyon anındaki uyumlu stable major | test_canonical_profile_matches_backend_and_frontend_manifests |
| REQ-V51-001-015 | 1 | P1 | PASS | TypeScript entegrasyonu | test_typescript_strict_and_production_defaults_are_conservative |
| REQ-V51-001-016 | 1 | P1 | PASS | candlestick + volume + indicator panes | test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup |
| REQ-V51-001-017 | 1 | P1 | PASS | order/entry/SL/TP markerları | test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup |
| REQ-V51-001-018 | 1 | P1 | PASS | attribution/license gereksinimlerine uy | test_phase125_local_ui_state_is_component_scoped_and_third_party_attribution_is_explicit |
| REQ-V51-001-019 | 1 | P1 | PASS | Tauri 2.x veya implementasyon anındaki uyumlu stable major | test_phase130_official_tauri_reference_is_version_checked_without_claiming_lock_or_build |
| REQ-V51-001-020 | 1 | P1 | PASS | Masaüstü uygulaması yalnızca güvenli client shell'dir; trading engine masaüstü process'ine bağımlı OLMAMALI. | test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities |
| REQ-V51-002-001 | 2 | P0 | PASS | Bölüm 2 (EXCHANGE MİMARİSİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_exchange_architecture_is_adapter_based_and_extensible_without_binance_coupling |
| REQ-V51-002-002 | 2 | P0 | PASS | get_ticker() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-003 | 2 | P0 | PASS | get_order_book() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-004 | 2 | P0 | PASS | get_balance() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-005 | 2 | P0 | PASS | get_positions() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-006 | 2 | P0 | PASS | get_open_orders() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-007 | 2 | P0 | PASS | get_klines() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-008 | 2 | P0 | PASS | create_market_order() | test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract |
| REQ-V51-002-009 | 2 | P0 | PASS | create_limit_order() | test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract |
| REQ-V51-002-010 | 2 | P0 | PASS | cancel_order() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-011 | 2 | P0 | PASS | cancel_all_orders() | test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract |
| REQ-V51-002-012 | 2 | P0 | PASS | create_stop_order() | test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract |
| REQ-V51-002-013 | 2 | P0 | PASS | create_take_profit_order() | test_explicit_exchange_adapter_order_wrappers_use_generic_order_contract |
| REQ-V51-002-014 | 2 | P0 | PASS | get_order() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-015 | 2 | P0 | PASS | get_exchange_info() | test_exchange_symbol_and_asset_metadata_are_from_exchange_info |
| REQ-V51-002-016 | 2 | P0 | PASS | get_server_time() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-017 | 2 | P0 | PASS | list_markets() | test_list_markets |
| REQ-V51-002-018 | 2 | P0 | PASS | get_symbol_metadata(symbol) | test_exchange_symbol_and_asset_metadata_are_from_exchange_info |
| REQ-V51-002-019 | 2 | P0 | PASS | get_asset_metadata(asset) | test_exchange_symbol_and_asset_metadata_are_from_exchange_info |
| REQ-V51-002-020 | 2 | P0 | PASS | get_trading_status(symbol) | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-021 | 2 | P0 | PASS | get_rate_limits() | test_rate_limits_runtime |
| REQ-V51-002-022 | 2 | P0 | PASS | get_scheduled_listings()  # exchange destekliyorsa capability-driven | test_scheduled_listings_use_documented_market_data_endpoint_and_api_key_only |
| REQ-V51-002-023 | 2 | P0 | PASS | get_exchange_status() | test_exchange_adapter_read_and_cancel_query_contract_methods |
| REQ-V51-002-024 | 2 | P0 | PASS | İleride Bybit / OKX / Coinbase gibi exchange'ler eklenebilecek şekilde adapter pattern kullan. | test_phase22_exchange_architecture_is_adapter_based_and_extensible_without_binance_coupling |
| REQ-V51-002-025 | 2 | P0 | PASS | KRİTİK IMPLEMENTASYON KURALI: | test_phase26_official_binance_reference_is_date_stamped_and_runtime_capability_remains_source_of_truth |
| REQ-V51-002-026 | 2 | P0 | PASS | Exchange endpoint, filter, order type, WebSocket subscription, rate-limit ve symbol-status ayrıntılarını prompt içindeki örneklerden körlemesine kopyalama. Implementasyon anında ilgili exchange'in güncel RESMİ API dokümantasyonunu doğrula; runtime capability discovery ve exchangeInfo/filter verisini source-of-truth kabul et. API değişikliği tespit edilirse fail-safe davran. | test_capabilities_are_discovered_not_assumed |
| REQ-V51-003-001 | 3 | P0 | PASS | Bölüm 3 (MODLAR) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_modes_contract_keeps_paper_as_safe_default_and_explicit_modes |
| REQ-V51-003-002 | 3 | P0 | PASS | Varsayılan: | test_defaults_paper |
| REQ-V51-003-003 | 3 | P0 | PASS | olmalı. | test_defaults_paper |
| REQ-V51-004-001 | 4 | P0 | PASS | Bölüm 4 (GERÇEK ZAMANLI VERİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-004-002 | 4 | P0 | PASS | timeframe destekle. | test_supported_timeframes |
| REQ-V51-004-003 | 4 | P0 | PASS | trades | test_public_stream_url_uses_documented_combined_stream_shapes |
| REQ-V51-004-004 | 4 | P0 | PASS | ticker | test_public_stream_url_uses_documented_combined_stream_shapes |
| REQ-V51-004-005 | 4 | P0 | PASS | order book | test_public_stream_url_uses_documented_combined_stream_shapes |
| REQ-V51-004-006 | 4 | P0 | PASS | klines | test_public_stream_url_uses_documented_combined_stream_shapes |
| REQ-V51-004-007 | 4 | P0 | PASS | REST API ile periyodik doğrulama yap. | test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe |
| REQ-V51-004-008 | 4 | P0 | PASS | otomatik reconnect | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-004-009 | 4 | P0 | PASS | exponential backoff | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-004-010 | 4 | P0 | PASS | heartbeat | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-004-011 | 4 | P0 | PASS | stale-data detection | test_public_stream_parser_and_stale_detection |
| REQ-V51-004-012 | 4 | P0 | PASS | uygula. | test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe |
| REQ-V51-004-013 | 4 | P0 | PASS | Verinin timestamp'ini mutlaka sakla. | test_public_stream_parser_and_stale_detection |
| REQ-V51-005-001 | 5 | P0 | PASS | Bölüm 5 (VERİ KALİTESİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_sequence_guard_rejects_duplicate_and_out_of_order_market_events |
| REQ-V51-005-002 | 5 | P0 | PASS | timestamp | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-003 | 5 | P0 | PASS | source | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-004 | 5 | P0 | PASS | timeframe | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-005 | 5 | P0 | PASS | symbol | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-006 | 5 | P0 | PASS | received_at | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-007 | 5 | P0 | PASS | exchange_time | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-008 | 5 | P0 | PASS | latency | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-009 | 5 | P0 | PASS | sakla. | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency |
| REQ-V51-005-010 | 5 | P0 | PASS | gibi yapılandırılabilir bir limit kullan. | test_stale |
| REQ-V51-005-011 | 5 | P0 | PASS | Gap detection yap. | test_candle_gap |
| REQ-V51-005-012 | 5 | P0 | PASS | tespit et | test_sequence_guard_rejects_duplicate_and_out_of_order_market_events |
| REQ-V51-005-013 | 5 | P0 | PASS | logla | test_sequence_guard_rejects_duplicate_and_out_of_order_market_events |
| REQ-V51-005-014 | 5 | P0 | PASS | gerekiyorsa REST ile tamamla | test_periodic_rest_reconciliation_schedule_is_due_and_clock_safe |
| REQ-V51-005-015 | 5 | P0 | PASS | veri tamamlanmadan sinyal üretme. | test_analyze_gap_rejected |
| REQ-V51-006-001 | 6 | P1 | PASS | Bölüm 6 (TEKNİK ANALİZ MOTORU) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-002 | 6 | P1 | PASS | En az aşağıdaki indikatörleri destekle: | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-003 | 6 | P1 | PASS | SMA 20 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-004 | 6 | P1 | PASS | SMA 50 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-005 | 6 | P1 | PASS | SMA 100 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-006 | 6 | P1 | PASS | SMA 200 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-007 | 6 | P1 | PASS | EMA 9 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-008 | 6 | P1 | PASS | EMA 21 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-009 | 6 | P1 | PASS | EMA 50 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-010 | 6 | P1 | PASS | EMA 200 | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-011 | 6 | P1 | PASS | VWAP | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-012 | 6 | P1 | PASS | MACD | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-013 | 6 | P1 | PASS | Stochastic RSI | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-014 | 6 | P1 | PASS | Bollinger Bands | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-015 | 6 | P1 | PASS | Bollinger Band Width | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-016 | 6 | P1 | PASS | Historical Volatility | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-017 | 6 | P1 | PASS | Volume SMA | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-018 | 6 | P1 | PASS | Volume Ratio | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-019 | 6 | P1 | PASS | Volume Spike | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-020 | 6 | P1 | PASS | Higher High | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-021 | 6 | P1 | PASS | Higher Low | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-022 | 6 | P1 | PASS | Lower High | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-023 | 6 | P1 | PASS | Lower Low | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-024 | 6 | P1 | PASS | swing highs | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-025 | 6 | P1 | PASS | swing lows | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-026 | 6 | P1 | PASS | recent support | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-027 | 6 | P1 | PASS | recent resistance | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-028 | 6 | P1 | PASS | Donchian Channels | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-029 | 6 | P1 | PASS | Keltner Channels ve BB/KC squeeze | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-030 | 6 | P1 | PASS | Anchored VWAP | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-031 | 6 | P1 | PASS | rolling z-score | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-032 | 6 | P1 | PASS | linear-regression slope / trend slope | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-006-033 | 6 | P1 | PASS | realized volatility alternatifleri (örn. close-to-close; veri uygunsa Parkinson/Garman-Klass) | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-034 | 6 | P1 | PASS | volume profile / POC / value area (yalnızca veri kalitesi yeterliyse) | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-035 | 6 | P1 | PASS | session VWAP | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-006-036 | 6 | P1 | PASS | trend efficiency / choppiness ölçümleri | test_phase109_advanced_indicator_set_is_finite_point_in_time_and_quality_labeled |
| REQ-V51-007-001 | 7 | P1 | PASS | Bölüm 7 (MULTI TIMEFRAME ANALYSIS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase110_multi_timeframe_analysis_has_configurable_normalized_weights_contract |
| REQ-V51-007-002 | 7 | P1 | PASS | gibi configurable bir yapı oluştur. | test_multi_timeframe_bullish_alignment, test_phase110_multi_timeframe_analysis_has_configurable_normalized_weights_contract |
| REQ-V51-007-003 | 7 | P1 | PASS | MULTI_TIMEFRAME_CONFLICT sistemi oluştur. | test_multi_timeframe_conflict_blocks_low_timeframe_buy, test_phase110_multi_timeframe_analysis_has_configurable_normalized_weights_contract |
| REQ-V51-008-001 | 8 | P1 | PASS | Bölüm 8 (MARKET REGIME DETECTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-002 | 8 | P1 | PASS | bullish trend | test_bullish_regime |
| REQ-V51-008-003 | 8 | P1 | PASS | bearish trend | test_bearish_regime |
| REQ-V51-008-004 | 8 | P1 | PASS | sideways | test_sideways_regime |
| REQ-V51-008-005 | 8 | P1 | PASS | high volatility | test_high_volatility_regime, test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-006 | 8 | P1 | PASS | low volatility | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-007 | 8 | P1 | PASS | panic | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-008 | 8 | P1 | PASS | breakout | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-009 | 8 | P1 | PASS | breakdown | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-010 | 8 | P1 | PASS | volatility | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-011 | 8 | P1 | PASS | moving averages | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-012 | 8 | P1 | PASS | market structure | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-008-013 | 8 | P1 | PASS | volume | test_phase110_extended_regime_detects_low_vol_panic_breakout_breakdown_and_uses_vol_ma_structure_volume |
| REQ-V51-009-001 | 9 | P1 | PASS | Bölüm 9 (SIGNAL ENGINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-002 | 9 | P1 | PASS | Composite scoring sistemi oluştur. | test_signal_explainability |
| REQ-V51-009-003 | 9 | P1 | PASS | Ama ağırlıkları config üzerinden değiştirilebilir yap. | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-004 | 9 | P1 | PASS | 4H bullish trend | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-005 | 9 | P1 | PASS | 1H EMA21 > EMA50 | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-006 | 9 | P1 | PASS | RSI 54 and rising | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-007 | 9 | P1 | PASS | volume +28% | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-008 | 9 | P1 | PASS | bullish market structure | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-009 | 9 | P1 | PASS | 15M pullback completed | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-010 | 9 | P1 | PASS | ATR normal | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-009-011 | 9 | P1 | PASS | BTC volatility elevated | test_phase110_configurable_signal_weights_score_4h_1h_rsi_volume_structure_pullback_atr_and_btc_volatility |
| REQ-V51-010-001 | 10 | P1 | PASS | Bölüm 10 (SIGNAL EXPLAINABILITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_signal_explainability |
| REQ-V51-011-001 | 11 | P1 | PASS | Bölüm 11 ("DÜŞERKEN AL" HATASINI ÖNLE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-002 | 11 | P1 | PASS | lower low devam ediyor | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-003 | 11 | P1 | PASS | güçlü bearish trend | test_falling_knife_blocks_bearish |
| REQ-V51-011-004 | 11 | P1 | PASS | fiyat EMA50 ve EMA200 altında | test_falling_knife_blocks_bearish |
| REQ-V51-011-005 | 11 | P1 | PASS | negatif volume expansion | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-006 | 11 | P1 | PASS | breakdown | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-007 | 11 | P1 | PASS | ATR spike | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-008 | 11 | P1 | PASS | liquidation/panic koşulu | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-009 | 11 | P1 | PASS | yüksek timeframe bearish | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-010 | 11 | P1 | PASS | stop mesafesi aşırı geniş | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-011 | 11 | P1 | PASS | risk/reward yetersiz | test_phase110_falling_knife_gate_blocks_every_required_deterioration_condition |
| REQ-V51-011-012 | 11 | P1 | PASS | "Falling knife protection" oluştur. | test_falling_knife_never_generates_buy_and_exposes_bearish_direction |
| REQ-V51-012-001 | 12 | P1 | PASS | Bölüm 12 (ENTRY ENGINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-012-002 | 12 | P1 | PASS | olmalı. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-001 | 13 | P1 | PASS | Bölüm 13 (STOP LOSS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-002 | 13 | P1 | PASS | ATR based | test_signal_explainability |
| REQ-V51-013-003 | 13 | P1 | PASS | Swing low based | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-004 | 13 | P1 | PASS | Percentage based | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-005 | 13 | P1 | PASS | Trailing stop | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-006 | 13 | P1 | PASS | Break-even stop | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-007 | 13 | P1 | PASS | destekle. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-008 | 13 | P1 | PASS | kullan. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-013-009 | 13 | P1 | PASS | Stop loss hiçbir koşulda manuel hesaplama hatasına açık olmamalı. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-014-001 | 14 | P1 | PASS | Bölüm 14 (TAKE PROFIT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-014-002 | 14 | P1 | PASS | Configurable yap. | test_phase109_entry_stop_take_profit_trailing_and_break_even_are_machine_calculated_and_bounded |
| REQ-V51-015-001 | 15 | P0 | PASS | Bölüm 15 (POSITION SIZING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_seeded_position_sizing_never_exceeds_risk_budget |
| REQ-V51-015-002 | 15 | P0 | PASS | Risk-based position sizing kullan. | test_seeded_position_sizing_never_exceeds_risk_budget |
| REQ-V51-015-003 | 15 | P0 | PASS | ifadesi yalnızca örnektir; production default'u körlemesine %1 kabul etme. Risk bütçesi backtest/OOS/paper/live-ramp kanıtına göre configurable olmalı. | test_seeded_position_sizing_never_exceeds_risk_budget |
| REQ-V51-015-004 | 15 | P0 | PASS | stop distance | test_position_size_reduces_with_wider_stop |
| REQ-V51-015-005 | 15 | P0 | PASS | entry fee | test_costs_in_effective_loss |
| REQ-V51-015-006 | 15 | P0 | PASS | expected exit fee | test_costs_in_effective_loss |
| REQ-V51-015-007 | 15 | P0 | PASS | expected spread | test_costs_in_effective_loss |
| REQ-V51-015-008 | 15 | P0 | PASS | expected entry slippage | test_costs_in_effective_loss |
| REQ-V51-015-009 | 15 | P0 | PASS | expected stop slippage / gap-through buffer | test_costs_in_effective_loss |
| REQ-V51-015-010 | 15 | P0 | PASS | funding/borrow cost (uygunsa) | test_funding_borrow_cost_increases_effective_loss_when_applicable |
| REQ-V51-016-001 | 16 | P0 | PASS | Bölüm 16 (PORTFOLIO RISK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_drawdown_blocks |
| REQ-V51-016-002 | 16 | P0 | PASS | Şunları kontrol et: | test_quote_asset_exposure_blocks |
| REQ-V51-016-003 | 16 | P0 | PASS | max portfolio exposure | test_exposure_blocks |
| REQ-V51-016-004 | 16 | P0 | PASS | max single-asset exposure | test_asset_exposure_blocks |
| REQ-V51-016-005 | 16 | P0 | PASS | max correlated-cluster exposure | test_cluster_exposure |
| REQ-V51-016-006 | 16 | P0 | PASS | max quote-asset exposure | test_quote_asset_exposure_blocks |
| REQ-V51-016-007 | 16 | P0 | PASS | max concurrent positions | test_position_count_blocks |
| REQ-V51-016-008 | 16 | P0 | PASS | max daily loss | test_daily_loss_blocks |
| REQ-V51-016-009 | 16 | P0 | PASS | max weekly loss | test_weekly_loss_blocks |
| REQ-V51-016-010 | 16 | P0 | PASS | max drawdown | test_drawdown_blocks |
| REQ-V51-016-011 | 16 | P0 | PASS | max consecutive losses | test_consecutive_losses_block |
| REQ-V51-016-012 | 16 | P0 | PASS | volatility-adjusted exposure | test_volatility_adjusted_exposure_blocks |
| REQ-V51-016-013 | 16 | P0 | PASS | olmalı. | test_quote_asset_exposure_blocks |
| REQ-V51-017-001 | 17 | P0 | PASS | Bölüm 17 (CIRCUIT BREAKER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_fatal_circuit_conditions |
| REQ-V51-017-002 | 17 | P0 | PASS | exchange API hatası | test_fatal_circuit_conditions |
| REQ-V51-017-003 | 17 | P0 | PASS | WebSocket data stale | test_fatal_circuit_conditions |
| REQ-V51-017-004 | 17 | P0 | PASS | clock drift | test_fatal_circuit_conditions |
| REQ-V51-017-005 | 17 | P0 | PASS | database unavailable | test_fatal_circuit_conditions |
| REQ-V51-017-006 | 17 | P0 | PASS | Redis unavailable | test_fatal_circuit_conditions |
| REQ-V51-017-007 | 17 | P0 | PASS | duplicate order | test_fatal_circuit_conditions |
| REQ-V51-017-008 | 17 | P0 | PASS | abnormal spread | test_fatal_circuit_conditions |
| REQ-V51-017-009 | 17 | P0 | PASS | abnormal volatility | test_fatal_circuit_conditions |
| REQ-V51-017-010 | 17 | P0 | PASS | daily loss limit | test_fatal_circuit_conditions |
| REQ-V51-017-011 | 17 | P0 | PASS | max drawdown | test_fatal_circuit_conditions |
| REQ-V51-017-012 | 17 | P0 | PASS | repeated order rejection | test_fatal_circuit_conditions |
| REQ-V51-017-013 | 17 | P0 | PASS | account balance inconsistency | test_fatal_circuit_conditions |
| REQ-V51-018-001 | 18 | P0 | PASS | Bölüm 18 (ORDER MANAGEMENT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_idempotent_submit |
| REQ-V51-018-002 | 18 | P0 | PASS | Order state machine oluştur: | test_order_transition_direct_fill |
| REQ-V51-018-003 | 18 | P0 | PASS | client_order_id | test_idempotent_submit |
| REQ-V51-018-004 | 18 | P0 | PASS | exchange_order_id | test_idempotent_submit |
| REQ-V51-018-005 | 18 | P0 | PASS | symbol | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-006 | 18 | P0 | PASS | side | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-007 | 18 | P0 | PASS | quantity | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-008 | 18 | P0 | PASS | price | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-009 | 18 | P0 | PASS | stop price | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-010 | 18 | P0 | PASS | timestamp | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-011 | 18 | P0 | PASS | status | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-012 | 18 | P0 | PASS | fees | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-013 | 18 | P0 | PASS | sakla. | test_order_persistence_schema_contains_required_execution_fields |
| REQ-V51-018-014 | 18 | P0 | PASS | Duplicate order protection oluştur. | test_idempotent_submit |
| REQ-V51-018-015 | 18 | P0 | PASS | Aynı sinyal için iki kere emir gönderilmesini engelle. | test_idempotent_submit |
| REQ-V51-019-001 | 19 | P0 | PASS | Bölüm 19 (POSITION RECONCILIATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_reconciliation_clean |
| REQ-V51-019-002 | 19 | P0 | PASS | exchange balance | test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks |
| REQ-V51-019-003 | 19 | P0 | PASS | open positions | test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks |
| REQ-V51-019-004 | 19 | P0 | PASS | open orders | test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks |
| REQ-V51-019-005 | 19 | P0 | PASS | local database | test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks |
| REQ-V51-020-001 | 20 | P1 | PASS | Bölüm 20 (PAPER TRADING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_paper_market_partial_fill_models_fee_slippage_and_latency |
| REQ-V51-020-002 | 20 | P1 | NOT_TESTED | Gerçek piyasa verisiyle sanal işlem yap. |  |
| REQ-V51-020-003 | 20 | P1 | NOT_TESTED | entry |  |
| REQ-V51-020-004 | 20 | P1 | NOT_TESTED | stop |  |
| REQ-V51-020-005 | 20 | P1 | PASS | slippage | test_phase134_paper_fixture_models_slippage_and_latency_without_real_orders |
| REQ-V51-020-006 | 20 | P1 | PASS | latency | test_phase134_paper_fixture_models_slippage_and_latency_without_real_orders |
| REQ-V51-021-001 | 21 | P1 | PASS | Bölüm 21 (BACKTEST ENGINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-002 | 21 | P1 | PASS | Backtest engine oluştur. | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-003 | 21 | P1 | PASS | historical candles | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-004 | 21 | P1 | PASS | fees | test_next_bar_entry_and_costs |
| REQ-V51-021-005 | 21 | P1 | PASS | slippage | test_next_bar_entry_and_costs |
| REQ-V51-021-006 | 21 | P1 | PASS | spread | test_next_bar_entry_and_costs |
| REQ-V51-021-007 | 21 | P1 | PASS | partial fills | test_next_bar_entry_and_costs |
| REQ-V51-021-008 | 21 | P1 | PASS | stop loss | test_next_bar_entry_and_costs |
| REQ-V51-021-009 | 21 | P1 | PASS | take profit | test_next_bar_entry_and_costs |
| REQ-V51-021-010 | 21 | P1 | PASS | trailing stop | test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp |
| REQ-V51-021-011 | 21 | P1 | PASS | position sizing | test_next_bar_entry_and_costs |
| REQ-V51-021-012 | 21 | P1 | PASS | total return | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-013 | 21 | P1 | PASS | CAGR | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-014 | 21 | P1 | PASS | Sharpe | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-015 | 21 | P1 | PASS | Sortino | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-016 | 21 | P1 | PASS | Calmar | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-017 | 21 | P1 | PASS | max drawdown | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-018 | 21 | P1 | PASS | win rate | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-019 | 21 | P1 | PASS | loss rate | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-020 | 21 | P1 | PASS | profit factor | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-021 | 21 | P1 | PASS | expectancy | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-022 | 21 | P1 | PASS | average win | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-023 | 21 | P1 | PASS | average loss | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-024 | 21 | P1 | PASS | largest win | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-025 | 21 | P1 | PASS | largest loss | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-026 | 21 | P1 | PASS | average holding time | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-021-027 | 21 | P1 | PASS | number of trades | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-022-001 | 22 | P1 | PASS | Bölüm 22 (WALK-FORWARD TEST) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_walk_forward_no_overlap |
| REQ-V51-022-002 | 22 | P1 | PASS | Train period ve test period ayrımı yap. | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-023-001 | 23 | P1 | PASS | Bölüm 23 (NO LOOK-AHEAD BIAS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-023-002 | 23 | P1 | PASS | Bunu testlerle doğrula. | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-024-001 | 24 | P1 | PASS | Bölüm 24 (MONTE CARLO) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-024-002 | 24 | P1 | PASS | expected return | test_monte_carlo_fields |
| REQ-V51-024-003 | 24 | P1 | PASS | worst drawdown | test_monte_carlo_fields |
| REQ-V51-024-004 | 24 | P1 | PASS | probability of ruin | test_monte_carlo_fields |
| REQ-V51-024-005 | 24 | P1 | PASS | confidence intervals | test_monte_carlo_fields |
| REQ-V51-024-006 | 24 | P1 | PASS | losing streak distribution | test_monte_carlo_fields |
| REQ-V51-025-001 | 25 | P1 | PASS | Bölüm 25 (STRATEGY ROBUSTNESS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-025-002 | 25 | P1 | PASS | Sensitivity analysis oluştur. | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-026-001 | 26 | P1 | PASS | Bölüm 26 (STRATEGY ENSEMBLE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-026-002 | 26 | P1 | PASS | Mümkünse birden fazla strateji oluştur: | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-026-003 | 26 | P1 | PASS | Trend Following | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-026-004 | 26 | P1 | PASS | Breakout | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-026-005 | 26 | P1 | PASS | Pullback | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-026-006 | 26 | P1 | PASS | Mean Reversion | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-026-007 | 26 | P1 | PASS | Momentum | test_phase109_strategy_ensemble_has_declared_families_and_requires_bounded_agreement |
| REQ-V51-027-001 | 27 | P1 | PASS | Bölüm 27 (MODEL HEALTH) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-027-002 | 27 | P1 | PASS | outcome | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-027-003 | 27 | P1 | PASS | return | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-027-004 | 27 | P1 | PASS | time to TP | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-027-005 | 27 | P1 | PASS | time to SL | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-027-006 | 27 | P1 | PASS | sakla. | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-027-007 | 27 | P1 | PASS | 7d / 30d / 90d performans raporu oluştur. | test_health_threshold_configurable |
| REQ-V51-027-008 | 27 | P1 | PASS | durumu oluştur. | test_phase110_model_health_outcomes_store_outcome_return_and_time_to_tp_sl_and_detect_degradation |
| REQ-V51-028-001 | 28 | P0 | PASS | Bölüm 28 (TELEGRAM) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_telegram_bot_api_sends_message_without_exposing_token_in_payload |
| REQ-V51-028-002 | 28 | P0 | PASS | Telegram Bot API kullan. | test_telegram_bot_api_sends_message_without_exposing_token_in_payload |
| REQ-V51-029-001 | 29 | P0 | PASS | Bölüm 29 (DASHBOARD / ANA KULLANICI EKRANI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-002 | 29 | P0 | PASS | Kullanıcı Redis, worker, container, coroutine, raw WebSocket event veya internal exception adı bilmek zorunda olmamalı. Teknik ayrıntı gerektiğinde ayrı "Gelişmiş / Sistem Sağlığı" ekranında gösterilsin. | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-003 | 29 | P0 | PASS | seçili sembolün canlı fiyatı | test_dashboard_endpoint_exposes_user_facing_operational_snapshot |
| REQ-V51-029-004 | 29 | P0 | PASS | PAPER / TESTNET / LIVE modu çok belirgin | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-005 | 29 | P0 | PASS | exchange bağlantısı | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-006 | 29 | P0 | PASS | canlı veri durumu ve son veri yaşı | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-007 | 29 | P0 | PASS | trading engine durumu | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-008 | 29 | P0 | PASS | risk durumu | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-009 | 29 | P0 | PASS | multi-asset market scanner / fırsat sıralaması | test_universe_scanner_metadata_and_breadth |
| REQ-V51-029-010 | 29 | P0 | PASS | top candidates | test_universe_scanner_metadata_and_breadth |
| REQ-V51-029-011 | 29 | P0 | PASS | current signal / confidence / net edge | test_universe_scanner_metadata_and_breadth |
| REQ-V51-029-012 | 29 | P0 | PASS | market regime | test_universe_scanner_metadata_and_breadth |
| REQ-V51-029-013 | 29 | P0 | PASS | açık pozisyonlar | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-014 | 29 | P0 | PASS | portfolio exposure | test_dashboard_frontend_contract_contains_required_user_facing_sections |
| REQ-V51-029-015 | 29 | P0 | PASS | günlük P&L ve drawdown | test_dashboard_frontend_contract_contains_required_user_facing_sections |
| REQ-V51-029-016 | 29 | P0 | PASS | aktif emirler | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-017 | 29 | P0 | PASS | kritik uyarılar | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-018 | 29 | P0 | PASS | son işlemler / sinyaller | test_dashboard_endpoint_exposes_user_facing_operational_snapshot |
| REQ-V51-029-019 | 29 | P0 | PASS | system health özeti | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-020 | 29 | P0 | PASS | Sistem güvenli ve sağlıklı mı? | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-021 | 29 | P0 | PASS | Şu anda hangi fırsatlar var ve neden? | test_universe_scanner_metadata_and_breadth |
| REQ-V51-029-022 | 29 | P0 | PASS | Açık riskim / pozisyonum ne durumda? | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-023 | 29 | P0 | PASS | "Canlı Veri: Aktif — son güncelleme 0.4 sn önce" | test_dashboard_endpoint_exposes_user_facing_operational_snapshot |
| REQ-V51-029-024 | 29 | P0 | PASS | "Yeni işlemler durduruldu — Binance verisi gecikiyor" | test_dashboard_snapshot_is_user_facing_and_fail_closed |
| REQ-V51-029-025 | 29 | P0 | PASS | "Pozisyon korunuyor — exchange üzerindeki stop emri doğrulandı" | test_dashboard_never_claims_position_protection_without_exchange_confirmation |
| REQ-V51-030-001 | 30 | P0 | PASS | Bölüm 30 (DATABASE SCHEMA) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_database_schema_contract_has_financial_and_operational_tables_registered |
| REQ-V51-030-002 | 30 | P0 | PASS | Her işlem immutable audit log'a sahip olmalı. | test_schema_creates_expected_tables |
| REQ-V51-031-001 | 31 | P0 | PASS | Bölüm 31 (AUDIT LOG) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_database_audit_detects_tampering |
| REQ-V51-031-002 | 31 | P0 | PASS | neden sinyal oluştu | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-003 | 31 | P0 | PASS | hangi indikatörler etkiledi | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-004 | 31 | P0 | PASS | hangi parametreler kullanıldı | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-005 | 31 | P0 | PASS | hangi fiyat vardı | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-006 | 31 | P0 | PASS | hangi veri timestamp'i kullanıldı | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-007 | 31 | P0 | PASS | hangi risk hesaplandı | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-008 | 31 | P0 | PASS | neden emir gönderildi | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-009 | 31 | P0 | PASS | exchange ne cevap verdi | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-031-010 | 31 | P0 | PASS | hangi universe snapshot içinde symbol eligible idi | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-031-011 | 31 | P0 | PASS | symbol metadata/filter version neydi | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-031-012 | 31 | P0 | PASS | portfolio correlation/concentration durumu neydi | test_decision_evidence_captures_signal_indicators_parameters_price_time_risk_order_exchange_and_portfolio |
| REQ-V51-032-001 | 32 | P0 | PASS | Bölüm 32 (SECURITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-032-002 | 32 | P0 | PASS | Git'e koyma | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-032-003 | 32 | P0 | PASS | Docker image içine koyma | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-032-004 | 32 | P0 | PASS | frontend'e gönderme | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-032-005 | 32 | P0 | PASS | loglama | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-032-006 | 32 | P0 | PASS | `.env` `.gitignore` içinde olmalı. | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-032-007 | 32 | P0 | PASS | API key permission validation yap. | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-033-001 | 33 | P0 | PASS | Bölüm 33 (RATE LIMIT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_rate_budget_reset_and_reserve |
| REQ-V51-033-002 | 33 | P0 | PASS | Exchange rate limits takip edilmeli. | test_rate_budget_reset_and_reserve |
| REQ-V51-033-003 | 33 | P0 | PASS | exponential backoff | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-033-004 | 33 | P0 | PASS | retry | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-033-005 | 33 | P0 | PASS | jitter | test_public_stream_reconnects_with_backoff_then_processes_event |
| REQ-V51-033-006 | 33 | P0 | PASS | kullan. | test_phase24_rate_limit_retry_uses_bounded_exponential_backoff_retry_and_jitter |
| REQ-V51-034-001 | 34 | P0 | PASS | Bölüm 34 (CLOCK SYNC) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_runtime_readiness_requires_health_db_redis_exchange_clock_reconciliation_and_outbox |
| REQ-V51-035-001 | 35 | P0 | PASS | Bölüm 35 (FEES & SLIPPAGE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_paper_market_partial_fill_models_fee_slippage_and_latency |
| REQ-V51-035-002 | 35 | P0 | PASS | trading fee | test_paper_market_partial_fill_models_fee_slippage_and_latency |
| REQ-V51-035-003 | 35 | P0 | PASS | slippage | test_paper_market_partial_fill_models_fee_slippage_and_latency |
| REQ-V51-035-004 | 35 | P0 | PASS | spread | test_paper_market_partial_fill_models_fee_slippage_and_latency |
| REQ-V51-036-001 | 36 | P0 | PASS | Bölüm 36 (DATABASE FAILURE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_database_account_snapshot_survives_process_state |
| REQ-V51-037-001 | 37 | P0 | PASS | Bölüm 37 (EXCHANGE FAILURE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects |
| REQ-V51-037-002 | 37 | P0 | PASS | yeni işlem açma | test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects |
| REQ-V51-037-003 | 37 | P0 | PASS | açık pozisyonların koruma emirlerini kontrol et | test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects |
| REQ-V51-037-004 | 37 | P0 | PASS | Telegram alarmı gönder | test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects |
| REQ-V51-037-005 | 37 | P0 | PASS | reconnect dene | test_exchange_failure_halts_new_risk_checks_protection_alerts_and_reconnects |
| REQ-V51-038-001 | 38 | P0 | PASS | Bölüm 38 (EMERGENCY STOP) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close |
| REQ-V51-038-002 | 38 | P0 | PASS | Emergency stop fonksiyonu oluştur. | test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close |
| REQ-V51-038-003 | 38 | P0 | PASS | yeni emirleri engeller | test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close |
| REQ-V51-038-004 | 38 | P0 | PASS | mümkünse koruyucu stopları silmez | test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close |
| REQ-V51-038-005 | 38 | P0 | PASS | açık pozisyonları otomatik kapatma kararını config'e bırakır | test_emergency_stop_policy_preserves_protective_orders_and_configures_position_close |
| REQ-V51-038-006 | 38 | P0 | PASS | Panic close ayrı fonksiyon olmalı. | test_panic_close_is_separate_human_approved_action |
| REQ-V51-039-001 | 39 | P0 | PASS | Bölüm 39 (CONFIG) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults |
| REQ-V51-039-002 | 39 | P0 | PASS | Aşağıdaki parametreler config üzerinden değiştirilebilir olmalı: | test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults |
| REQ-V51-040-001 | 40 | P0 | PASS | Bölüm 40 (HEALTH CHECK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_prod_health_is_fail_closed_when_probes_are_unconfigured |
| REQ-V51-040-002 | 40 | P0 | PASS | endpointleri oluştur. | test_prod_health_is_fail_closed_when_probes_are_unconfigured |
| REQ-V51-040-003 | 40 | P0 | PASS | database | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-004 | 40 | P0 | PASS | redis | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-005 | 40 | P0 | PASS | exchange | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-006 | 40 | P0 | PASS | websocket | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-007 | 40 | P0 | PASS | data freshness | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-008 | 40 | P0 | PASS | trading engine | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-009 | 40 | P0 | PASS | telegram | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-010 | 40 | P0 | PASS | strategy engine | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-011 | 40 | P0 | PASS | universe freshness | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-040-012 | 40 | P0 | PASS | scanner cycle health | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-040-013 | 40 | P0 | PASS | eligible symbol count | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-040-014 | 40 | P0 | PASS | stale/blocked symbol count | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-040-015 | 40 | P0 | PASS | portfolio concentration state | test_health_snapshot_is_fail_closed_for_all_operational_components |
| REQ-V51-041-001 | 41 | P0 | PASS | Bölüm 41 (OBSERVABILITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-041-002 | 41 | P0 | PASS | Grafana dashboard mümkünse oluştur. | test_grafana_dashboard_is_provisioned_with_real_health_panels |
| REQ-V51-042-001 | 42 | P0 | PASS | Bölüm 42 (TESTLER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_test_suite_has_required_local_safety_and_recovery_categories |
| REQ-V51-042-002 | 42 | P0 | PASS | indicator calculations | test_mandatory_indicator_feature_set_is_finite |
| REQ-V51-042-003 | 42 | P0 | PASS | signal scoring | test_signal_explainability |
| REQ-V51-042-004 | 42 | P0 | PASS | position sizing | test_seeded_position_sizing_never_exceeds_risk_budget |
| REQ-V51-042-005 | 42 | P0 | PASS | SL calculation | test_signal_stop_take_profit_and_risk_reward_calculation_are_explicit |
| REQ-V51-042-006 | 42 | P0 | PASS | TP calculation | test_signal_stop_take_profit_and_risk_reward_calculation_are_explicit |
| REQ-V51-042-007 | 42 | P0 | PASS | risk calculation | test_position_risk_calculation_returns_positive_bounded_quantity |
| REQ-V51-042-008 | 42 | P0 | PASS | database | test_schema_creates_expected_tables |
| REQ-V51-042-009 | 42 | P0 | NOT_TESTED | redis |  |
| REQ-V51-042-010 | 42 | P0 | PASS | exchange mock | test_idempotent_submit |
| REQ-V51-042-011 | 42 | P0 | PASS | telegram mock | test_telegram_bot_api_sends_message_without_exposing_token_in_payload |
| REQ-V51-042-012 | 42 | P0 | PASS | duplicate order | test_idempotent_submit |
| REQ-V51-042-013 | 42 | P0 | PASS | stale data | test_stale |
| REQ-V51-042-014 | 42 | P0 | PASS | exchange disconnect | test_fatal_circuit_conditions |
| REQ-V51-042-015 | 42 | P0 | PASS | database disconnect | test_schema_creates_expected_tables |
| REQ-V51-042-016 | 42 | P0 | PASS | rate limit | test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed |
| REQ-V51-042-017 | 42 | P0 | PASS | rejected order | test_phase23_rejected_order_is_terminal_and_not_retried_as_duplicate |
| REQ-V51-042-018 | 42 | P0 | PASS | partial fill | test_paper_market_partial_fill_models_fee_slippage_and_latency |
| REQ-V51-042-019 | 42 | P0 | PASS | restart recovery | test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates |
| REQ-V51-042-020 | 42 | P0 | PASS | clock drift | test_fatal_circuit_conditions |
| REQ-V51-042-021 | 42 | P0 | PASS | daily loss | test_fatal_circuit_conditions |
| REQ-V51-042-022 | 42 | P0 | PASS | max drawdown | test_fatal_circuit_conditions |
| REQ-V51-042-023 | 42 | P0 | PASS | no look-ahead | test_next_bar_entry_and_costs |
| REQ-V51-042-024 | 42 | P0 | PASS | no future leakage | test_time_alignment_never_uses_future_higher_timeframe_candle |
| REQ-V51-042-025 | 42 | P0 | PASS | fee calculation | test_backtest_fee_slippage_future_leakage_and_stop_execution_contracts |
| REQ-V51-042-026 | 42 | P0 | PASS | slippage | test_backtest_fee_slippage_future_leakage_and_stop_execution_contracts |
| REQ-V51-042-027 | 42 | P0 | PASS | stop execution | test_backtest_fee_slippage_future_leakage_and_stop_execution_contracts |
| REQ-V51-043-001 | 43 | P0 | NOT_TESTED | Bölüm 43 (TESTNET) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-043-002 | 43 | P0 | NOT_TESTED | market order |  |
| REQ-V51-043-003 | 43 | P0 | NOT_TESTED | limit order |  |
| REQ-V51-043-004 | 43 | P0 | NOT_TESTED | cancel |  |
| REQ-V51-043-005 | 43 | P0 | NOT_TESTED | partial fill |  |
| REQ-V51-044-001 | 44 | P0 | PASS | Bölüm 44 (SELF TEST) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_selftest_never_promotes_unconfigured_external_dependency_to_pass |
| REQ-V51-044-002 | 44 | P0 | PASS | Environment | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-003 | 44 | P0 | PASS | API credentials | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-004 | 44 | P0 | PASS | Exchange connectivity | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-005 | 44 | P0 | PASS | Exchange permissions | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-006 | 44 | P0 | PASS | Server time | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-007 | 44 | P0 | PASS | Database | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-008 | 44 | P0 | PASS | Redis | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-009 | 44 | P0 | PASS | Telegram | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-010 | 44 | P0 | PASS | WebSocket | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-011 | 44 | P0 | PASS | Data freshness | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-012 | 44 | P0 | PASS | Risk configuration | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-013 | 44 | P0 | PASS | Strategy configuration | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-014 | 44 | P0 | PASS | Disk space | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-015 | 44 | P0 | PASS | Memory | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-044-016 | 44 | P0 | PASS | Docker services | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-045-001 | 45 | P0 | PASS | Bölüm 45 (AUTOMATIC REGRESSION TEST) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-046-001 | 46 | P0 | NOT_TESTED | Bölüm 46 (DOCKER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-046-002 | 46 | P0 | PASS | docker-compose.yml oluştur. | test_base_compose_is_pinned_and_postgres18_volume_is_correct |
| REQ-V51-047-001 | 47 | P0 | PASS | Bölüm 47 (INSTALL / FIRST-RUN EXPERIENCE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-002 | 47 | P0 | PASS | oluştur. | test_phase25_install_scripts_exist_for_windows_and_linux_and_linux_is_executable |
| REQ-V51-047-003 | 47 | P0 | PASS | Docker / container runtime kontrolü | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-004 | 47 | P0 | PASS | gerekli runtime/dependency kontrolü | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-005 | 47 | P0 | PASS | secure config/.env bootstrap | test_production_secret_bootstrap_rejects_missing_mock_and_default_secret |
| REQ-V51-047-006 | 47 | P0 | PASS | database migration | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-007 | 47 | P0 | PASS | frontend production build | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-008 | 47 | P0 | PASS | backend self-test | test_selftest_never_promotes_unconfigured_external_dependency_to_pass |
| REQ-V51-047-009 | 47 | P0 | PASS | unit/integration smoke test | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-010 | 47 | P0 | PASS | health/ready check | test_install_scripts_fail_fast_and_include_build_migration_test_health_contract |
| REQ-V51-047-011 | 47 | P0 | PASS | başlangıç admin hesabı oluşturma akışı | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-047-012 | 47 | P0 | PASS | TLS / reverse proxy readiness kontrolü | test_install_and_deployment_contract_keeps_tls_and_first_start_paper |
| REQ-V51-047-013 | 47 | P0 | PASS | İlk açılışta GUI tabanlı FIRST-RUN WIZARD zorunlu: | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-047-014 | 47 | P0 | PASS | Sistem / server bağlantısı | test_prod_health_is_fail_closed_when_probes_are_unconfigured |
| REQ-V51-047-015 | 47 | P0 | PASS | Exchange API bağlantısı ve permission testi | test_selftest_passes_only_when_all_required_checks_are_explicitly_green |
| REQ-V51-047-016 | 47 | P0 | PASS | Telegram bağlantısı ve test bildirimi | test_telegram_bot_api_sends_message_without_exposing_token_in_payload |
| REQ-V51-047-017 | 47 | P0 | PASS | PAPER / TESTNET / LIVE modu seçimi; default PAPER | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-047-018 | 47 | P0 | PASS | Risk profili | test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults |
| REQ-V51-047-019 | 47 | P0 | PASS | Coin evreni / otomatik uygunluk seçimi | test_risk_and_runtime_parameters_are_configurable_with_conservative_defaults |
| REQ-V51-047-020 | 47 | P0 | PASS | Saat dilimi / bildirim tercihleri | test_phase23_setup_preferences_validate_iana_timezone_and_notification_booleans |
| REQ-V51-047-021 | 47 | P0 | PASS | Son güvenlik kontrolü ve özet | test_wizard_requires_final_preflight_and_forces_paper |
| REQ-V51-047-022 | 47 | P0 | PASS | Secret alanları maskeli olmalı; secret tekrar ekrana yazdırılmamalı. | test_production_secret_bootstrap_rejects_missing_mock_and_default_secret |
| REQ-V51-048-001 | 48 | P0 | PASS | Bölüm 48 (README) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-002 | 48 | P0 | PASS | Eksiksiz README oluştur. | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-003 | 48 | P0 | PASS | sistem mimarisi | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-004 | 48 | P0 | PASS | kurulum | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-005 | 48 | P0 | PASS | Binance API oluşturma | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-006 | 48 | P0 | PASS | API permission ayarları | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-007 | 48 | P0 | PASS | Telegram bot oluşturma | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-008 | 48 | P0 | PASS | environment variables | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-009 | 48 | P0 | PASS | Docker | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-010 | 48 | P0 | PASS | backtest | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-011 | 48 | P0 | PASS | paper trading | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-012 | 48 | P0 | PASS | testnet | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-013 | 48 | P0 | PASS | live trading | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-014 | 48 | P0 | PASS | risk yönetimi | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-015 | 48 | P0 | PASS | troubleshooting | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-016 | 48 | P0 | PASS | database backup | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-017 | 48 | P0 | PASS | disaster recovery | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-018 | 48 | P0 | PASS | kullanıcı kılavuzu | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-019 | 48 | P0 | PASS | ilk kurulum sihirbazı | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-020 | 48 | P0 | PASS | masaüstü istemci kurulumu (varsa) | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-021 | 48 | P0 | PASS | mobil/PWA kullanım | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-048-022 | 48 | P0 | PASS | PAPER / TESTNET / LIVE ekran farkları | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-023 | 48 | P0 | PASS | güvenli LIVE geçiş prosedürü | test_readme_and_operator_docs_cover_install_modes_risk_backup_and_recovery |
| REQ-V51-048-024 | 48 | P0 | PASS | kullanıcı dostu hata/uyarı sözlüğü | test_readme_contains_first_run_exchange_telegram_environment_and_error_guidance |
| REQ-V51-049-001 | 49 | P0 | PASS | Bölüm 49 (BACKUP) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_backup_dr_policy_is_explicit_but_restore_drill_evidence_cannot_be_faked |
| REQ-V51-049-002 | 49 | P0 | PASS | PostgreSQL backup script oluştur. | test_backup_restore_scripts_are_encrypted_integrity_checked_and_fail_fast |
| REQ-V51-049-003 | 49 | P0 | PASS | Database restore prosedürü oluştur. | test_backup_restore_scripts_are_encrypted_integrity_checked_and_fail_fast |
| REQ-V51-050-001 | 50 | P0 | PASS | Bölüm 50 (DISASTER RECOVERY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_backup_dr_policy_is_explicit_but_restore_drill_evidence_cannot_be_faked |
| REQ-V51-050-002 | 50 | P0 | PASS | yeniden başla | test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection |
| REQ-V51-050-003 | 50 | P0 | PASS | database'i oku | test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection |
| REQ-V51-050-004 | 50 | P0 | PASS | exchange'den gerçek pozisyonları çek | test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection |
| REQ-V51-050-005 | 50 | P0 | PASS | karşılaştır | test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection |
| REQ-V51-050-006 | 50 | P0 | PASS | reconciliation yap | test_database_account_snapshot_survives_process_state |
| REQ-V51-050-007 | 50 | P0 | PASS | açık pozisyonları tanı | test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection |
| REQ-V51-050-008 | 50 | P0 | PASS | koruyucu emirleri kontrol et | test_database_account_snapshot_survives_process_state |
| REQ-V51-050-009 | 50 | P0 | PASS | güvenli şekilde devam et | test_operator_recovery_never_resumes_active_without_human_approval, test_operator_recovery_runbook_requires_db_exchange_reconcile_risk_and_protection |
| REQ-V51-051-001 | 51 | P0 | PASS | Bölüm 51 (LIVE TRADING SAFETY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_defaults_paper |
| REQ-V51-051-002 | 51 | P0 | PASS | LIVE modu varsayılan olmayacak. | test_defaults_paper |
| REQ-V51-051-003 | 51 | P0 | PASS | zorunlu. | test_live_full_gate |
| REQ-V51-051-004 | 51 | P0 | PASS | minimum win rate | test_live_blocked_when_evidence_missing |
| REQ-V51-051-005 | 51 | P0 | PASS | minimum profit factor | test_live_blocked_when_evidence_missing |
| REQ-V51-051-006 | 51 | P0 | PASS | maximum drawdown | test_live_blocked_when_evidence_missing |
| REQ-V51-051-007 | 51 | P0 | PASS | minimum Sharpe | test_live_blocked_when_evidence_missing |
| REQ-V51-051-008 | 51 | P0 | PASS | minimum expectancy | test_live_blocked_when_evidence_missing |
| REQ-V51-051-009 | 51 | P0 | PASS | KRİTİK EK KURAL: | test_phase26_hundred_correlated_trades_are_not_treated_as_independent_live_evidence |
| REQ-V51-051-010 | 51 | P0 | PASS | minimum etkin örnek büyüklüğü (autocorrelation dikkate alınarak), | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-051-011 | 51 | P0 | PASS | yeterli takvim süresi, | test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence |
| REQ-V51-051-012 | 51 | P0 | PASS | birden fazla piyasa rejimi, | test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence |
| REQ-V51-051-013 | 51 | P0 | PASS | yeterli long/exit/short örneği (aktif market type'a göre), | test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence |
| REQ-V51-051-014 | 51 | P0 | PASS | maliyet ve latency stresleri, | test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence |
| REQ-V51-051-015 | 51 | P0 | PASS | bağımsız out-of-sample dönem, | test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence |
| REQ-V51-051-016 | 51 | P0 | PASS | execution divergence limiti | test_phase26_paper_campaign_requires_duration_multiple_regimes_direction_examples_stresses_oos_and_divergence |
| REQ-V51-052-001 | 52 | P1 | PASS | Bölüm 52 (STRATEGY SELECTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-002 | 52 | P1 | PASS | return | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-003 | 52 | P1 | PASS | drawdown | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-004 | 52 | P1 | PASS | Sharpe | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-005 | 52 | P1 | PASS | Sortino | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-006 | 52 | P1 | PASS | profit factor | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-007 | 52 | P1 | PASS | stability | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-008 | 52 | P1 | PASS | number of trades | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-052-009 | 52 | P1 | PASS | out-of-sample performance | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-053-001 | 53 | P1 | PASS | Bölüm 53 (NO GUARANTEED PROFIT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase111_strategy_selection_ranks_return_drawdown_sharpe_sortino_profit_factor_stability_and_trade_count_without_profit_guarantee |
| REQ-V51-054-001 | 54 | P1 | PASS | Bölüm 54 (SELF-LEARNING KONUSU) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes |
| REQ-V51-054-002 | 54 | P1 | PASS | geçmiş sinyal sonuçlarını analiz etmek | test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes |
| REQ-V51-054-003 | 54 | P1 | PASS | model performansını ölçmek | test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes |
| REQ-V51-054-004 | 54 | P1 | PASS | parametre önerileri oluşturmak | test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes |
| REQ-V51-054-005 | 54 | P1 | PASS | strategy degradation tespit etmek | test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes |
| REQ-V51-054-006 | 54 | P1 | PASS | paper test önermek | test_phase111_self_learning_analyzes_history_measures_degradation_and_only_proposes_paper_validated_non_live_parameter_changes |
| REQ-V51-055-001 | 55 | P1 | PASS | Bölüm 55 (AI / ML OPSİYONEL KATMAN) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-002 | 55 | P1 | PASS | feature store | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-003 | 55 | P1 | PASS | training dataset | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-004 | 55 | P1 | PASS | train/test split | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-005 | 55 | P1 | PASS | walk-forward validation | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-006 | 55 | P1 | PASS | model versioning | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-007 | 55 | P1 | PASS | feature importance | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-008 | 55 | P1 | PASS | drift detection | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-055-009 | 55 | P1 | PASS | olmalı. | test_phase111_ml_contract_has_point_in_time_training_dataset_split_versioning_importance_and_drift_detection |
| REQ-V51-056-001 | 56 | P1 | PASS | Bölüm 56 (SIGNAL DECISION PIPELINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations |
| REQ-V51-057-001 | 57 | P1 | PASS | Bölüm 57 (SIGNAL SNAPSHOT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations |
| REQ-V51-058-001 | 58 | P1 | PASS | Bölüm 58 (DUPLICATE SIGNAL PROTECTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations |
| REQ-V51-058-002 | 58 | P1 | PASS | Signal fingerprint oluştur. | test_idempotent_submit |
| REQ-V51-059-001 | 59 | P1 | PASS | Bölüm 59 (POSITION MANAGEMENT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances |
| REQ-V51-059-002 | 59 | P1 | PASS | Şunları takip et: | test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances |
| REQ-V51-059-003 | 59 | P1 | PASS | unrealized PnL | test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances |
| REQ-V51-059-004 | 59 | P1 | PASS | current R | test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances |
| REQ-V51-059-005 | 59 | P1 | PASS | distance to SL | test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances |
| REQ-V51-059-006 | 59 | P1 | PASS | distance to TP | test_phase111_position_management_exposes_unrealized_pnl_current_r_stop_and_take_profit_distances |
| REQ-V51-059-007 | 59 | P1 | PASS | volatility | test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp |
| REQ-V51-059-008 | 59 | P1 | PASS | trend change | test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp |
| REQ-V51-059-009 | 59 | P1 | PASS | trailing stop | test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp |
| REQ-V51-059-010 | 59 | P1 | PASS | partial TP | test_phase123_position_management_tracks_volatility_trend_trailing_stop_and_partial_tp |
| REQ-V51-060-001 | 60 | P1 | PASS | Bölüm 60 (TELEGRAM CONFIRMATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations |
| REQ-V51-060-002 | 60 | P1 | PASS | AUTO_EXECUTION varsayılan: | test_phase123_signal_pipeline_snapshot_duplicate_and_confirmation_sections_have_real_implementations |
| REQ-V51-061-001 | 61 | P1 | PASS | Bölüm 61 (PROJECT STRUCTURE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase123_project_structure_is_cleanly_split_and_api_surface_is_versioned |
| REQ-V51-061-002 | 61 | P1 | PASS | Aşağıdakine benzer temiz bir yapı oluştur: | test_phase123_project_structure_is_cleanly_split_and_api_surface_is_versioned |
| REQ-V51-062-001 | 62 | P1 | PASS | Bölüm 62 (API ENDPOINTS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase123_project_structure_is_cleanly_split_and_api_surface_is_versioned |
| REQ-V51-063-001 | 63 | P1 | PASS | Bölüm 63 (FRONTEND / PRODUCT UI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-002 | 63 | P1 | PASS | Frontend bir "debug paneli" değil, son kullanıcının günlük kullanacağı profesyonel ürün olmalı. | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-003 | 63 | P1 | PASS | React + TypeScript | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-004 | 63 | P1 | PASS | responsive desktop/tablet/mobile tasarım | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-005 | 63 | P1 | PASS | erişilebilir component kullanımı | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-006 | 63 | P1 | PASS | dark/light theme desteği | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-007 | 63 | P1 | PASS | Türkçe öncelikli i18n altyapısı; metinleri component içine dağınık hard-code etme | test_phase125_turkish_first_i18n_centralizes_shell_strings |
| REQ-V51-063-008 | 63 | P1 | PASS | route-level error boundary | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-009 | 63 | P1 | PASS | loading / empty / stale / error / unauthorized state'leri | test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded |
| REQ-V51-063-010 | 63 | P1 | PASS | REST initial snapshot + authenticated WebSocket incremental updates | test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup |
| REQ-V51-063-011 | 63 | P1 | PASS | server trading state source-of-truth | test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup |
| REQ-V51-063-012 | 63 | P1 | PASS | frontend refresh veya kapanması trading engine'i etkilememeli | test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup |
| REQ-V51-063-013 | 63 | P1 | PASS | Ana Ekran | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-014 | 63 | P1 | PASS | Piyasa / Coin Tarayıcı | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-015 | 63 | P1 | PASS | Analiz | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-016 | 63 | P1 | PASS | Pozisyonlar & Emirler | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-017 | 63 | P1 | PASS | Alarmlar | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-018 | 63 | P1 | PASS | Backtest & Araştırma | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-019 | 63 | P1 | PASS | Performans & Risk | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-020 | 63 | P1 | PASS | Ayarlar / Sistem | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-021 | 63 | P1 | PASS | LIVE / PAPER / TESTNET modu üst bar veya kalıcı shell içinde her zaman görünür olmalı. | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-022 | 63 | P1 | PASS | LIVE modunda yalnızca renk değil, açık "GERÇEK PARA" etiketi kullan. | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-023 | 63 | P1 | PASS | aktif universe ve hariç bırakılma gerekçeleri | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-024 | 63 | P1 | PASS | liquidity/spread/volume filtre durumu | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-025 | 63 | P1 | PASS | top candidate ranking | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-026 | 63 | P1 | PASS | asset bazlı signal/score/confidence | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-027 | 63 | P1 | PASS | korelasyon heatmap veya sade korelasyon matrisi | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-028 | 63 | P1 | PASS | cluster/tema konsantrasyonu | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-029 | 63 | P1 | PASS | quote-asset exposure | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-030 | 63 | P1 | PASS | per-symbol data health | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-031 | 63 | P1 | PASS | listing age / new-listing risk badge | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-032 | 63 | P1 | PASS | delisting/suspension uyarısı | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-033 | 63 | P1 | PASS | Signal | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-034 | 63 | P1 | PASS | Entry | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-035 | 63 | P1 | PASS | TP1/TP2/TP3 | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-036 | 63 | P1 | PASS | risk amount + risk percent | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-037 | 63 | P1 | PASS | Confidence | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-038 | 63 | P1 | PASS | Reasons | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-039 | 63 | P1 | PASS | Risks | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-040 | 63 | P1 | PASS | data timestamp | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-041 | 63 | P1 | PASS | mode | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-063-042 | 63 | P1 | PASS | Kullanıcı tek ekrandan yüzlerce coine toplu LIVE emir gönderen tehlikeli bir "TRADE ALL" aksiyonuna sahip olmamalı. | test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible |
| REQ-V51-064-001 | 64 | P1 | PASS | Bölüm 64 (ERROR HANDLING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase122_error_handling_has_human_message_action_correlation_and_critical_alert_channel |
| REQ-V51-064-002 | 64 | P1 | PASS | kullanıcıya uygun kısa mesaj | test_phase122_error_handling_has_human_message_action_correlation_and_critical_alert_channel |
| REQ-V51-064-003 | 64 | P1 | PASS | kullanıcı için önerilen aksiyon | test_phase122_error_handling_has_human_message_action_correlation_and_critical_alert_channel |
| REQ-V51-064-004 | 64 | P1 | PASS | teknik detay için correlation ID | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-064-005 | 64 | P1 | PASS | structured log | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-064-006 | 64 | P1 | PASS | gerekiyorsa Telegram kritik alarm | test_phase122_error_handling_has_human_message_action_correlation_and_critical_alert_channel |
| REQ-V51-065-001 | 65 | P1 | NOT_TESTED | Bölüm 65 (FINAL ACCEPTANCE TEST) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-065-002 | 65 | P1 | NOT_TESTED | docker compose build |  |
| REQ-V51-065-003 | 65 | P1 | NOT_TESTED | docker compose up -d |  |
| REQ-V51-065-004 | 65 | P1 | NOT_TESTED | migrations |  |
| REQ-V51-065-005 | 65 | P1 | PASS | pytest | test_local_test_evidence_requires_git_bound_shard_and_log_hashes |
| REQ-V51-065-006 | 65 | P1 | PASS | health check | test_health |
| REQ-V51-065-007 | 65 | P1 | NOT_TESTED | paper trading |  |
| REQ-V51-065-008 | 65 | P1 | PASS | historical backtest | test_phase109_backtest_performance_metrics_are_complete_and_consistent |
| REQ-V51-065-009 | 65 | P1 | PASS | walk-forward | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-065-010 | 65 | P1 | PASS | Monte Carlo | test_phase109_walkforward_purge_monte_carlo_and_sensitivity_are_deterministic_oos_tools |
| REQ-V51-065-011 | 65 | P1 | PASS | Telegram test | test_telegram_bot_api_sends_message_without_exposing_token_in_payload |
| REQ-V51-065-012 | 65 | P1 | NOT_TESTED | exchange testnet bağlantısı |  |
| REQ-V51-065-013 | 65 | P1 | PASS | multi-symbol universe/scanner smoke test | test_universe_scanner_metadata_and_breadth |
| REQ-V51-065-014 | 65 | P1 | PASS | official exchange API capability/filter/rate-limit contract verification | test_phase26_official_binance_reference_is_date_stamped_and_runtime_capability_remains_source_of_truth |
| REQ-V51-065-015 | 65 | P1 | PASS | Her testin sonucunu raporla. | test_local_test_evidence_requires_git_bound_shard_and_log_hashes |
| REQ-V51-066-001 | 66 | P1 | PASS | Bölüm 66 (TESLİM FORMATI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-002 | 66 | P1 | PASS | bütün source code | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-003 | 66 | P1 | PASS | Dockerfile | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-004 | 66 | P1 | PASS | docker-compose.yml | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-005 | 66 | P1 | PASS | .env.example | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-006 | 66 | P1 | PASS | requirements.txt veya pyproject.toml | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-007 | 66 | P1 | PASS | Alembic migrations | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-008 | 66 | P1 | PASS | database schema | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-009 | 66 | P1 | PASS | backend | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-010 | 66 | P1 | PASS | frontend | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-011 | 66 | P1 | PASS | Telegram bot | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-012 | 66 | P1 | PASS | exchange adapter | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-013 | 66 | P1 | PASS | backtest engine | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-014 | 66 | P1 | PASS | paper trading | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-015 | 66 | P1 | PASS | testnet | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-016 | 66 | P1 | PASS | risk engine | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-017 | 66 | P1 | PASS | signal engine | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-018 | 66 | P1 | PASS | dashboard | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-019 | 66 | P1 | PASS | tests | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-020 | 66 | P1 | PASS | install scripts | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-021 | 66 | P1 | PASS | backup scripts | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-022 | 66 | P1 | PASS | README | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-023 | 66 | P1 | PASS | troubleshooting | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-066-024 | 66 | P1 | PASS | architecture documentation | test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs |
| REQ-V51-067-001 | 67 | P1 | PASS | Bölüm 67 (ÇALIŞMAYAN KOD YASAK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase122_real_api_absence_uses_explicit_mock_adapter_and_never_fakes_unsupported_capability |
| REQ-V51-067-002 | 67 | P1 | PASS | Gerçek API bulunmayan yerde interface + mock/sandbox implementasyonu yap. | test_phase122_real_api_absence_uses_explicit_mock_adapter_and_never_fakes_unsupported_capability |
| REQ-V51-068-001 | 68 | P1 | PASS | Bölüm 68 (GERÇEK API CREDENTIAL YOKSA) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase122_real_api_absence_uses_explicit_mock_adapter_and_never_fakes_unsupported_capability |
| REQ-V51-069-001 | 69 | P1 | PASS | Bölüm 69 (PERFORMANCE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts |
| REQ-V51-069-002 | 69 | P1 | PASS | WebSocket kullan. | test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts |
| REQ-V51-069-003 | 69 | P1 | PASS | Redis cache kullan. | test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts |
| REQ-V51-069-004 | 69 | P1 | PASS | Candle aggregation yap. | test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts |
| REQ-V51-069-005 | 69 | P1 | PASS | Log rotation uygula. | test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts |
| REQ-V51-069-006 | 69 | P1 | PASS | Memory leak kontrolü yap. | test_phase128_local_mock_soak_has_bounded_retained_memory_growth |
| REQ-V51-070-001 | 70 | P1 | PASS | Bölüm 70 (DOCUMENTATION OF ASSUMPTIONS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions |
| REQ-V51-070-002 | 70 | P1 | PASS | matematiksel mantığını | test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions |
| REQ-V51-070-003 | 70 | P1 | PASS | giriş şartlarını | test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions |
| REQ-V51-070-004 | 70 | P1 | PASS | çıkış şartlarını | test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions |
| REQ-V51-070-005 | 70 | P1 | PASS | risk şartlarını | test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions |
| REQ-V51-070-006 | 70 | P1 | PASS | başarısızlık durumlarını | test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions |
| REQ-V51-071-001 | 71 | P0 | PASS | Bölüm 71 (SAYISAL DOĞRULUK / PARA HESAPLARI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_financial_rounding_is_directional_not_builtin_round |
| REQ-V51-071-002 | 71 | P0 | PASS | Exchange'den gelen price/quantity değerlerini Decimal veya exchange-native fixed precision yaklaşımıyla işle. | test_seeded_step_normalization_multiple |
| REQ-V51-071-003 | 71 | P0 | PASS | Emir gönderilmeden önce price tickSize'a, quantity stepSize'a uygun normalize edilmeli. | test_seeded_step_normalization_multiple |
| REQ-V51-071-004 | 71 | P0 | PASS | Yuvarlama yönü işleme göre bilinçli seçilmeli; "round()" ile kör yuvarlama yapılmamalı. | test_financial_rounding_is_directional_not_builtin_round |
| REQ-V51-071-005 | 71 | P0 | PASS | Hesaplanan emir, normalize edildikten sonra risk kurallarını yeniden geçmeli. | test_seeded_step_normalization_multiple |
| REQ-V51-071-006 | 71 | P0 | PASS | Normalize sonrası R/R, stop distance veya risk oranı bozuluyorsa emir iptal edilmeli. | test_seeded_step_normalization_multiple |
| REQ-V51-071-007 | 71 | P0 | PASS | NaN, Infinity, negative-zero ve division-by-zero kontrolleri yapılmalı. | test_seeded_step_normalization_multiple |
| REQ-V51-071-008 | 71 | P0 | PASS | Tüm finansal değerlerin unit/currency bilgisi açık olmalı. | test_seeded_step_normalization_multiple |
| REQ-V51-072-001 | 72 | P0 | PASS | Bölüm 72 (MARKET TYPE / SPOT - PERPETUAL - FUTURES AYRIMI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_safe_default_market_type_is_spot |
| REQ-V51-072-002 | 72 | P0 | PASS | Sistem MARKET_TYPE kavramına sahip olmalı. | test_safe_default_market_type_is_spot |
| REQ-V51-072-003 | 72 | P0 | PASS | Varsayılan ilk güvenli profil: | test_safe_default_market_type_is_spot |
| REQ-V51-072-004 | 72 | P0 | PASS | mevcut bakiyeden fazla SELL yapılamaz, | test_execution_service_enforces_spot_sell_balance_before_exchange_side_effect |
| REQ-V51-072-005 | 72 | P0 | PASS | leverage/liquidation/funding yoktur, | test_spot_forbids_liquidation_leverage_semantics_and_enforces_concentration |
| REQ-V51-072-006 | 72 | P0 | PASS | position kavramı balance/lot bazlı ele alınır. | test_spot_forbids_liquidation_leverage_semantics_and_enforces_concentration |
| REQ-V51-072-007 | 72 | P0 | PASS | long/short | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-008 | 72 | P0 | PASS | leverage | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-009 | 72 | P0 | PASS | isolated/cross margin | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-010 | 72 | P0 | PASS | one-way/hedge mode | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-011 | 72 | P0 | PASS | mark price | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-012 | 72 | P0 | PASS | index price | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-013 | 72 | P0 | PASS | liquidation price | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-014 | 72 | P0 | PASS | maintenance margin | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-015 | 72 | P0 | PASS | funding rate | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-016 | 72 | P0 | PASS | funding payment | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-017 | 72 | P0 | PASS | reduce-only | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-018 | 72 | P0 | PASS | position side | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-072-019 | 72 | P0 | PASS | leverage bracket | test_derivative_market_requires_liquidation_margin_and_leverage_buffers |
| REQ-V51-073-001 | 73 | P0 | PASS | Bölüm 73 (EXCHANGE CAPABILITY DISCOVERY VE SYMBOL FILTERS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-002 | 73 | P0 | PASS | Her exchange ve symbol için runtime capability discovery yap. | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-003 | 73 | P0 | PASS | supported order types | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-004 | 73 | P0 | PASS | market/limit | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-005 | 73 | P0 | PASS | stop | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-006 | 73 | P0 | PASS | take profit | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-007 | 73 | P0 | PASS | trailing stop | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-008 | 73 | P0 | PASS | OCO/order list | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-009 | 73 | P0 | PASS | post-only | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-010 | 73 | P0 | PASS | reduce-only | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-011 | 73 | P0 | PASS | time-in-force: GTC/IOC/FOK | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-012 | 73 | P0 | PASS | client order id | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-013 | 73 | P0 | PASS | testnet | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-014 | 73 | P0 | PASS | user/private stream | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-015 | 73 | P0 | PASS | order book depth | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-016 | 73 | P0 | PASS | amend/cancel-replace | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-017 | 73 | P0 | PASS | precision mode | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-018 | 73 | P0 | PASS | min/max price | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-019 | 73 | P0 | PASS | tick size | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-020 | 73 | P0 | PASS | min/max quantity | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-021 | 73 | P0 | PASS | step size | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-022 | 73 | P0 | PASS | min/max notional | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-023 | 73 | P0 | PASS | max open orders | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-024 | 73 | P0 | PASS | exchange/account limits | test_phase21_exchange_capability_profile_covers_oco_depth_cancel_replace_precision_price_and_limits |
| REQ-V51-073-025 | 73 | P0 | PASS | Periyodik refresh ve "filter changed" tespiti yap. | test_symbol_filter_change_between_validation_and_submit_fails_closed |
| REQ-V51-073-026 | 73 | P0 | PASS | PRICE_FILTER | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-027 | 73 | P0 | PASS | LOT_SIZE | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-028 | 73 | P0 | PASS | MARKET_LOT_SIZE | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-029 | 73 | P0 | PASS | MIN_NOTIONAL / NOTIONAL | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-030 | 73 | P0 | PASS | quantity precision | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-031 | 73 | P0 | PASS | price precision | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-032 | 73 | P0 | PASS | order count limits | test_capabilities_are_discovered_not_assumed |
| REQ-V51-073-033 | 73 | P0 | PASS | kontrol edilmeli. | test_phase24_capability_filters_are_all_consistency_checked_fail_closed |
| REQ-V51-074-001 | 74 | P0 | PASS | Bölüm 74 (ORDER BOOK BÜTÜNLÜĞÜ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-002 | 74 | P0 | PASS | WebSocket delta eventlerini buffer et. | test_orderbook_delta |
| REQ-V51-074-003 | 74 | P0 | PASS | REST snapshot al. | test_orderbook_delta |
| REQ-V51-074-004 | 74 | P0 | PASS | snapshot lastUpdateId ile delta sequence'i eşleştir. | test_orderbook_delta |
| REQ-V51-074-005 | 74 | P0 | PASS | Eski eventleri at. | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-006 | 74 | P0 | PASS | Her yeni delta için update sequence continuity kontrol et. | test_orderbook_delta |
| REQ-V51-074-007 | 74 | P0 | PASS | Sequence gap varsa local book'u INVALID yap. | test_orderbook_delta |
| REQ-V51-074-008 | 74 | P0 | PASS | INVALID book ile order-flow sinyali veya execution kararı üretme. | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-009 | 74 | P0 | PASS | Snapshot + buffer ile yeniden senkronize et. | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-010 | 74 | P0 | PASS | Exchange checksum sağlıyorsa checksum doğrulaması da kullan. | test_phase23_orderbook_checksum_is_conditional_and_mismatch_invalidates_book |
| REQ-V51-074-011 | 74 | P0 | PASS | book age | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-012 | 74 | P0 | PASS | last update id | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-013 | 74 | P0 | PASS | best bid | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-014 | 74 | P0 | PASS | best ask | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-015 | 74 | P0 | PASS | spread | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-016 | 74 | P0 | PASS | crossed book | test_orderbook_delta |
| REQ-V51-074-017 | 74 | P0 | PASS | locked book | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-018 | 74 | P0 | PASS | depth imbalance | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-019 | 74 | P0 | PASS | update gap count | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-074-020 | 74 | P0 | PASS | resync count | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-075-001 | 75 | P0 | PASS | Bölüm 75 (PRIVATE USER DATA STREAM / FILL SOURCE OF TRUTH) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_private_stream_account_update_carries_position_and_balance_truth |
| REQ-V51-075-002 | 75 | P0 | PASS | order accepted | test_private_stream_projects_order_lifecycle_statuses |
| REQ-V51-075-003 | 75 | P0 | PASS | order changed | test_private_stream_projects_order_lifecycle_statuses |
| REQ-V51-075-004 | 75 | P0 | PASS | partial fill | test_private_stream_projects_order_lifecycle_statuses |
| REQ-V51-075-005 | 75 | P0 | PASS | fill | test_private_stream_projects_order_lifecycle_statuses |
| REQ-V51-075-006 | 75 | P0 | PASS | cancel | test_private_stream_projects_order_lifecycle_statuses |
| REQ-V51-075-007 | 75 | P0 | PASS | reject | test_private_stream_projects_order_lifecycle_statuses |
| REQ-V51-075-008 | 75 | P0 | PASS | balance | test_balance_snapshot |
| REQ-V51-075-009 | 75 | P0 | PASS | position | test_private_stream_account_update_carries_position_and_balance_truth |
| REQ-V51-075-010 | 75 | P0 | PASS | yeni risk artırıcı emirler durdurulmalı, | test_private_stream_termination_is_explicit_unknown_risk_boundary |
| REQ-V51-075-011 | 75 | P0 | PASS | açık emir/pozisyonlar REST ile reconcile edilmeli, | test_composite_reconciliation_requires_balance_positions_open_orders_and_local_database_checks |
| REQ-V51-075-012 | 75 | P0 | PASS | durum UNKNOWN ise LIVE işlem yapılmamalı. | test_private_stream_termination_is_explicit_unknown_risk_boundary |
| REQ-V51-076-001 | 76 | P0 | PASS | Bölüm 76 (IDEMPOTENCY / BELİRSİZ EMİR SONUCU) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews |
| REQ-V51-076-002 | 76 | P0 | PASS | ACCEPTED/KNOWN | test_durable_intent_idempotency_survives_service_restart_without_duplicate_submit |
| REQ-V51-076-003 | 76 | P0 | PASS | REJECTED/KNOWN | test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed |
| REQ-V51-076-004 | 76 | P0 | PASS | UNKNOWN | test_ambiguous_durable_intent_is_not_blindly_retried_after_restart |
| REQ-V51-076-005 | 76 | P0 | PASS | UNKNOWN kritik durumdur. | test_ambiguous_becomes_unknown |
| REQ-V51-076-006 | 76 | P0 | PASS | kör retry yapma, | test_ambiguous_becomes_unknown |
| REQ-V51-076-007 | 76 | P0 | PASS | önce client_order_id ile order sorgula, | test_durable_submitted_intent_reconciles_by_client_order_id_before_any_resubmit |
| REQ-V51-076-008 | 76 | P0 | PASS | user stream'i kontrol et, | test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews |
| REQ-V51-076-009 | 76 | P0 | PASS | open orders/fills ile reconcile et, | test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews |
| REQ-V51-076-010 | 76 | P0 | PASS | sonuç kesinleşmeden yeni aynı emir gönderme. | test_ambiguous_becomes_unknown |
| REQ-V51-076-011 | 76 | P0 | PASS | At-least-once event delivery + idempotent handler yaklaşımı kullan. | test_private_stream_duplicate_order_event_is_idempotent |
| REQ-V51-077-001 | 77 | P0 | PASS | Bölüm 77 (ORDER RACE CONDITION VE ORPHAN ORDER KORUMASI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_replace_race_ack_loss_is_unknown_until_reconciled |
| REQ-V51-077-002 | 77 | P0 | PASS | cancel gönderildiği sırada fill gelmesi | test_cancel_pending_can_receive_late_fill_without_illegal_state |
| REQ-V51-077-003 | 77 | P0 | PASS | cancel timeout ama order'ın gerçekte cancel olması | test_cancel_timeout_applies_terminal_exchange_truth |
| REQ-V51-077-004 | 77 | P0 | PASS | cancel timeout ama order'ın hâlâ live olması | test_cancel_timeout_applies_terminal_exchange_truth |
| REQ-V51-077-005 | 77 | P0 | PASS | replace/amend sırasında eski order'ın fill olması | test_replace_race_detects_old_fill_and_overlapping_orders |
| REQ-V51-077-006 | 77 | P0 | PASS | late fill | test_cancel_pending_can_receive_late_fill_without_illegal_state |
| REQ-V51-077-007 | 77 | P0 | PASS | duplicate fill event | test_duplicate_fill_idempotent |
| REQ-V51-077-008 | 77 | P0 | PASS | out-of-order order event | test_private_stream_stale_order_event_cannot_regress_projection |
| REQ-V51-077-009 | 77 | P0 | PASS | partial fill sonrası restart | test_partial_fill_is_reconstructed_from_committed_fills_after_restart |
| REQ-V51-077-010 | 77 | P0 | PASS | TP ile SL'nin aynı anda tetiklenmeye yaklaşması | test_cancel_pending_can_receive_late_fill_without_illegal_state |
| REQ-V51-077-011 | 77 | P0 | PASS | bağlantı koptuğu sırada order acknowledgement alınamaması | test_replace_race_ack_loss_is_unknown_until_reconciled |
| REQ-V51-078-001 | 78 | P0 | PASS | Bölüm 78 (CANDLE FINALITY / TIME ALIGNMENT / WARMUP) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_time_alignment_rejects_naive_or_nonfinal_and_separates_open_close_time |
| REQ-V51-078-002 | 78 | P0 | PASS | Varsayılan: | test_phase25_closed_candle_only_is_explicit_safe_default |
| REQ-V51-078-003 | 78 | P0 | PASS | olmalı. | test_phase25_closed_candle_only_is_explicit_safe_default |
| REQ-V51-078-004 | 78 | P0 | PASS | yüksek timeframe verisini geleceğe sızdırma, | test_time_alignment_never_uses_future_higher_timeframe_candle |
| REQ-V51-078-005 | 78 | P0 | PASS | candle open time ile close time'ı karıştırma, | test_time_alignment_rejects_naive_or_nonfinal_and_separates_open_close_time |
| REQ-V51-078-006 | 78 | P0 | PASS | timezone farkı üretme. | test_time_alignment_rejects_naive_or_nonfinal_and_separates_open_close_time |
| REQ-V51-078-007 | 78 | P0 | PASS | Süre ölçümlerinde mümkün olduğunca monotonic clock kullan. | test_monotonic_timer_rejects_clock_regression |
| REQ-V51-078-008 | 78 | P0 | PASS | Ayrıca "recursive indicator stability test" oluştur: | test_recursive_indicator_stability_with_sufficient_warmup |
| REQ-V51-079-001 | 79 | P0 | PASS | Bölüm 79 (BACKTEST EXECUTION REALISM / INTRABAR BELİRSİZLİK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative |
| REQ-V51-079-002 | 79 | P0 | PASS | daha düşük timeframe verisi | test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative |
| REQ-V51-079-003 | 79 | P0 | PASS | trade/tick data | test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative |
| REQ-V51-079-004 | 79 | P0 | PASS | order book data | test_phase22_intrabar_resolution_prioritizes_lower_timeframe_then_tick_then_orderbook_and_falls_back_conservative |
| REQ-V51-079-005 | 79 | P0 | PASS | açıkça tanımlanmış konservatif intrabar fill policy | test_conservative_intrabar_chooses_stop_when_stop_and_tp_both_touch |
| REQ-V51-079-006 | 79 | P0 | PASS | Konservatif mod varsayılan olmalı. | test_conservative_intrabar_chooses_stop_when_stop_and_tp_both_touch |
| REQ-V51-079-007 | 79 | P0 | PASS | market order her zaman candle close'dan fill olmuş sayılmamalı, | test_market_fill_is_next_bar_open_with_slippage_and_versioned |
| REQ-V51-079-008 | 79 | P0 | PASS | limit order sadece fiyat "dokundu" diye garanti fill sayılmamalı, | test_limit_touch_is_not_guaranteed_fill_and_queue_liquidity_can_block |
| REQ-V51-079-009 | 79 | P0 | PASS | queue position/liquidity modeli mümkün olduğunda kullanılmalı, | test_limit_touch_is_not_guaranteed_fill_and_queue_liquidity_can_block |
| REQ-V51-079-010 | 79 | P0 | PASS | gap/slippage etkisi dikkate alınmalı, | test_stop_gap_through_never_assumes_guaranteed_stop_price |
| REQ-V51-079-011 | 79 | P0 | PASS | stop gap-through durumunda stop fiyatından garantili fill varsayılmamalı. | test_stop_gap_through_never_assumes_guaranteed_stop_price |
| REQ-V51-079-012 | 79 | P0 | PASS | Backtest execution model VERSIONED olmalı. | test_market_fill_is_next_bar_open_with_slippage_and_versioned |
| REQ-V51-080-001 | 80 | P0 | PASS | Bölüm 80 (LIQUIDITY / MARKET IMPACT / EXECUTION QUALITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_execution_quality_includes_market_impact |
| REQ-V51-080-002 | 80 | P0 | PASS | quoted spread | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-003 | 80 | P0 | PASS | effective spread | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-004 | 80 | P0 | PASS | realized slippage | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-005 | 80 | P0 | PASS | expected slippage | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-006 | 80 | P0 | PASS | fill ratio | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-007 | 80 | P0 | PASS | partial fill ratio | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-008 | 80 | P0 | PASS | cancel ratio | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-009 | 80 | P0 | PASS | order reject ratio | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-010 | 80 | P0 | PASS | time-to-ack | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-011 | 80 | P0 | PASS | time-to-fill | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-012 | 80 | P0 | PASS | market impact | test_execution_quality_includes_market_impact |
| REQ-V51-080-013 | 80 | P0 | PASS | adverse selection | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-014 | 80 | P0 | PASS | maker/taker ratio | test_execution_quality_reports_cost_fill_latency_and_adverse_selection |
| REQ-V51-080-015 | 80 | P0 | PASS | gerektiğinde available liquidity ve expected slippage'a da bağlı olmalı. | test_execution_quality_reports_cost_fill_latency_and_adverse_selection, test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-080-016 | 80 | P0 | PASS | oluştur. | test_phase24_execution_quality_score_is_bounded_and_penalizes_cost_liquidity_rejects |
| REQ-V51-081-001 | 81 | P0 | PASS | Bölüm 81 (PRE-TRADE FAT-FINGER VE PRICE COLLAR) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_execution_service_enforces_spot_sell_balance_before_exchange_side_effect |
| REQ-V51-081-002 | 81 | P0 | PASS | Her order için risk motoru son kapı olmalı. | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-081-003 | 81 | P0 | PASS | max order notional | test_pretrade_rejects_notional_quantity_position_balance_and_exchange_price |
| REQ-V51-081-004 | 81 | P0 | PASS | max quantity | test_pretrade_rejects_notional_quantity_position_balance_and_exchange_price |
| REQ-V51-081-005 | 81 | P0 | PASS | max position notional | test_pretrade_rejects_notional_quantity_position_balance_and_exchange_price |
| REQ-V51-081-006 | 81 | P0 | PASS | price deviation from reference | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-081-007 | 81 | P0 | PASS | spread limit | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-081-008 | 81 | P0 | PASS | slippage estimate | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-081-009 | 81 | P0 | PASS | stale reference price | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-081-010 | 81 | P0 | PASS | min/max exchange filter | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-081-011 | 81 | P0 | PASS | side sanity | test_pretrade_rejects_invalid_side_and_trading_state |
| REQ-V51-081-012 | 81 | P0 | PASS | reduce-only sanity | test_reduce_only_sanity_is_inside_final_pretrade_gate |
| REQ-V51-081-013 | 81 | P0 | PASS | available balance/margin | test_pretrade_rejects_notional_quantity_position_balance_and_exchange_price |
| REQ-V51-081-014 | 81 | P0 | PASS | duplicate intent | test_durable_intent_id_collision_with_different_symbol_fails_closed_without_submit |
| REQ-V51-081-015 | 81 | P0 | PASS | trading state | test_pretrade_rejects_invalid_side_and_trading_state |
| REQ-V51-081-016 | 81 | P0 | PASS | symbol trading status | test_pretrade_rejects_fat_finger_stale_spread_slippage_and_symbol_state |
| REQ-V51-082-001 | 82 | P0 | PASS | Bölüm 82 (PROTECTIVE ORDER GARANTİSİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_protective_supervisor_restricts_retries_and_alerts_when_unprotected |
| REQ-V51-082-002 | 82 | P0 | PASS | gerçekten exchange tarafından ACKNOWLEDGED edilmeden "koruma aktif" sayılmamalı. | test_protective_state_requires_exchange_ack_before_claiming_protected |
| REQ-V51-082-003 | 82 | P0 | PASS | synthetic/local stop kullanılıyorsa bunun bot/network bağımlı olduğu açıkça işaretlenmeli. | test_protective_state_requires_exchange_ack_before_claiming_protected |
| REQ-V51-082-004 | 82 | P0 | PASS | UNPROTECTED_POSITION durumu oluştur. | test_protective_state_requires_exchange_ack_before_claiming_protected |
| REQ-V51-082-005 | 82 | P0 | PASS | yeni işlem açma, | test_protective_supervisor_restricts_retries_and_alerts_when_unprotected |
| REQ-V51-082-006 | 82 | P0 | PASS | tekrar protective order kurmayı dene, | test_protective_supervisor_restricts_retries_and_alerts_when_unprotected |
| REQ-V51-082-007 | 82 | P0 | PASS | kullanıcıyı alarm ile bilgilendir, | test_protective_supervisor_restricts_retries_and_alerts_when_unprotected |
| REQ-V51-082-008 | 82 | P0 | PASS | configured policy'e göre REDUCING_ONLY veya PANIC_CLOSE uygulanabilsin. | test_unprotected_position_blocks_new_risk_and_selects_safe_action |
| REQ-V51-082-009 | 82 | P0 | PASS | Default policy güvenli ve konservatif olmalı. | test_unprotected_position_blocks_new_risk_and_selects_safe_action |
| REQ-V51-083-001 | 83 | P0 | PASS | Bölüm 83 (PERPETUAL / MARGIN EK RİSK MOTORU) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-002 | 83 | P0 | PASS | max leverage | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-003 | 83 | P0 | PASS | leverage per symbol | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-004 | 83 | P0 | PASS | liquidation distance | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-005 | 83 | P0 | PASS | maintenance margin ratio | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-006 | 83 | P0 | PASS | margin ratio | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-007 | 83 | P0 | PASS | funding rate | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-008 | 83 | P0 | PASS | funding timestamp | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-009 | 83 | P0 | PASS | expected funding cost | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-010 | 83 | P0 | PASS | mark/index divergence | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-011 | 83 | P0 | PASS | open interest | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-012 | 83 | P0 | PASS | liquidation spike | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-013 | 83 | P0 | PASS | reduce-only enforcement | test_perpetual_reduce_only_enforcement_rejects_position_increase, test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-014 | 83 | P0 | PASS | kontrol et. | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-083-015 | 83 | P0 | PASS | Varsayılan: | test_perpetual_risk_engine_checks_leverage_liquidation_margin_funding_mark_oi_and_spikes |
| REQ-V51-084-001 | 84 | P0 | PASS | Bölüm 84 (ORDER FLOW / MICROSTRUCTURE OPSİYONEL KATMANI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-002 | 84 | P0 | PASS | bid/ask spread | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-003 | 84 | P0 | PASS | order book imbalance | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-004 | 84 | P0 | PASS | depth imbalance | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-005 | 84 | P0 | PASS | microprice | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-006 | 84 | P0 | PASS | trade aggressor side | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-007 | 84 | P0 | PASS | buy/sell volume delta | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-008 | 84 | P0 | PASS | cumulative volume delta | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-009 | 84 | P0 | PASS | short-term order-flow momentum | test_microstructure_extracts_spread_imbalance_microprice_delta_cvd_and_momentum |
| REQ-V51-084-010 | 84 | P0 | PASS | abnormal sweep | test_microstructure_detects_abnormal_sweep_and_liquidity_vacuum |
| REQ-V51-084-011 | 84 | P0 | PASS | liquidity vacuum | test_microstructure_detects_abnormal_sweep_and_liquidity_vacuum |
| REQ-V51-085-001 | 85 | P0 | PASS | Bölüm 85 (STRATEGY LIFECYCLE / PROMOTION PIPELINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-002 | 85 | P0 | PASS | Her aşama için gate oluştur. | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-003 | 85 | P0 | PASS | strategy_version | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-004 | 85 | P0 | PASS | config_hash | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-005 | 85 | P0 | PASS | git_commit_sha | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-006 | 85 | P0 | PASS | dataset_version | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-007 | 85 | P0 | PASS | indicator_version | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-008 | 85 | P0 | PASS | execution_model_version | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-085-009 | 85 | P0 | PASS | risk_model_version | test_strategy_promotion_is_sequential_and_provenance_manifest_is_complete |
| REQ-V51-086-001 | 86 | P0 | PASS | Bölüm 86 (ADVANCED RESEARCH VALIDATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-002 | 86 | P0 | PASS | Zorunlu değerlendirmeler: | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-003 | 86 | P0 | PASS | in-sample | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-004 | 86 | P0 | PASS | out-of-sample | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-005 | 86 | P0 | PASS | walk-forward | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-006 | 86 | P0 | PASS | fee sensitivity | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-007 | 86 | P0 | PASS | slippage sensitivity | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-008 | 86 | P0 | PASS | latency sensitivity | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-009 | 86 | P0 | PASS | parameter sensitivity | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-010 | 86 | P0 | PASS | regime breakdown | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-011 | 86 | P0 | PASS | bull/bear/range breakdown | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-012 | 86 | P0 | PASS | benchmark comparison | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-013 | 86 | P0 | PASS | trade count sufficiency | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-014 | 86 | P0 | PASS | Probabilistic Sharpe Ratio | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-015 | 86 | P0 | PASS | Deflated Sharpe Ratio | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-016 | 86 | P0 | PASS | bootstrap confidence intervals | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-086-017 | 86 | P0 | PASS | multiple-testing / data-snooping kontrolü | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-087-001 | 87 | P0 | PASS | Bölüm 87 (SIGNAL CONFIDENCE CALIBRATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-002 | 87 | P0 | PASS | Confidence skoru keyfi "84%" olmamalı. | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-003 | 87 | P0 | PASS | geçmiş benzer sinyallerin sonucu | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-004 | 87 | P0 | PASS | out-of-sample doğrulama | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-005 | 87 | P0 | PASS | regime uyumu | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-006 | 87 | P0 | PASS | feature completeness | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-007 | 87 | P0 | PASS | data quality | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-008 | 87 | P0 | PASS | model calibration | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-009 | 87 | P0 | PASS | reliability/calibration curve | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-010 | 87 | P0 | PASS | Brier score veya uygun calibration metric | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-011 | 87 | P0 | PASS | confidence bucket performance | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-087-012 | 87 | P0 | PASS | takip edilmeli. | test_confidence_is_oos_calibrated_and_penalized_by_regime_features_and_data_quality |
| REQ-V51-088-001 | 88 | P0 | PASS | Bölüm 88 (EVENT-DRIVEN CORE / DETERMINISTIC REPLAY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift |
| REQ-V51-088-002 | 88 | P0 | PASS | immutable id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-088-003 | 88 | P0 | PASS | event timestamp | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-088-004 | 88 | P0 | PASS | received timestamp | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-088-005 | 88 | P0 | PASS | correlation id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-088-006 | 88 | P0 | PASS | causation id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-088-007 | 88 | P0 | PASS | sequence | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-088-008 | 88 | P0 | PASS | Kritik production olayı sonradan replay edilebilmeli. | test_replay_sequence |
| REQ-V51-089-001 | 89 | P0 | PASS | Bölüm 89 (CONCURRENCY / SINGLE LEADER / SPLIT-BRAIN KORUMASI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_live_submit_revalidates_fencing_immediately_at_exchange_side_effect_boundary |
| REQ-V51-089-002 | 89 | P0 | PASS | Aynı account için iki trading engine instance'ının eşzamanlı emir göndermesini engelle. | test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-089-003 | 89 | P0 | PASS | single active leader | test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-089-004 | 89 | P0 | PASS | lease/lock | test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-089-005 | 89 | P0 | PASS | fencing token veya eşdeğer split-brain koruması | test_live_submit_revalidates_fencing_immediately_at_exchange_side_effect_boundary, test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-089-006 | 89 | P0 | PASS | instance_id | test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-089-007 | 89 | P0 | PASS | heartbeat | test_persistent_leader_heartbeat_extends_same_token_and_expired_lease_cannot_renew |
| REQ-V51-090-001 | 90 | P0 | PASS | Bölüm 90 (BACKPRESSURE / EVENT PRIORITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_market_data_coordinator_preserves_high_priority_under_backpressure |
| REQ-V51-090-002 | 90 | P0 | PASS | Bounded queue + backpressure politikası oluştur. | test_backpressure_prioritizes_private_event |
| REQ-V51-090-003 | 90 | P0 | PASS | Kritik eventler: | test_backpressure_prioritizes_private_event |
| REQ-V51-090-004 | 90 | P0 | PASS | order | test_backpressure_prioritizes_private_event |
| REQ-V51-090-005 | 90 | P0 | PASS | fill | test_backpressure_prioritizes_private_event |
| REQ-V51-090-006 | 90 | P0 | PASS | balance | test_backpressure_prioritizes_private_event |
| REQ-V51-090-007 | 90 | P0 | PASS | position | test_backpressure_prioritizes_private_event |
| REQ-V51-090-008 | 90 | P0 | PASS | risk | test_backpressure_prioritizes_private_event |
| REQ-V51-090-009 | 90 | P0 | PASS | circuit breaker | test_backpressure_prioritizes_private_event |
| REQ-V51-090-010 | 90 | P0 | PASS | Market-data eventleri yüksek yükte coalesce edilecekse bu davranış açık ve güvenli olmalı. | test_backpressure_prioritizes_private_event |
| REQ-V51-091-001 | 91 | P0 | PASS | Bölüm 91 (DATABASE INTEGRITY / LEDGER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-002 | 91 | P0 | PASS | Orders/fills/positions dışında gerçek finansal muhasebe için ledger yaklaşımı oluştur. | test_double_entry_integrity_balanced_per_asset |
| REQ-V51-091-003 | 91 | P0 | PASS | cash/balance changes | test_double_entry_integrity_balanced_per_asset |
| REQ-V51-091-004 | 91 | P0 | PASS | funding | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-005 | 91 | P0 | PASS | realized PnL | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-006 | 91 | P0 | PASS | unrealized PnL snapshot | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-007 | 91 | P0 | PASS | transfers if manually reconciled | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-008 | 91 | P0 | PASS | locked/available balance | test_double_entry_integrity_balanced_per_asset |
| REQ-V51-091-009 | 91 | P0 | PASS | takip edilsin. | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-010 | 91 | P0 | PASS | exchange + account + exchange_order_id | test_execution_referential_integrity_accepts_valid_order_fill_ledger |
| REQ-V51-091-011 | 91 | P0 | PASS | exchange + account + fill/trade_id | test_execution_referential_integrity_accepts_valid_order_fill_ledger |
| REQ-V51-091-012 | 91 | P0 | PASS | signal fingerprint where appropriate | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-013 | 91 | P0 | PASS | oluştur. | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-014 | 91 | P0 | PASS | partitioning | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-015 | 91 | P0 | PASS | retention | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-016 | 91 | P0 | PASS | archival | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-017 | 91 | P0 | PASS | compression opsiyonları | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-091-018 | 91 | P0 | PASS | TimescaleDB gibi ek dependency zorunlu olmasın; PostgreSQL native partitioning yeterli olabilir. | test_accounting_evidence_covers_funding_pnl_transfer_signal_and_lifecycle_policy |
| REQ-V51-092-001 | 92 | P0 | PASS | Bölüm 92 (TRANSACTIONAL CONSISTENCY / OUTBOX) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_outbox_failure_to_dlq |
| REQ-V51-092-002 | 92 | P0 | PASS | DB write ile mesaj/notification/event publish arasında tutarsızlık oluşmasını engellemek için transactional outbox veya eşdeğer güvenilir pattern kullan. | test_outbox_failure_to_dlq |
| REQ-V51-092-003 | 92 | P0 | PASS | DB'deki committed event kaybolmamalı, | test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure |
| REQ-V51-092-004 | 92 | P0 | PASS | yeniden publish edilebilmeli, | test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure |
| REQ-V51-092-005 | 92 | P0 | PASS | consumer idempotent olmalı. | test_idempotent_consumer_applies_duplicate_event_once_and_releases_failed_claim_for_retry |
| REQ-V51-092-006 | 92 | P0 | PASS | ancak kritik alarm teslim edilemiyorsa health status degraded olsun. | test_phase21_outbox_health_requires_committed_events_replayable_and_degrades_on_critical_delivery_failure |
| REQ-V51-093-001 | 93 | P0 | PASS | Bölüm 93 (API / DASHBOARD AUTHENTICATION & AUTHORIZATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-002 | 93 | P0 | PASS | authentication | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-003 | 93 | P0 | PASS | secure session/token | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-004 | 93 | P0 | PASS | RBAC | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-005 | 93 | P0 | PASS | admin/trader/viewer ayrımı | test_login_and_rbac |
| REQ-V51-093-006 | 93 | P0 | PASS | CORS allowlist | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-007 | 93 | P0 | PASS | CSRF koruması gerekiyorsa | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-008 | 93 | P0 | PASS | login rate limiting | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-009 | 93 | P0 | PASS | brute-force protection | test_phase21_login_throttle_is_bounded_and_clears_after_success |
| REQ-V51-093-010 | 93 | P0 | PASS | WebSocket authentication | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-011 | 93 | P0 | PASS | audit log for state-changing actions | test_mfa_reset_requires_admin_reauthentication_and_is_audited |
| REQ-V51-093-012 | 93 | P0 | PASS | HttpOnly + Secure + SameSite cookie veya eşdeğer güvenli session transport | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-093-013 | 93 | P0 | PASS | browser localStorage içinde exchange API secret/token saklama YASAK | test_secret_material_is_excluded_from_git_docker_frontend_and_logs |
| REQ-V51-093-014 | 93 | P0 | PASS | session revocation / inactivity timeout | test_bootstrap_single_use_login_cookie_and_csrf |
| REQ-V51-094-001 | 94 | P0 | PASS | Bölüm 94 (TELEGRAM SECURITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary |
| REQ-V51-094-002 | 94 | P0 | PASS | allowed chat/user id allowlist | test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off |
| REQ-V51-094-003 | 94 | P0 | PASS | state-changing komutlar varsayılan kapalı | test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off |
| REQ-V51-094-004 | 94 | P0 | PASS | /live için time-limited one-time confirmation nonce | test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary |
| REQ-V51-094-005 | 94 | P0 | PASS | replay protection | test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary |
| REQ-V51-094-006 | 94 | P0 | PASS | confirmation expiry | test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary |
| REQ-V51-094-007 | 94 | P0 | PASS | işlem özeti: symbol, side, max notional, mode | test_telegram_live_confirmation_is_time_limited_one_time_replay_protected_and_has_trade_summary |
| REQ-V51-094-008 | 94 | P0 | PASS | yanlış chat'ten gelen komutu reddet | test_telegram_allowlist_rejects_wrong_chat_and_user_and_state_changes_default_off |
| REQ-V51-094-009 | 94 | P0 | PASS | secret/token mesajlarda gösterilmesin | test_secret_masking_never_echoes_plain_secret |
| REQ-V51-095-001 | 95 | P0 | PASS | Bölüm 95 (SECRET MANAGEMENT / HOST SECURITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_production_secret_bootstrap_rejects_missing_mock_and_default_secret |
| REQ-V51-095-002 | 95 | P0 | PASS | Production için destekle: | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-003 | 95 | P0 | PASS | Docker secrets veya | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-004 | 95 | P0 | PASS | OS secret store veya | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-005 | 95 | P0 | PASS | Vault/KMS benzeri secret provider | test_production_secret_bootstrap_rejects_missing_mock_and_default_secret |
| REQ-V51-095-006 | 95 | P0 | PASS | IP allowlist mümkünse öner | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-007 | 95 | P0 | PASS | withdrawal disabled | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-095-008 | 95 | P0 | PASS | minimum permission | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-095-009 | 95 | P0 | PASS | ayrı TESTNET ve LIVE key | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-010 | 95 | P0 | PASS | key fingerprint göster, secret gösterme | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-095-011 | 95 | P0 | PASS | non-root user | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-095-012 | 95 | P0 | PASS | minimal base image | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-013 | 95 | P0 | PASS | no privileged mode | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-014 | 95 | P0 | PASS | Docker socket mount etme | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-015 | 95 | P0 | PASS | filesystem mümkün olduğunca read-only | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-095-016 | 95 | P0 | PASS | only required ports | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-017 | 95 | P0 | PASS | resource limits | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-095-018 | 95 | P0 | PASS | security_opt/capabilities hardening | test_credential_vault_encrypts_and_rejects_withdrawal |
| REQ-V51-095-019 | 95 | P0 | PASS | uygula. | test_production_container_security_contract_uses_secret_files_nonroot_minimal_images_no_privilege_socket_and_resource_limits |
| REQ-V51-096-001 | 96 | P0 | NOT_TESTED | Bölüm 96 (SUPPLY CHAIN / DEPENDENCY SECURITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-096-002 | 96 | P0 | NOT_TESTED | lock file kullan |  |
| REQ-V51-096-003 | 96 | P0 | PASS | direct dependencies pin'le | test_python_and_frontend_direct_dependencies_are_exactly_pinned |
| REQ-V51-096-004 | 96 | P0 | PASS | Docker base image'i version/digest ile sabitle | test_third_party_notices_exists_and_docker_build_base_images_are_digest_pinned |
| REQ-V51-096-005 | 96 | P0 | NOT_TESTED | vulnerability scan yap |  |
| REQ-V51-096-006 | 96 | P0 | PASS | secret scan yap | test_phase23_local_secret_scanner_executes_and_reports_zero_findings |
| REQ-V51-096-007 | 96 | P0 | PASS | SAST yap | test_local_sast_executes_and_has_no_high_or_critical_findings |
| REQ-V51-096-008 | 96 | P0 | PASS | SBOM üret | test_local_sbom_is_explicitly_unresolved_and_never_claims_supply_chain_acceptance |
| REQ-V51-096-009 | 96 | P0 | NOT_TESTED | dependency license raporu üret |  |
| REQ-V51-096-010 | 96 | P0 | NOT_TESTED | pip-audit |  |
| REQ-V51-096-011 | 96 | P0 | NOT_TESTED | Trivy |  |
| REQ-V51-096-012 | 96 | P0 | NOT_TESTED | gitleaks |  |
| REQ-V51-096-013 | 96 | P0 | NOT_TESTED | Bandit/Semgrep |  |
| REQ-V51-096-014 | 96 | P0 | PASS | CycloneDX veya SPDX | test_local_sbom_is_cyclonedx_1_6_but_remains_direct_only |
| REQ-V51-096-015 | 96 | P0 | PASS | THIRD_PARTY_NOTICES.md oluştur. | test_third_party_notices_exists_and_docker_build_base_images_are_digest_pinned |
| REQ-V51-097-001 | 97 | P0 | NOT_TESTED | Bölüm 97 (CI/CD / RELEASE GATES) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-097-002 | 97 | P0 | PASS | GitHub Actions veya eşdeğer CI oluştur. | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-003 | 97 | P0 | PASS | formatting | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-004 | 97 | P0 | PASS | ruff | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-005 | 97 | P0 | PASS | mypy | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-006 | 97 | P0 | PASS | unit tests | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-007 | 97 | P0 | PASS | integration tests | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-008 | 97 | P0 | PASS | safety tests | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-009 | 97 | P0 | PASS | no-lookahead test | test_ci_pytest_contract_includes_no_lookahead_and_recursive_indicator_guards |
| REQ-V51-097-010 | 97 | P0 | PASS | recursive-indicator stability test | test_ci_pytest_contract_includes_no_lookahead_and_recursive_indicator_guards |
| REQ-V51-097-011 | 97 | P0 | PASS | dependency/security scan | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-012 | 97 | P0 | PASS | secret scan | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-013 | 97 | P0 | PASS | Docker build | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-014 | 97 | P0 | PASS | migration test | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-097-015 | 97 | P0 | PASS | immutable version/tag | test_local_git_provenance_has_real_clean_commit_and_immutable_tag |
| REQ-V51-097-016 | 97 | P0 | PASS | git SHA | test_local_git_provenance_has_real_clean_commit_and_immutable_tag |
| REQ-V51-097-017 | 97 | P0 | PASS | build timestamp | test_phase23_release_identity_requires_real_provenance_for_production_and_manifest_has_timestamp |
| REQ-V51-097-018 | 97 | P0 | NOT_TESTED | dependency lock hash |  |
| REQ-V51-097-019 | 97 | P0 | PASS | SBOM | test_local_sbom_is_explicitly_unresolved_and_never_claims_supply_chain_acceptance |
| REQ-V51-097-020 | 97 | P0 | PASS | checksums | test_release_packaging_contract_is_content_addressed_and_writes_checksum_file |
| REQ-V51-097-021 | 97 | P0 | PASS | FAILED CI ile LIVE deploy yasak. | test_ci_workflow_is_fail_closed_and_covers_backend_frontend_docker_and_release_gate |
| REQ-V51-098-001 | 98 | P0 | PASS | Bölüm 98 (GRACEFUL SHUTDOWN / PROCESS LIFECYCLE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-002 | 98 | P0 | PASS | new entries stop | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-003 | 98 | P0 | PASS | scheduler stop | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-004 | 98 | P0 | PASS | in-flight order intents settle/reconcile | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-005 | 98 | P0 | PASS | open orders/positions snapshot | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-006 | 98 | P0 | PASS | DB flush | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-007 | 98 | P0 | PASS | pending outbox flush best-effort | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-008 | 98 | P0 | PASS | health state STOPPING | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-009 | 98 | P0 | PASS | clean shutdown | test_graceful_shutdown_orders_entry_scheduler_reconcile_snapshot_db_outbox_and_stopping |
| REQ-V51-098-010 | 98 | P0 | PASS | Hard crash sonrası restart reconciliation zorunlu. | test_database_account_snapshot_survives_process_state, test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates |
| REQ-V51-099-001 | 99 | P0 | NOT_TESTED | Bölüm 99 (ADVANCED TESTING / FAULT INJECTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-099-002 | 99 | P0 | PASS | position sizing hiçbir zaman risk limitini aşmıyor mu? | test_seeded_position_sizing_never_exceeds_risk_budget |
| REQ-V51-099-003 | 99 | P0 | PASS | normalize edilen quantity filter dışına çıkıyor mu? | test_seeded_step_normalization_multiple |
| REQ-V51-099-004 | 99 | P0 | PASS | reduce-only exposure artırabiliyor mu? | test_reduce_only_model_cannot_increase_absolute_exposure |
| REQ-V51-099-005 | 99 | P0 | PASS | random order event sequence state machine'i bozuyor mu? | test_illegal_transition |
| REQ-V51-099-006 | 99 | P0 | PASS | CREATED → ... → terminal states | test_illegal_transition |
| REQ-V51-099-007 | 99 | P0 | PASS | duplicate/out-of-order events | test_sequence_guard_rejects_duplicate_and_out_of_order_market_events |
| REQ-V51-099-008 | 99 | P0 | PASS | restart | test_restart_recovery_blocks_new_risk_until_reconciliation_human_approval_and_green_gates |
| REQ-V51-099-009 | 99 | P0 | PASS | WebSocket packet loss | test_public_stream_detects_depth_packet_gap_delay_and_clock_jump |
| REQ-V51-099-010 | 99 | P0 | PASS | duplicated event | test_sequence_guard_rejects_duplicate_and_out_of_order_market_events |
| REQ-V51-099-011 | 99 | P0 | PASS | delayed event | test_private_stream_stale_and_clock_regression_fail_closed, test_public_stream_detects_depth_packet_gap_delay_and_clock_jump |
| REQ-V51-099-012 | 99 | P0 | PASS | out-of-order event | test_sequence_guard_rejects_duplicate_and_out_of_order_market_events |
| REQ-V51-099-013 | 99 | P0 | PASS | REST timeout | test_phase23_rest_timeout_and_dns_failure_are_fail_closed_fault_contracts |
| REQ-V51-099-014 | 99 | P0 | PASS | DNS failure | test_phase23_rest_timeout_and_dns_failure_are_fail_closed_fault_contracts |
| REQ-V51-099-015 | 99 | P0 | NOT_TESTED | Redis restart |  |
| REQ-V51-099-016 | 99 | P0 | NOT_TESTED | PostgreSQL restart |  |
| REQ-V51-099-017 | 99 | P0 | PASS | disk full | test_disk_full_on_durability_critical_audit_write_halts_new_risk |
| REQ-V51-099-018 | 99 | P0 | PASS | clock jump | test_private_stream_stale_and_clock_regression_fail_closed, test_public_stream_detects_depth_packet_gap_delay_and_clock_jump |
| REQ-V51-099-019 | 99 | P0 | PASS | process kill -9 | test_committed_account_state_survives_abrupt_worker_exit |
| REQ-V51-099-020 | 99 | P0 | NOT_TESTED | kritik senaryolarını test et. |  |
| REQ-V51-100-001 | 100 | P0 | PASS | Bölüm 100 (DATASET VERSIONING / REPRODUCIBILITY / FINAL EVIDENCE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-002 | 100 | P0 | PASS | Her backtest için kullanılan veri tekrar üretilebilir olmalı. | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-003 | 100 | P0 | PASS | exchange | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-004 | 100 | P0 | PASS | symbol | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-005 | 100 | P0 | PASS | timeframe | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-006 | 100 | P0 | PASS | start/end | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-007 | 100 | P0 | PASS | source | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-008 | 100 | P0 | PASS | download timestamp | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-009 | 100 | P0 | PASS | candle count | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-010 | 100 | P0 | PASS | missing candle count | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-011 | 100 | P0 | PASS | checksum/hash | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-012 | 100 | P0 | PASS | preprocessing version | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-013 | 100 | P0 | PASS | sakla. | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-014 | 100 | P0 | PASS | strategy version | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-015 | 100 | P0 | PASS | config hash | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-016 | 100 | P0 | PASS | dataset hash | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-017 | 100 | P0 | PASS | code git SHA | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-018 | 100 | P0 | PASS | random seed | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-019 | 100 | P0 | PASS | execution model version | test_full_dataset_reproducibility_manifest_hashes_exact_rows_and_versions |
| REQ-V51-100-020 | 100 | P0 | PASS | benchmark buy-and-hold sonucu | test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet |
| REQ-V51-100-021 | 100 | P0 | PASS | fee/slippage stress sonucu | test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet |
| REQ-V51-100-022 | 100 | P0 | PASS | paper-vs-backtest farkı | test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet |
| REQ-V51-100-023 | 100 | P0 | PASS | testnet-vs-paper execution farkı | test_phase27_testnet_vs_paper_execution_difference_is_explicit_and_bounded |
| REQ-V51-100-024 | 100 | P0 | PASS | unresolved known issues | test_phase21_final_evidence_bundle_records_benchmark_cost_divergence_and_known_issues_without_faking_testnet |
| REQ-V51-101-001 | 101 | P1 | PASS | Bölüm 101 (RESEARCH / PROFITABILITY EXPANSION — LEGACY COMPATIBILITY / OVERRIDE RULE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-102-001 | 102 | P1 | PASS | Bölüm 102 (PRIMARY OBJECTIVE — NET EDGE / CAPITAL PRESERVATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-002 | 102 | P1 | PASS | Sistemin optimization objective'i "en yüksek brüt getiri" veya "en yüksek win rate" OLMAMALI. | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-003 | 102 | P1 | PASS | Sermayenin kalıcı kayıp riskini sınırlamak | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-004 | 102 | P1 | PASS | Veri ve execution doğruluğu | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-005 | 102 | P1 | PASS | Tail-risk / drawdown kontrolü | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-006 | 102 | P1 | PASS | Maliyet sonrası pozitif expectancy | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-007 | 102 | P1 | PASS | OOS istatistiksel güvenilirlik | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-008 | 102 | P1 | PASS | Canlı execution kalitesi | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-009 | 102 | P1 | PASS | Risk-adjusted net return | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-010 | 102 | P1 | PASS | Ancak bunlardan sonra trade count / win rate / brüt return | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-011 | 102 | P1 | PASS | trading_fees | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-012 | 102 | P1 | PASS | spread_cost | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-013 | 102 | P1 | PASS | realized_slippage | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-014 | 102 | P1 | PASS | funding_cost | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-015 | 102 | P1 | PASS | borrow_cost | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-102-016 | 102 | P1 | PASS | diğer doğrudan execution maliyetleri | test_phase103_capital_preservation_objective_gates_vanity_metrics_and_accounts_all_costs |
| REQ-V51-103-001 | 103 | P1 | PASS | Bölüm 103 (STRATEGY SPECIFICATION CONTRACT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-002 | 103 | P1 | PASS | Her strateji kodlanmadan önce machine-readable ve insan tarafından okunabilir StrategySpec oluştur. | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-003 | 103 | P1 | PASS | strategy_id | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-004 | 103 | P1 | PASS | strategy_version | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-005 | 103 | P1 | PASS | hypothesis | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-006 | 103 | P1 | PASS | supported_market_types | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-007 | 103 | P1 | PASS | supported_symbols | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-008 | 103 | P1 | PASS | allowed_direction | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-009 | 103 | P1 | PASS | required_timeframes | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-010 | 103 | P1 | PASS | required_features | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-011 | 103 | P1 | PASS | warmup | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-012 | 103 | P1 | PASS | valid_regimes | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-013 | 103 | P1 | PASS | invalid_regimes | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-014 | 103 | P1 | PASS | entry_rule | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-015 | 103 | P1 | PASS | confirmation_rule | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-016 | 103 | P1 | PASS | invalidation_rule | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-017 | 103 | P1 | PASS | exit_rule | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-018 | 103 | P1 | PASS | stop_rule | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-019 | 103 | P1 | PASS | take_profit_rule | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-020 | 103 | P1 | PASS | max_holding_time | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-021 | 103 | P1 | PASS | cooldown | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-022 | 103 | P1 | PASS | order_policy | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-023 | 103 | P1 | PASS | position_sizing_policy | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-024 | 103 | P1 | PASS | risk_limits | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-025 | 103 | P1 | PASS | assumptions | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-026 | 103 | P1 | PASS | known_failure_modes | test_phase103_strategy_spec_is_machine_and_human_readable_complete_contract |
| REQ-V51-103-027 | 103 | P1 | PASS | BUY = envanter/pozisyon artırma | test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit |
| REQ-V51-103-028 | 103 | P1 | PASS | SELL = mevcut spot envanteri azaltma/çıkış | test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit |
| REQ-V51-103-029 | 103 | P1 | PASS | SPOT SELL sinyali gizlice short açmamalı. | test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit |
| REQ-V51-103-030 | 103 | P1 | PASS | BUY/SELL ile open-long/open-short davranışı position side ve config ile açıkça tanımlanmalı. | test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit |
| REQ-V51-103-031 | 103 | P1 | PASS | ALLOW_SHORT varsayılan false olabilir; aktif edilirse ayrı validation gerektirir. | test_phase103_spot_sell_never_opens_short_and_buy_sell_semantics_are_explicit |
| REQ-V51-103-032 | 103 | P1 | PASS | Signal -> RiskApproved -> OrderIntent dönüşümü açık state transition olmalı. | test_phase103_signal_riskapproved_orderintent_transition_cannot_skip_risk |
| REQ-V51-104-001 | 104 | P1 | PASS | Bölüm 104 (RESEARCH HYPOTHESIS / TRIAL LEDGER / SELECTION BIAS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-002 | 104 | P1 | PASS | Immutable RESEARCH_TRIAL_LEDGER oluştur. | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-003 | 104 | P1 | PASS | trial_id | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-004 | 104 | P1 | PASS | hypothesis_id | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-005 | 104 | P1 | PASS | strategy family | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-006 | 104 | P1 | PASS | tested features | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-007 | 104 | P1 | PASS | tested parameters | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-008 | 104 | P1 | PASS | dataset hash | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-009 | 104 | P1 | PASS | train period | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-010 | 104 | P1 | PASS | validation period | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-011 | 104 | P1 | PASS | test period | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-012 | 104 | P1 | PASS | metrics | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-013 | 104 | P1 | PASS | failure reason | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-014 | 104 | P1 | PASS | selected / rejected | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-015 | 104 | P1 | PASS | researcher/agent | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-016 | 104 | P1 | PASS | timestamp | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-017 | 104 | P1 | PASS | sakla. | test_phase103_research_trial_ledger_is_append_only_hash_chained_and_complete |
| REQ-V51-104-018 | 104 | P1 | PASS | Pre-registration benzeri yaklaşım destekle: | test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget |
| REQ-V51-104-019 | 104 | P1 | PASS | hypothesis before result | test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget |
| REQ-V51-104-020 | 104 | P1 | PASS | primary metric before test | test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget |
| REQ-V51-104-021 | 104 | P1 | PASS | test set lock | test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget |
| REQ-V51-104-022 | 104 | P1 | PASS | parameter search budget | test_phase103_research_preregistration_locks_hypothesis_metric_testset_and_budget |
| REQ-V51-105-001 | 105 | P1 | PASS | Bölüm 105 (POINT-IN-TIME DATA / AVAILABILITY SEMANTICS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-002 | 105 | P1 | PASS | Mümkün olduğunda ayrı sakla: | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-003 | 105 | P1 | PASS | event_time | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-004 | 105 | P1 | PASS | exchange_time | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency, test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-005 | 105 | P1 | PASS | published_at | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-006 | 105 | P1 | PASS | available_at | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-007 | 105 | P1 | PASS | received_at | test_market_data_envelope_preserves_source_timestamp_received_exchange_time_and_latency, test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-008 | 105 | P1 | PASS | persisted_at | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-009 | 105 | P1 | PASS | makro veri | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-010 | 105 | P1 | PASS | ETF flow | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-011 | 105 | P1 | PASS | funding | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-012 | 105 | P1 | PASS | open interest | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-013 | 105 | P1 | PASS | liquidation | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-014 | 105 | P1 | PASS | on-chain metric | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-015 | 105 | P1 | PASS | haber/sentiment | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-016 | 105 | P1 | PASS | exchange status/filter değişikliği | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-105-017 | 105 | P1 | PASS | Revize edilen makro verilerde mümkünse vintage/realtime release verisi kullan. | test_phase104_point_in_time_availability_tracks_all_required_semantics_and_macro_vintages |
| REQ-V51-106-001 | 106 | P1 | PASS | Bölüm 106 (MULTI-VENUE / CROSS-EXCHANGE REFERENCE DATA) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-002 | 106 | P1 | PASS | Opsiyonel ReferenceMarketDataAdapter katmanı oluştur. | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-003 | 106 | P1 | PASS | Binance | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-004 | 106 | P1 | PASS | Coinbase | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-005 | 106 | P1 | PASS | Kraken | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-006 | 106 | P1 | PASS | Bybit | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-007 | 106 | P1 | PASS | diğer onaylı kaynaklar | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-008 | 106 | P1 | PASS | reference median/consensus price | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-009 | 106 | P1 | PASS | venue divergence | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-010 | 106 | P1 | PASS | abnormal spread | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-011 | 106 | P1 | PASS | isolated bad tick | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-012 | 106 | P1 | PASS | stale exchange feed | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-106-013 | 106 | P1 | PASS | exchange-specific dislocation | test_phase104_reference_market_consensus_detects_divergence_spread_bad_tick_and_stale_feed |
| REQ-V51-107-001 | 107 | P1 | PASS | Bölüm 107 (DERIVATIVES MARKET INTELLIGENCE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-002 | 107 | P1 | PASS | perpetual funding rate | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-003 | 107 | P1 | PASS | predicted/next funding if reliable | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-004 | 107 | P1 | PASS | open interest | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-005 | 107 | P1 | PASS | OI change | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-006 | 107 | P1 | PASS | futures basis | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-007 | 107 | P1 | PASS | annualized basis | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-008 | 107 | P1 | PASS | mark-index basis | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-009 | 107 | P1 | PASS | liquidation intensity | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-010 | 107 | P1 | PASS | liquidation imbalance | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-011 | 107 | P1 | PASS | taker buy/sell imbalance | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-012 | 107 | P1 | PASS | long/short positioning yalnızca metodolojisi güvenilir ise | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-013 | 107 | P1 | PASS | bu feature'lar tek başına trade açmamalı, | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-014 | 107 | P1 | PASS | provider timestamp'i point-in-time olmalı, | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-015 | 107 | P1 | PASS | missing/stale olduğunda degrade gracefully, | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-016 | 107 | P1 | PASS | backtestte gelecekte açıklanan funding/OI değerleri kullanılmamalı, | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-107-017 | 107 | P1 | PASS | aynı bilginin farklı provider kopyaları double-count edilmemeli. | test_phase104_derivatives_context_is_point_in_time_deduplicated_non_triggering_and_gracefully_stale |
| REQ-V51-108-001 | 108 | P1 | PASS | Bölüm 108 (OPTIONS / IMPLIED VOLATILITY LAYER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-002 | 108 | P1 | PASS | ATM implied volatility | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-003 | 108 | P1 | PASS | term structure | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-004 | 108 | P1 | PASS | skew | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-005 | 108 | P1 | PASS | risk reversal | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-006 | 108 | P1 | PASS | put/call open interest veya volume | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-007 | 108 | P1 | PASS | implied expected move | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-008 | 108 | P1 | PASS | IV - realized volatility spread | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-009 | 108 | P1 | PASS | event-risk | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-010 | 108 | P1 | PASS | volatility expansion/compression | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-011 | 108 | P1 | PASS | tail-risk | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-012 | 108 | P1 | PASS | stop mesafesi | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-013 | 108 | P1 | PASS | position size | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-108-014 | 108 | P1 | PASS | Options verisi yoksa feature capability=false olmalı; uydurma veri üretme. | test_phase104_options_context_is_capability_gated_and_only_modifies_risk_context |
| REQ-V51-109-001 | 109 | P1 | PASS | Bölüm 109 (ON-CHAIN DATA LAYER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-002 | 109 | P1 | PASS | exchange inflow/outflow | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-003 | 109 | P1 | PASS | net exchange flow | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-004 | 109 | P1 | PASS | active addresses gibi network activity metrikleri | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-005 | 109 | P1 | PASS | realized-cap tabanlı metrikler | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-006 | 109 | P1 | PASS | MVRV/SOPR benzeri valuation/behavior metrikleri | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-007 | 109 | P1 | PASS | miner-related flows | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-008 | 109 | P1 | PASS | stablecoin exchange flows | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-009 | 109 | P1 | PASS | on-chain veri düşük frekanslı ve revision/latency içerebilir, | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-010 | 109 | P1 | PASS | provider metodolojisi değişebilir, | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-011 | 109 | P1 | PASS | backtestte available_at kullanılmalı, | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-012 | 109 | P1 | PASS | tek başına kısa vadeli 1m/5m entry tetiklememeli, | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-109-013 | 109 | P1 | PASS | OOS katkısı kanıtlanmazsa production score'da ağırlığı sıfır olmalı. | test_phase104_onchain_context_uses_available_at_never_triggers_intraday_and_requires_oos_edge_for_weight |
| REQ-V51-110-001 | 110 | P1 | PASS | Bölüm 110 (MACRO / EVENT RISK ENGINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-002 | 110 | P1 | PASS | Opsiyonel EventCalendarAdapter oluştur. | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-003 | 110 | P1 | PASS | Takip edilebilecek olaylar: | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-004 | 110 | P1 | PASS | FOMC / Fed kararları ve konuşmalar | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-005 | 110 | P1 | PASS | NFP / employment | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-006 | 110 | P1 | PASS | önemli likidite/faiz gelişmeleri | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-007 | 110 | P1 | PASS | DXY / US yields / real yields gibi makro referanslar | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-008 | 110 | P1 | PASS | ilgili varlığa ait spot ETF/ETP flow verisi güvenilir ve zaman damgalı ise (ör. BTC/ETH) | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-009 | 110 | P1 | PASS | büyük exchange maintenance veya sistem olayları | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-010 | 110 | P1 | PASS | scheduled_time | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-011 | 110 | P1 | PASS | actual_release_time | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-012 | 110 | P1 | PASS | expected | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-013 | 110 | P1 | PASS | actual | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-014 | 110 | P1 | PASS | previous/vintage | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-015 | 110 | P1 | PASS | surprise | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-016 | 110 | P1 | PASS | source | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-017 | 110 | P1 | PASS | reliability | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-018 | 110 | P1 | PASS | no new entry window | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-019 | 110 | P1 | PASS | reduce size | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-020 | 110 | P1 | PASS | widen slippage assumption | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-021 | 110 | P1 | PASS | require extra confirmation | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-110-022 | 110 | P1 | PASS | Ama event blackout kör kural olmamalı; OOS etkisi raporlanmalı. | test_phase104_event_risk_engine_tracks_required_events_point_in_time_and_requires_oos_report_for_blackout |
| REQ-V51-111-001 | 111 | P1 | PASS | Bölüm 111 (NEWS / SENTIMENT / LLM SAFETY LAYER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-002 | 111 | P1 | PASS | trusted source allowlist | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-003 | 111 | P1 | PASS | source URL/id | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-004 | 111 | P1 | PASS | publication timestamp | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-005 | 111 | P1 | PASS | ingestion timestamp | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-006 | 111 | P1 | PASS | duplicate clustering | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-007 | 111 | P1 | PASS | story update/version tracking | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-008 | 111 | P1 | PASS | language normalization | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-009 | 111 | P1 | PASS | source reliability score | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-010 | 111 | P1 | PASS | stale-news rejection | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-011 | 111 | P1 | PASS | haber metni instruction değil DATA'dır, | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-012 | 111 | P1 | PASS | prompt injection içeren haber/web içeriği hiçbir komut çalıştıramaz, | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-013 | 111 | P1 | PASS | LLM doğrudan order gönderemez, | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-014 | 111 | P1 | PASS | LLM sadece schema-validated feature/event classification üretebilir, | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-015 | 111 | P1 | PASS | risk engine deterministic son kapıdır, | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-016 | 111 | P1 | PASS | parsed result source evidence ile ilişkilendirilmeli, | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-111-017 | 111 | P1 | PASS | düşük güven / çelişkili kaynak durumunda NO_TRADE veya feature-disabled tercih edilmeli. | test_phase105_news_sentiment_llm_layer_is_allowlisted_point_in_time_schema_only_and_never_executes_orders |
| REQ-V51-112-001 | 112 | P1 | PASS | Bölüm 112 (FEATURE REGISTRY / REDUNDANCY / ABLATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-002 | 112 | P1 | PASS | name | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-003 | 112 | P1 | PASS | version | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-004 | 112 | P1 | PASS | formula | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-005 | 112 | P1 | PASS | required inputs | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-006 | 112 | P1 | PASS | warmup | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-007 | 112 | P1 | PASS | timeframe | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-008 | 112 | P1 | PASS | latency | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-009 | 112 | P1 | PASS | availability semantics | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-010 | 112 | P1 | PASS | expected range | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-011 | 112 | P1 | PASS | missing-value policy | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-012 | 112 | P1 | PASS | directionality assumption varsa | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-013 | 112 | P1 | PASS | Zorunlu research kontrolleri: | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-014 | 112 | P1 | PASS | correlation matrix | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-015 | 112 | P1 | PASS | cluster/group analysis | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-016 | 112 | P1 | PASS | feature ablation | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-017 | 112 | P1 | PASS | incremental OOS performance | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-018 | 112 | P1 | PASS | permutation/importance yalnızca metodolojik olarak uygunsa | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-112-019 | 112 | P1 | PASS | regime-specific contribution | test_phase105_feature_registry_redundancy_ablation_and_regime_increment_are_explicit_and_versioned |
| REQ-V51-113-001 | 113 | P1 | PASS | Bölüm 113 (ENSEMBLE DIVERSIFICATION / CONFLICT RESOLUTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-002 | 113 | P1 | PASS | return correlation | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-003 | 113 | P1 | PASS | signal correlation | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-004 | 113 | P1 | PASS | drawdown overlap | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-005 | 113 | P1 | PASS | regime dependency | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-006 | 113 | P1 | PASS | turnover | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-007 | 113 | P1 | PASS | capacity/liquidity need | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-008 | 113 | P1 | PASS | bounded | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-009 | 113 | P1 | PASS | explainable | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-010 | 113 | P1 | PASS | versioned | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-011 | 113 | P1 | PASS | OOS validated | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-012 | 113 | P1 | PASS | strategy health aware | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-013 | 113 | P1 | PASS | olmalı. | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-014 | 113 | P1 | PASS | ConflictResolver oluştur: | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-015 | 113 | P1 | PASS | trend BUY + mean-reversion SELL gibi çatışmalarda | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-016 | 113 | P1 | PASS | rejim önceliği | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-017 | 113 | P1 | PASS | net edge | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-018 | 113 | P1 | PASS | risk | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-019 | 113 | P1 | PASS | confidence calibration | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-020 | 113 | P1 | PASS | strategy health | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-113-021 | 113 | P1 | PASS | Çatışma yüksekse ABSTAIN / NO_TRADE geçerli ve tercih edilebilir sonuç olmalı. | test_phase105_ensemble_diversification_conflict_resolution_is_bounded_explainable_health_and_risk_aware |
| REQ-V51-114-001 | 114 | P1 | PASS | Bölüm 114 (NO-TRADE / ABSTENTION ENGINE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-002 | 114 | P1 | PASS | net edge yetersiz | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-003 | 114 | P1 | PASS | confidence uncalibrated | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-004 | 114 | P1 | PASS | MTF conflict | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-005 | 114 | P1 | PASS | regime unclear | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-006 | 114 | P1 | PASS | spread high | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-007 | 114 | P1 | PASS | liquidity insufficient | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-008 | 114 | P1 | PASS | slippage too high | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-009 | 114 | P1 | PASS | data incomplete/stale | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-010 | 114 | P1 | PASS | cross-venue divergence | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-011 | 114 | P1 | PASS | macro event risk | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-012 | 114 | P1 | PASS | unprotected position exists | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-013 | 114 | P1 | PASS | strategy degraded | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-014 | 114 | P1 | PASS | execution engine degraded | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-015 | 114 | P1 | PASS | daily/weekly risk budget low | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-114-016 | 114 | P1 | PASS | recent drawdown cooling period | test_phase105_no_trade_abstention_engine_covers_edge_calibration_market_data_execution_and_drawdown_conditions |
| REQ-V51-115-001 | 115 | P1 | PASS | Bölüm 115 (COST-AWARE EXPECTANCY / BREAK-EVEN GATE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-115-002 | 115 | P1 | PASS | EXPECTED_FEES | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-115-003 | 115 | P1 | PASS | EXPECTED_SPREAD | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-115-004 | 115 | P1 | PASS | EXPECTED_SLIPPAGE | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-115-005 | 115 | P1 | PASS | EXPECTED_FUNDING_OR_BORROW | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-115-006 | 115 | P1 | PASS | UNCERTAINTY_BUFFER | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-115-007 | 115 | P1 | PASS | olarak işaretle ve deterministic/OOS proxy gate kullan. | test_phase105_cost_aware_expectancy_gate_requires_positive_net_edge_after_all_costs_and_oos_validation |
| REQ-V51-116-001 | 116 | P1 | PASS | Bölüm 116 (VOLATILITY TARGETING / DRAWDOWN-ADAPTIVE RISK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-002 | 116 | P1 | PASS | DynamicRiskBudget oluştur: | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-003 | 116 | P1 | PASS | Tüm scalar'lar bounded ve versioned olmalı. | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-004 | 116 | P1 | PASS | realized volatility yükselirse risk azalt | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-005 | 116 | P1 | PASS | drawdown büyürse risk azalt | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-006 | 116 | P1 | PASS | liquidity bozulursa risk azalt | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-007 | 116 | P1 | PASS | strategy health düşerse risk azalt | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-008 | 116 | P1 | PASS | recovery sırasında risk kademeli artır | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-009 | 116 | P1 | PASS | "Zarar ettim, daha çok risk alıp geri kazanayım" davranışı kesinlikle yasak. | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-010 | 116 | P1 | PASS | Martingale yasak. | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-011 | 116 | P1 | PASS | aggregate stop-risk | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-012 | 116 | P1 | PASS | correlated strategy risk | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-013 | 116 | P1 | PASS | correlated asset risk (multi-asset) | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-014 | 116 | P1 | PASS | güvenilir calibrated distribution | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-015 | 116 | P1 | PASS | çok uzun OOS history | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-016 | 116 | P1 | PASS | fractional Kelly | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-017 | 116 | P1 | PASS | sert üst limit | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-116-018 | 116 | P1 | PASS | ile; varsayılan disabled olması tercih edilir. | test_phase105_dynamic_risk_budget_is_bounded_deleverages_on_vol_drawdown_liquidity_health_and_disables_kelly_by_default |
| REQ-V51-117-001 | 117 | P1 | PASS | Bölüm 117 (TAIL RISK / EXPECTED SHORTFALL / STRESS LIBRARY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-002 | 117 | P1 | PASS | Raporla: | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-003 | 117 | P1 | PASS | VaR (yardımcı) | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-004 | 117 | P1 | PASS | Expected Shortfall / CVaR | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-005 | 117 | P1 | PASS | drawdown duration / time under water | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-006 | 117 | P1 | PASS | worst rolling return | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-007 | 117 | P1 | PASS | downside deviation | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-008 | 117 | P1 | PASS | tail ratio uygun ise | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-009 | 117 | P1 | PASS | gap loss | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-010 | 117 | P1 | PASS | liquidity-adjusted stress loss | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-011 | 117 | P1 | PASS | StressScenarioLibrary oluştur. | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-012 | 117 | P1 | PASS | flash crash | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-013 | 117 | P1 | PASS | sudden gap / jump | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-014 | 117 | P1 | PASS | spread xN genişleme | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-015 | 117 | P1 | PASS | order book liquidity collapse | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-016 | 117 | P1 | PASS | API latency spike | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-017 | 117 | P1 | PASS | private stream disconnect | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-018 | 117 | P1 | PASS | exchange partial outage | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-019 | 117 | P1 | PASS | stablecoin depeg | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-020 | 117 | P1 | PASS | funding spike | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-021 | 117 | P1 | PASS | mark/index divergence | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-022 | 117 | P1 | PASS | high-volatility liquidation cascade | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-117-023 | 117 | P1 | PASS | database/redis failure while position open | test_phase105_tail_risk_metrics_stress_library_and_liquidity_adjusted_stress_are_complete_and_conservative |
| REQ-V51-118-001 | 118 | P1 | PASS | Bölüm 118 (QUOTE-ASSET / STABLECOIN / COUNTERPARTY RISK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-002 | 118 | P1 | PASS | QuoteAssetRiskEngine oluştur. | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-003 | 118 | P1 | PASS | Takip et: | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-004 | 118 | P1 | PASS | USDT/USDC/USD parity divergence mümkünse | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-005 | 118 | P1 | PASS | quote asset depeg | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-006 | 118 | P1 | PASS | exchange withdrawal/deposit status yalnızca gerekiyorsa | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-007 | 118 | P1 | PASS | venue-specific price dislocation | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-008 | 118 | P1 | PASS | custody concentration | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-009 | 118 | P1 | PASS | idle balance concentration | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-010 | 118 | P1 | PASS | new entry block | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-011 | 118 | P1 | PASS | reducing only | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-118-012 | 118 | P1 | PASS | alternate quote symbol suggestion (otomatik transfer yapmadan) | test_phase105_quote_asset_counterparty_risk_blocks_new_entry_and_is_reduce_only_without_auto_transfer |
| REQ-V51-119-001 | 119 | P1 | PASS | Bölüm 119 (TIME-OF-DAY / WEEKEND / MAINTENANCE / FUNDING WINDOWS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-002 | 119 | P1 | PASS | UTC hour | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-003 | 119 | P1 | PASS | day of week | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-004 | 119 | P1 | PASS | weekend vs weekday | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-005 | 119 | P1 | PASS | Asia / Europe / US overlap gibi configurable session buckets | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-006 | 119 | P1 | PASS | funding windows | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-007 | 119 | P1 | PASS | major scheduled event windows | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-119-008 | 119 | P1 | PASS | Dokümante edilmiş WebSocket connection lifetime varsa planned rotation yap; bağlantının zorunlu süre sonunda düşmesini "beklenmeyen hata" gibi ele alma. | test_phase105_time_of_day_weekend_funding_event_maintenance_and_planned_websocket_rotation_are_explicit |
| REQ-V51-120-001 | 120 | P1 | PASS | Bölüm 120 (PURGED / EMBARGO VALIDATION / NESTED WALK-FORWARD / CPCV) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-002 | 120 | P1 | PASS | Destekle: | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-003 | 120 | P1 | PASS | time-series split | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-004 | 120 | P1 | PASS | purged train/validation split | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-005 | 120 | P1 | PASS | embargo period | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-006 | 120 | P1 | PASS | nested walk-forward optimization | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-007 | 120 | P1 | PASS | final untouched holdout | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-120-008 | 120 | P1 | PASS | uygun araştırmalarda Combinatorial Purged Cross-Validation (CPCV) | test_phase105_purged_embargo_nested_walk_forward_final_holdout_and_cpcv_prevent_temporal_leakage |
| REQ-V51-121-001 | 121 | P1 | PASS | Bölüm 121 (BLOCK BOOTSTRAP / REGIME-AWARE MONTE CARLO) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-002 | 121 | P1 | PASS | simple trade reshuffle | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-003 | 121 | P1 | PASS | block bootstrap | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-004 | 121 | P1 | PASS | stationary bootstrap | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-005 | 121 | P1 | PASS | regime-stratified bootstrap | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-006 | 121 | P1 | PASS | cost shock simulation | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-007 | 121 | P1 | PASS | slippage shock | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-008 | 121 | P1 | PASS | latency shock | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-009 | 121 | P1 | PASS | Seri korelasyon varsa effective sample size raporla. | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-010 | 121 | P1 | PASS | ruin probability | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-011 | 121 | P1 | PASS | expected/max drawdown distribution | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-012 | 121 | P1 | PASS | drawdown duration | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-013 | 121 | P1 | PASS | losing streak | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-014 | 121 | P1 | PASS | terminal wealth distribution | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-015 | 121 | P1 | PASS | recovery time | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-121-016 | 121 | P1 | PASS | percentile bands | test_phase106_block_bootstrap_regime_monte_carlo_reports_tail_path_and_effective_sample_statistics |
| REQ-V51-122-001 | 122 | P1 | PASS | Bölüm 122 (POINT-IN-TIME COST / FEE TIER / FUNDING / BORROW MODEL) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-002 | 122 | P1 | PASS | Backtestte bugünkü fee oranını bütün geçmişe uygulamak zorunlu varsayım olmamalı. | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-003 | 122 | P1 | PASS | maker fee | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-004 | 122 | P1 | PASS | taker fee | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-005 | 122 | P1 | PASS | fee discount assumptions | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-006 | 122 | P1 | PASS | VIP/account tier | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-007 | 122 | P1 | PASS | funding history | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-008 | 122 | P1 | PASS | borrow interest history | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-009 | 122 | P1 | PASS | symbol filter history | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-010 | 122 | P1 | PASS | minimum notional / tick-size değişiklikleri | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-011 | 122 | P1 | PASS | explicit assumption | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-012 | 122 | P1 | PASS | source | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-013 | 122 | P1 | PASS | validity range | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-014 | 122 | P1 | PASS | sensitivity range | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-122-015 | 122 | P1 | PASS | raporla. | test_phase106_point_in_time_cost_model_resolves_historical_fee_tier_funding_borrow_filters_and_sensitivity |
| REQ-V51-123-001 | 123 | P1 | PASS | Bölüm 123 (EXCHANGE API CONTRACT / CHANGELOG / SCHEMA COMPATIBILITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-002 | 123 | P1 | PASS | AdapterVersion manifest oluştur: | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-003 | 123 | P1 | PASS | exchange | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-004 | 123 | P1 | PASS | market type | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-005 | 123 | P1 | PASS | API family | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-006 | 123 | P1 | PASS | documented schema/version | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-007 | 123 | P1 | PASS | authentication type | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-008 | 123 | P1 | PASS | supported endpoints | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-009 | 123 | P1 | PASS | limits snapshot | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-010 | 123 | P1 | PASS | filters snapshot | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-011 | 123 | P1 | PASS | last compatibility test | test_adapter_manifest_captures_contract_limits_filters_and_auth_profile, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-012 | 123 | P1 | PASS | schema parsing | test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-013 | 123 | P1 | PASS | unknown enum tolerance | test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review, test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed |
| REQ-V51-123-014 | 123 | P1 | PASS | new optional field tolerance | test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review, test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed |
| REQ-V51-123-015 | 123 | P1 | PASS | required field missing handling | test_missing_required_order_contract_field_fails_explicitly, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-016 | 123 | P1 | PASS | error-code mapping | test_http_429_maps_to_explicit_rate_limit_error_and_retry_after, test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review |
| REQ-V51-123-017 | 123 | P1 | PASS | rate-limit headers | test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review, test_rate_limit_response_headers_are_parsed_and_exposed_without_guessing_missing_headers |
| REQ-V51-123-018 | 123 | P1 | PASS | order status mapping | test_phase106_exchange_api_contract_schema_compatibility_is_versioned_and_changelog_breakage_requires_review, test_unknown_order_status_and_unknown_response_fields_are_tolerated_fail_closed |
| REQ-V51-124-001 | 124 | P1 | PASS | Bölüm 124 (WEBSOCKET LIFECYCLE / CONNECTION ROTATION / TRAFFIC BUDGET) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-002 | 124 | P1 | PASS | connection_started_at | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-003 | 124 | P1 | PASS | documented/max lifetime config | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-004 | 124 | P1 | PASS | planned_rotation_at | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-005 | 124 | P1 | PASS | ping/pong health | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-006 | 124 | P1 | PASS | inbound/outbound message rate | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-007 | 124 | P1 | PASS | subscription count | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-008 | 124 | P1 | PASS | reconnect count | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-009 | 124 | P1 | PASS | disconnect reason | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-010 | 124 | P1 | PASS | sakla. | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-011 | 124 | P1 | PASS | yeni bağlantıyı aç | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-012 | 124 | P1 | PASS | subscription'ları doğrula | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-013 | 124 | P1 | PASS | veri continuity kontrol et | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-014 | 124 | P1 | PASS | private stream ise account/order state reconcile et | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-015 | 124 | P1 | PASS | yeni stream healthy olduktan sonra eskisini kapat | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-124-016 | 124 | P1 | PASS | Mümkün olduğunda overlap/handover kullan. | test_phase106_websocket_lifecycle_tracks_budget_rotation_and_only_handover_after_verified_continuity_and_private_reconcile |
| REQ-V51-125-001 | 125 | P1 | PASS | Bölüm 125 (AUTHENTICATION TYPES / TRANSPORT ABSTRACTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams |
| REQ-V51-125-002 | 125 | P1 | PASS | HMAC | test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams |
| REQ-V51-125-003 | 125 | P1 | PASS | Ed25519 | test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams |
| REQ-V51-125-004 | 125 | P1 | PASS | REST JSON | test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams |
| REQ-V51-125-005 | 125 | P1 | PASS | WebSocket request/response | test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams |
| REQ-V51-125-006 | 125 | P1 | PASS | WebSocket streams | test_phase106_authentication_transport_abstraction_supports_hmac_ed25519_rest_json_ws_request_response_and_streams |
| REQ-V51-126-001 | 126 | P1 | PASS | Bölüm 126 (SMART EXECUTION / MAKER-TAKER / ALPHA HALF-LIFE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-002 | 126 | P1 | PASS | signal urgency | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-003 | 126 | P1 | PASS | expected alpha half-life | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-004 | 126 | P1 | PASS | spread | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-005 | 126 | P1 | PASS | depth | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-006 | 126 | P1 | PASS | expected slippage | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-007 | 126 | P1 | PASS | adverse selection | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-008 | 126 | P1 | PASS | maker/taker fee difference | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-009 | 126 | P1 | PASS | fill probability | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-010 | 126 | P1 | PASS | time to fill | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-011 | 126 | P1 | PASS | order rejection risk | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-012 | 126 | P1 | PASS | current volatility | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-013 | 126 | P1 | PASS | market | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-014 | 126 | P1 | PASS | aggressive limit | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-015 | 126 | P1 | PASS | passive limit/post-only | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-016 | 126 | P1 | PASS | IOC/FOK | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-017 | 126 | P1 | PASS | cancel/replace | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-126-018 | 126 | P1 | PASS | sliced execution yalnızca gerekli notional'da | test_phase106_smart_execution_uses_urgency_alpha_half_life_spread_depth_cost_fill_rejection_vol_and_slicing |
| REQ-V51-127-001 | 127 | P1 | PASS | Bölüm 127 (PROTECTIVE ORDER RESIZING / TRIGGER SOURCE SEMANTICS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-002 | 127 | P1 | PASS | Koruyucu emirlerde açıkça sakla: | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-003 | 127 | P1 | PASS | trigger_source = LAST / MARK / INDEX / BID / ASK / MID capability'ye göre | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-004 | 127 | P1 | PASS | trigger_direction | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-005 | 127 | P1 | PASS | reduce_only | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-006 | 127 | P1 | PASS | close_position semantics | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-007 | 127 | P1 | PASS | working_type varsa | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-008 | 127 | P1 | PASS | quantity | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-127-009 | 127 | P1 | PASS | protected_position_quantity | test_phase106_protective_order_contract_persists_trigger_source_direction_reduce_only_close_working_type_and_protected_quantity |
| REQ-V51-128-001 | 128 | P1 | PASS | Bölüm 128 (RISK STATE MACHINE / RECOVERY HYSTERESIS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_recovery_hysteresis_rejects_single_transient_green_sample |
| REQ-V51-128-002 | 128 | P1 | PASS | Tek boolean TRADING_ENABLED yerine formal RiskState kullan. | test_formal_risk_states_are_explicit |
| REQ-V51-128-003 | 128 | P1 | PASS | STARTING | test_formal_risk_states_are_explicit |
| REQ-V51-128-004 | 128 | P1 | PASS | PAPER_ONLY | test_formal_risk_states_are_explicit |
| REQ-V51-128-005 | 128 | P1 | PASS | ACTIVE | test_formal_risk_states_are_explicit |
| REQ-V51-128-006 | 128 | P1 | PASS | DEGRADED | test_formal_risk_states_are_explicit |
| REQ-V51-128-007 | 128 | P1 | PASS | REDUCING_ONLY | test_formal_risk_states_are_explicit |
| REQ-V51-128-008 | 128 | P1 | PASS | HALTED | test_formal_risk_states_are_explicit |
| REQ-V51-128-009 | 128 | P1 | PASS | RECOVERY_PENDING | test_formal_risk_states_are_explicit |
| REQ-V51-128-010 | 128 | P1 | PASS | MANUAL_REVIEW_REQUIRED | test_formal_risk_states_are_explicit |
| REQ-V51-128-011 | 128 | P1 | PASS | STOPPING | test_formal_risk_states_are_explicit |
| REQ-V51-128-012 | 128 | P1 | PASS | Her transition için reason code ve allowed actions tanımla. | test_risk_state_allowed_actions_are_fail_closed |
| REQ-V51-128-013 | 128 | P1 | PASS | HALTED -> ACTIVE otomatik ve anında olmamalı. | test_formal_risk_states_are_explicit, test_halted_cannot_jump_directly_to_active_even_with_green_checks |
| REQ-V51-128-014 | 128 | P1 | PASS | data healthy for minimum duration | test_halted_recovery_requires_human_and_all_green_checks, test_recovery_hysteresis_rejects_single_transient_green_sample |
| REQ-V51-128-015 | 128 | P1 | PASS | exchange healthy | test_halted_recovery_requires_human_and_all_green_checks |
| REQ-V51-128-016 | 128 | P1 | PASS | private stream healthy | test_halted_recovery_requires_human_and_all_green_checks |
| REQ-V51-128-017 | 128 | P1 | PASS | reconciliation PASS | test_halted_recovery_requires_human_and_all_green_checks, test_protective_stop_coverage |
| REQ-V51-128-018 | 128 | P1 | PASS | no orphan orders | test_halted_recovery_requires_human_and_all_green_checks, test_restart_recovery_missing_exchange_order_blocks_no_orphan_gate |
| REQ-V51-128-019 | 128 | P1 | PASS | protective orders PASS | test_halted_recovery_requires_human_and_all_green_checks, test_protective_coverage_fails_for_any_exposed_symbol_without_guard, test_protective_stop_coverage |
| REQ-V51-128-020 | 128 | P1 | PASS | risk limits PASS | test_halted_recovery_requires_human_and_all_green_checks |
| REQ-V51-128-021 | 128 | P1 | PASS | clock PASS | test_halted_recovery_requires_human_and_all_green_checks |
| REQ-V51-128-022 | 128 | P1 | PASS | strategy health PASS | test_halted_recovery_requires_human_and_all_green_checks |
| REQ-V51-128-023 | 128 | P1 | PASS | gibi hysteresis/gate kullan. | test_halted_recovery_requires_human_and_all_green_checks, test_recovery_hysteresis_rejects_single_transient_green_sample |
| REQ-V51-129-001 | 129 | P1 | PASS | Bölüm 129 (CONFIG SAFETY / IMMUTABLE LIVE PROFILE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-002 | 129 | P1 | PASS | 0 < RISK_PER_TRADE <= configured hard cap | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash, test_risk_config_cross_field_validation_fail_closed |
| REQ-V51-129-003 | 129 | P1 | PASS | MIN_RISK_REWARD > 0 | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash, test_risk_config_cross_field_validation_fail_closed |
| REQ-V51-129-004 | 129 | P1 | PASS | MAX_DAILY_LOSS <= MAX_DRAWDOWN mantıksal ilişkileri | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash, test_risk_config_cross_field_validation_fail_closed |
| REQ-V51-129-005 | 129 | P1 | PASS | TP allocation sum = 100% gerekiyorsa | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash, test_risk_config_cross_field_validation_fail_closed |
| REQ-V51-129-006 | 129 | P1 | PASS | timeframe dependency valid | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-007 | 129 | P1 | PASS | market type capability valid | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-008 | 129 | P1 | PASS | symbol filter valid | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-009 | 129 | P1 | PASS | LIVE çalışan strategy/config immutable snapshot olmalı. | test_live_config_risk_increase_requires_restart_and_human_approval, test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-010 | 129 | P1 | PASS | risk azaltıcı emergency değişikliklere izin verilebilir, | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-011 | 129 | P1 | PASS | risk artırıcı/strategy-changing ayarlar revalidation + explicit approval gerektirir. | test_live_config_risk_increase_requires_restart_and_human_approval, test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-012 | 129 | P1 | PASS | old value | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-013 | 129 | P1 | PASS | new value | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-014 | 129 | P1 | PASS | actor | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-015 | 129 | P1 | PASS | reason | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-016 | 129 | P1 | PASS | timestamp | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-017 | 129 | P1 | PASS | config hash | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-018 | 129 | P1 | PASS | required gate | test_live_config_risk_increase_requires_restart_and_human_approval, test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-129-019 | 129 | P1 | PASS | sakla. | test_phase106_live_profile_is_validated_immutable_and_emergency_mutation_can_only_reduce_risk_with_audit_hash |
| REQ-V51-130-001 | 130 | P1 | PASS | Bölüm 130 (LIVE SHADOW / CHAMPION-CHALLENGER) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-002 | 130 | P1 | PASS | Champion-Challenger modeli destekle: | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-003 | 130 | P1 | PASS | CHAMPION = mevcut onaylı live strategy | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-004 | 130 | P1 | PASS | CHALLENGER = aynı canlı veriyi gören fakat order göndermeyen shadow strategy | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-005 | 130 | P1 | PASS | hypothetical signal | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-006 | 130 | P1 | PASS | hypothetical order intent | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-007 | 130 | P1 | PASS | expected fill | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-008 | 130 | P1 | PASS | actual market path | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-009 | 130 | P1 | PASS | cost model | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-010 | 130 | P1 | PASS | divergence from champion | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-130-011 | 130 | P1 | PASS | gate zinciri kullan. | test_phase106_champion_challenger_is_shadow_only_records_hypothetical_intent_fill_market_path_cost_divergence_and_gates |
| REQ-V51-131-001 | 131 | P1 | PASS | Bölüm 131 (ONLINE CHANGE DETECTION / STRATEGY DEGRADATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-002 | 131 | P1 | PASS | Opsiyonel sequential degradation detector oluştur: | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-003 | 131 | P1 | PASS | CUSUM | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-004 | 131 | P1 | PASS | Page-Hinkley | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-005 | 131 | P1 | PASS | Bayesian/change-point yaklaşımı | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-006 | 131 | P1 | PASS | rolling control bands | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-007 | 131 | P1 | PASS | Ama minimum sample ve false-alarm kontrolü zorunlu. | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-008 | 131 | P1 | PASS | Takip et: | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-009 | 131 | P1 | PASS | expectancy decay | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-010 | 131 | P1 | PASS | win/loss payoff change | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-011 | 131 | P1 | PASS | slippage drift | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-012 | 131 | P1 | PASS | fill-rate drift | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-013 | 131 | P1 | PASS | feature distribution drift | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-014 | 131 | P1 | PASS | regime mix shift | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-131-015 | 131 | P1 | PASS | calibration drift | test_phase106_online_degradation_detection_has_minimum_sample_false_alarm_guard_and_cusum_page_hinkley_support |
| REQ-V51-132-001 | 132 | P1 | PASS | Bölüm 132 (PNL / SIGNAL / EXECUTION ATTRIBUTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-002 | 132 | P1 | PASS | PnL decomposition oluştur: | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-003 | 132 | P1 | PASS | signal alpha | test_implementation_shortfall, test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-004 | 132 | P1 | PASS | entry timing | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-005 | 132 | P1 | PASS | exit timing | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-006 | 132 | P1 | PASS | spread cost | test_implementation_shortfall, test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-007 | 132 | P1 | PASS | slippage | test_implementation_shortfall, test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-008 | 132 | P1 | PASS | fees | test_implementation_shortfall, test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-009 | 132 | P1 | PASS | funding/borrow | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-010 | 132 | P1 | PASS | adverse selection | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-011 | 132 | P1 | PASS | missed fill opportunity | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-012 | 132 | P1 | PASS | stop gap loss | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-013 | 132 | P1 | PASS | kötü strategy mi, | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-014 | 132 | P1 | PASS | kötü execution mı, | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-015 | 132 | P1 | PASS | yüksek maliyet mi, | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-132-016 | 132 | P1 | PASS | data latency mi | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-001 | 133 | P1 | PASS | Bölüm 133 (PERFORMANCE ATTRIBUTION BY REGIME / TIME / SCORE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-002 | 133 | P1 | PASS | strategy | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-003 | 133 | P1 | PASS | strategy version | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-004 | 133 | P1 | PASS | market regime | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-005 | 133 | P1 | PASS | volatility bucket | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-006 | 133 | P1 | PASS | timeframe | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-007 | 133 | P1 | PASS | long/short/spot-exit | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-008 | 133 | P1 | PASS | confidence bucket | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-009 | 133 | P1 | PASS | signal score bucket | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-010 | 133 | P1 | PASS | hour-of-day | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-011 | 133 | P1 | PASS | day-of-week | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-012 | 133 | P1 | PASS | weekend/weekday | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-013 | 133 | P1 | PASS | execution type | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-014 | 133 | P1 | PASS | maker/taker | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-015 | 133 | P1 | PASS | liquidity bucket | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-133-016 | 133 | P1 | PASS | data quality bucket | test_phase106_pnl_signal_execution_attribution_decomposes_timing_funding_adverse_selection_missed_fill_stop_gap_latency_and_groups_context |
| REQ-V51-134-001 | 134 | P1 | PASS | Bölüm 134 (BENCHMARKS / ECONOMIC SIGNIFICANCE / MINIMUM TRACK RECORD) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-002 | 134 | P1 | PASS | her test edilen varlık için point-in-time buy-and-hold | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-003 | 134 | P1 | PASS | uygun ise eşit ağırlıklı / likidite ağırlıklı universe benchmark | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-004 | 134 | P1 | PASS | cash/no-trade baseline | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-005 | 134 | P1 | PASS | basit DCA baseline uygun dönemde | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-006 | 134 | P1 | PASS | basit trend baseline | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-007 | 134 | P1 | PASS | Raporla: | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-008 | 134 | P1 | PASS | alpha/excess return uygun tanımla | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-009 | 134 | P1 | PASS | Sharpe/Sortino uncertainty | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-010 | 134 | P1 | PASS | Deflated Sharpe Ratio | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-011 | 134 | P1 | PASS | Probabilistic Sharpe Ratio uygun ise | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-012 | 134 | P1 | PASS | Minimum Track Record Length | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-013 | 134 | P1 | PASS | effective sample size | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-014 | 134 | P1 | PASS | bootstrap confidence intervals | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-134-015 | 134 | P1 | PASS | Probability of Backtest Overfitting uygun metodoloji ile | test_phase106_benchmarks_economic_significance_track_record_uncertainty_and_overfit_proxies_are_reported |
| REQ-V51-135-001 | 135 | P1 | PASS | Bölüm 135 (SECURITY HARDENING — TLS / MFA / BROWSER SECURITY / DATA AT REST) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase119_tls_trusted_proxy_and_encrypted_backup_delivery_contracts_are_fail_closed |
| REQ-V51-135-002 | 135 | P1 | PASS | HTTPS/TLS zorunlu | test_phase119_tls_trusted_proxy_and_encrypted_backup_delivery_contracts_are_fail_closed |
| REQ-V51-135-003 | 135 | P1 | PASS | secure cookies | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-004 | 135 | P1 | PASS | HttpOnly | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-005 | 135 | P1 | PASS | SameSite | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-006 | 135 | P1 | PASS | HSTS | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-007 | 135 | P1 | PASS | X-Content-Type-Options | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-008 | 135 | P1 | PASS | clickjacking protection | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-009 | 135 | P1 | PASS | trusted proxy configuration | test_phase119_tls_trusted_proxy_and_encrypted_backup_delivery_contracts_are_fail_closed |
| REQ-V51-135-010 | 135 | P1 | PASS | MFA/TOTP veya passkey desteği özellikle admin/trader hesapları için | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-011 | 135 | P1 | PASS | session revocation | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-012 | 135 | P1 | PASS | inactivity timeout | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-013 | 135 | P1 | PASS | suspicious-login audit | test_prod_security_headers_docs_disabled_and_correlation_id_preserved |
| REQ-V51-135-014 | 135 | P1 | PASS | Backup dosyaları da şifreli ve access-controlled olmalı. | test_phase119_tls_trusted_proxy_and_encrypted_backup_delivery_contracts_are_fail_closed |
| REQ-V51-136-001 | 136 | P1 | PASS | Bölüm 136 (LIVE CAPITAL RAMP / FINAL PROFITABILITY EVIDENCE GATE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-002 | 136 | P1 | PASS | Kademeli live risk ramp oluştur. | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-003 | 136 | P1 | PASS | LIVE_STAGE_0 = manual-confirmation + minimal risk | test_live_ramp_requires_human |
| REQ-V51-136-004 | 136 | P1 | PASS | LIVE_STAGE_1 = approved risk budget'un küçük kısmı | test_live_ramp_requires_human |
| REQ-V51-136-005 | 136 | P1 | PASS | LIVE_STAGE_2 = sınırlı artış | test_live_ramp_requires_human |
| REQ-V51-136-006 | 136 | P1 | PASS | LIVE_STAGE_3 = normal approved risk budget | test_live_ramp_requires_human |
| REQ-V51-136-007 | 136 | P1 | PASS | Stage multiplier configurable olmalı; stage artışı otomatik kâr kovalamaya dönüşmemeli. | test_live_ramp_requires_human |
| REQ-V51-136-008 | 136 | P1 | PASS | reconciliation PASS | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-009 | 136 | P1 | PASS | zero unresolved critical incidents | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-010 | 136 | P1 | PASS | protective order success rate acceptable | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-011 | 136 | P1 | PASS | live slippage within bound | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-012 | 136 | P1 | PASS | live vs shadow/paper divergence acceptable | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-013 | 136 | P1 | PASS | net expectancy non-negative/acceptable with uncertainty | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-014 | 136 | P1 | PASS | drawdown within bound | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-015 | 136 | P1 | PASS | sufficient effective sample | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-016 | 136 | P1 | PASS | multiple market conditions observed | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-017 | 136 | P1 | PASS | strategy not degraded | test_phase119_live_ramp_blocks_every_required_operational_and_profitability_condition |
| REQ-V51-136-018 | 136 | P1 | PASS | human approval | test_live_ramp_requires_human |
| REQ-V51-136-019 | 136 | P1 | PASS | Gerekirse stage otomatik azaltılabilir; otomatik artırma varsayılan kapalı olmalı. | test_live_ramp_requires_human |
| REQ-V51-136-020 | 136 | P1 | PASS | In-sample result | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-021 | 136 | P1 | PASS | Out-of-sample result | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-022 | 136 | P1 | PASS | Walk-forward result | test_phase134_local_fixture_walk_forward_purged_embargo_cost_stress_and_effective_sample_are_real_code_paths |
| REQ-V51-136-023 | 136 | P1 | PASS | Purged/embargo validation result | test_phase134_local_fixture_walk_forward_purged_embargo_cost_stress_and_effective_sample_are_real_code_paths |
| REQ-V51-136-024 | 136 | P1 | PASS | DSR / multiple-testing evidence | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-025 | 136 | P1 | PASS | Fee/slippage/funding adverse scenario | test_phase134_local_fixture_walk_forward_purged_embargo_cost_stress_and_effective_sample_are_real_code_paths |
| REQ-V51-136-026 | 136 | P1 | PASS | Tail stress scenarios | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-027 | 136 | P1 | NOT_TESTED | Paper result |  |
| REQ-V51-136-028 | 136 | P1 | NOT_TESTED | Testnet execution result |  |
| REQ-V51-136-029 | 136 | P1 | NOT_TESTED | Live-shadow result |  |
| REQ-V51-136-030 | 136 | P1 | PASS | Benchmark comparison | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-031 | 136 | P1 | PASS | Effective sample size | test_phase134_local_fixture_walk_forward_purged_embargo_cost_stress_and_effective_sample_are_real_code_paths |
| REQ-V51-136-032 | 136 | P1 | PASS | Confidence intervals | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-033 | 136 | P1 | PASS | Strategy/regime attribution | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-034 | 136 | P1 | PASS | Execution attribution | test_phase136_local_fixture_reports_is_oos_dsr_tail_benchmark_ci_and_attribution_without_live_claim |
| REQ-V51-136-035 | 136 | P1 | PASS | Known limitations | test_phase128_delivery_status_discloses_known_limitations_and_unresolved_risks |
| REQ-V51-136-036 | 136 | P1 | PASS | Unresolved risks | test_phase128_delivery_status_discloses_known_limitations_and_unresolved_risks |
| REQ-V51-136-037 | 136 | P1 | PASS | LIVE stage recommendation | test_live_ramp_requires_human |
| REQ-V51-137-001 | 137 | P0 | PASS | Bölüm 137 (MULTI-ASSET UNIVERSE MANAGER / POINT-IN-TIME UNIVERSE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-002 | 137 | P0 | PASS | Sistem hard-coded birkaç coin listesine bağımlı OLMAMALI. | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-003 | 137 | P0 | PASS | UniverseManager oluştur. | test_eligible |
| REQ-V51-137-004 | 137 | P0 | PASS | STATIC_ALLOWLIST | test_eligible |
| REQ-V51-137-005 | 137 | P0 | PASS | DYNAMIC_EXCHANGE_UNIVERSE | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-006 | 137 | P0 | PASS | TOP_LIQUIDITY_N | test_eligible |
| REQ-V51-137-007 | 137 | P0 | PASS | TOP_VOLUME_N | test_eligible |
| REQ-V51-137-008 | 137 | P0 | PASS | RESEARCH_SNAPSHOT | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics, test_research_snapshot_rejects_future_available_membership_and_snapshots_are_immutable |
| REQ-V51-137-009 | 137 | P0 | PASS | Varsayılan güvenli yaklaşım: | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-010 | 137 | P0 | PASS | universe_snapshot_id | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-137-011 | 137 | P0 | PASS | exchange | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-012 | 137 | P0 | PASS | market_type | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-013 | 137 | P0 | PASS | symbol | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-014 | 137 | P0 | PASS | base_asset | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-015 | 137 | P0 | PASS | quote_asset | test_eligible |
| REQ-V51-137-016 | 137 | P0 | PASS | trading_status | test_eligible |
| REQ-V51-137-017 | 137 | P0 | PASS | first_seen_at | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-018 | 137 | P0 | PASS | listing/open time biliniyorsa | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-019 | 137 | P0 | PASS | eligible_from | test_eligible |
| REQ-V51-137-020 | 137 | P0 | PASS | eligible_until | test_eligible |
| REQ-V51-137-021 | 137 | P0 | PASS | inclusion_reason | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-022 | 137 | P0 | PASS | exclusion_reason | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-023 | 137 | P0 | PASS | metadata_version | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-137-024 | 137 | P0 | PASS | observed_at | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-137-025 | 137 | P0 | PASS | available_at | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics, test_research_snapshot_rejects_future_available_membership_and_snapshots_are_immutable |
| REQ-V51-137-026 | 137 | P0 | PASS | sakla. | test_point_in_time_universe_registry_is_dynamic_snapshot_based_and_preserves_membership_forensics |
| REQ-V51-138-001 | 138 | P0 | PASS | Bölüm 138 (SYMBOL ELIGIBILITY / LİKİDİTE / KALİTE FİLTRELERİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_eligibility_engine_accepts_complete_liquid_healthy_symbol, test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-002 | 138 | P0 | PASS | EligibilityEngine oluştur. | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-003 | 138 | P0 | PASS | En az kontrol et: | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-004 | 138 | P0 | PASS | symbol trading status aktif mi | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-005 | 138 | P0 | PASS | market type destekleniyor mu | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-006 | 138 | P0 | PASS | base/quote asset izinli mi | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-007 | 138 | P0 | PASS | minimum listing age | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-008 | 138 | P0 | PASS | yeterli historical bar var mı | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-009 | 138 | P0 | PASS | 24h quote volume minimumu | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-010 | 138 | P0 | PASS | rolling median volume | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-011 | 138 | P0 | PASS | median/percentile spread | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-012 | 138 | P0 | PASS | order-book depth | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-013 | 138 | P0 | PASS | expected slippage | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-014 | 138 | P0 | PASS | minimum trade count | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-015 | 138 | P0 | PASS | stale tick oranı | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-016 | 138 | P0 | PASS | missing candle oranı | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-017 | 138 | P0 | PASS | abnormal gap/data error oranı | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-018 | 138 | P0 | PASS | exchange filter uyumluluğu | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-019 | 138 | P0 | PASS | symbol precision/filter metadata mevcut mu | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-138-020 | 138 | P0 | PASS | quote asset risk durumu | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-021 | 138 | P0 | PASS | venue health durumu | test_eligibility_engine_checks_market_assets_listing_history_liquidity_quality_filters_quote_and_venue |
| REQ-V51-138-022 | 138 | P0 | PASS | Yeni listelenen varlıklarda configurable quarantine uygula: | test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters |
| REQ-V51-138-023 | 138 | P0 | PASS | Filtre eşikleri asset price seviyesine bağımlı kör nominal rakamlar yerine mümkün olduğunca bps/notional/percentile tabanlı olmalı. | test_eligibility_policy_uses_relative_bps_ratio_and_notional_thresholds |
| REQ-V51-139-001 | 139 | P0 | PASS | Bölüm 139 (LISTING / DELISTING / SUSPENSION / TOKEN LIFECYCLE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-002 | 139 | P0 | PASS | AssetLifecycleManager oluştur. | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-003 | 139 | P0 | PASS | Takip et: | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-004 | 139 | P0 | PASS | scheduled listing/open time | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-005 | 139 | P0 | PASS | trading enabled/disabled | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-006 | 139 | P0 | PASS | symbol suspension | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-007 | 139 | P0 | PASS | delisting announcement/time biliniyorsa | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-008 | 139 | P0 | PASS | quote pair removal | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-009 | 139 | P0 | PASS | token rename | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-010 | 139 | P0 | PASS | redenomination | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-011 | 139 | P0 | PASS | contract migration | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-012 | 139 | P0 | PASS | chain migration | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-013 | 139 | P0 | PASS | hard fork etkisi | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-014 | 139 | P0 | PASS | ticker değişimi | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-015 | 139 | P0 | PASS | decimal/precision değişimi | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-139-016 | 139 | P0 | PASS | asset merge/split/rebase benzeri ekonomik anlam değişiklikleri | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-017 | 139 | P0 | PASS | kullanıcıyı uyar | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-018 | 139 | P0 | PASS | venue kurallarını doğrula | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-019 | 139 | P0 | PASS | exit/reducing-only policy uygula | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-020 | 139 | P0 | PASS | otomatik transfer/withdrawal yapma | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-139-021 | 139 | P0 | PASS | Asset mapping değişikliği versioned ve audit edilebilir olmalı. | test_asset_lifecycle_manager_supports_suspension_pair_removal_migration_fork_and_economic_changes |
| REQ-V51-140-001 | 140 | P0 | PASS | Bölüm 140 (CROSS-SECTIONAL SCANNER / CANDIDATE RANKING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters |
| REQ-V51-140-002 | 140 | P0 | PASS | ScannerEngine oluştur. | test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters |
| REQ-V51-140-003 | 140 | P0 | PASS | calibrated net expectancy | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-004 | 140 | P0 | PASS | signal confidence | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-005 | 140 | P0 | PASS | trend/regime alignment | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-006 | 140 | P0 | PASS | liquidity quality | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-007 | 140 | P0 | PASS | expected slippage | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-008 | 140 | P0 | PASS | risk/reward | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-009 | 140 | P0 | PASS | volatility suitability | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-010 | 140 | P0 | PASS | strategy health | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-011 | 140 | P0 | PASS | diversification benefit | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-012 | 140 | P0 | PASS | data quality | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-013 | 140 | P0 | PASS | Gerektiğinde cross-sectional percentile/z-score veya asset-specific calibration kullan. | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-014 | 140 | P0 | PASS | rank | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-015 | 140 | P0 | PASS | rank_score | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-016 | 140 | P0 | PASS | eligible/not eligible | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-017 | 140 | P0 | PASS | signal | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-018 | 140 | P0 | PASS | net expected edge | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-019 | 140 | P0 | PASS | risk budget | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-020 | 140 | P0 | PASS | blocking reasons | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-021 | 140 | P0 | PASS | correlation penalty | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-022 | 140 | P0 | PASS | liquidity penalty | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-140-023 | 140 | P0 | PASS | data quality score | test_cross_sectional_ranking_uses_expectancy_confidence_regime_liquidity_slippage_rr_health_diversification_and_data_quality |
| REQ-V51-141-001 | 141 | P0 | PASS | Bölüm 141 (MULTI-ASSET PORTFOLIO CORRELATION / CONCENTRATION RISK) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-002 | 141 | P0 | PASS | Takip et: | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-003 | 141 | P0 | PASS | per-asset exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-004 | 141 | P0 | PASS | per-symbol exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-005 | 141 | P0 | PASS | per-quote exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-006 | 141 | P0 | PASS | per-exchange exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-007 | 141 | P0 | PASS | per-market-type exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-008 | 141 | P0 | PASS | per-strategy exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-009 | 141 | P0 | PASS | long/short directional exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-010 | 141 | P0 | PASS | rolling return correlation | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-011 | 141 | P0 | PASS | downside correlation | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-012 | 141 | P0 | PASS | tail correlation | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-013 | 141 | P0 | PASS | rolling beta to BTC | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-014 | 141 | P0 | PASS | rolling beta to ETH uygun ise | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-015 | 141 | P0 | PASS | covariance / risk contribution | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-016 | 141 | P0 | PASS | correlated cluster exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-017 | 141 | P0 | PASS | common-factor exposure | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-141-018 | 141 | P0 | PASS | Bu nedenle stress correlation / crisis correlation senaryosu da uygula. | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-142-001 | 142 | P0 | PASS | Bölüm 142 (CAPITAL ALLOCATION / CASH BUFFER / RISK BUDGETING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-002 | 142 | P0 | PASS | CapitalAllocator oluştur. | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-003 | 142 | P0 | PASS | account equity | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-004 | 142 | P0 | PASS | free collateral/cash | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-005 | 142 | P0 | PASS | portfolio heat | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-006 | 142 | P0 | PASS | candidate expected edge | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-007 | 142 | P0 | PASS | stop-risk | test_capital_allocator_revalidates_remaining_risk_after_each_candidate |
| REQ-V51-142-008 | 142 | P0 | PASS | volatility | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-009 | 142 | P0 | PASS | liquidity | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-010 | 142 | P0 | PASS | correlation penalty | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-011 | 142 | P0 | PASS | strategy health | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-012 | 142 | P0 | PASS | drawdown state | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-013 | 142 | P0 | PASS | market regime | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-014 | 142 | P0 | PASS | quote-asset risk | test_capital_allocator_penalizes_correlation_and_unhealthy_strategy |
| REQ-V51-142-015 | 142 | P0 | PASS | reserve/cash buffer configurable olmalı | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-016 | 142 | P0 | PASS | açık emirlerin reserved capital'i hesaba katılmalı | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-017 | 142 | P0 | PASS | fee/funding/slippage için buffer ayrılmalı | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-018 | 142 | P0 | PASS | aynı cycle'da birden fazla emir birlikte risk kontrolünden geçmeli | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers |
| REQ-V51-142-019 | 142 | P0 | PASS | sequential order placement sonucu exposure değiştikçe kalan candidate'lar yeniden doğrulanmalı | test_capital_allocator_keeps_cash_reserve_open_order_and_cost_buffers, test_capital_allocator_revalidates_remaining_risk_after_each_candidate |
| REQ-V51-142-020 | 142 | P0 | PASS | Portfolio optimizer kullanılacaksa aşırı hassas unconstrained mean-variance çözümü varsayılan olmasın. | test_phase23_optimizer_default_is_constrained_not_unbounded_mean_variance |
| REQ-V51-143-001 | 143 | P0 | PASS | Bölüm 143 (MULTI-SYMBOL MARKET DATA SCALABILITY / RATE-LIMIT BUDGET) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_market_data_coordinator_preserves_high_priority_under_backpressure |
| REQ-V51-143-002 | 143 | P0 | PASS | MarketDataCoordinator oluştur. | test_market_data_coordinator_shards_and_reconnects_deterministically |
| REQ-V51-143-003 | 143 | P0 | PASS | WebSocket multiplex/combined stream veya provider-equivalent batching | test_public_stream_url_uses_documented_combined_stream_shapes |
| REQ-V51-143-004 | 143 | P0 | PASS | connection sharding gerektiğinde | test_market_data_coordinator_shards_and_reconnects_deterministically |
| REQ-V51-143-005 | 143 | P0 | PASS | per-connection subscription registry | test_market_data_coordinator_shards_and_reconnects_deterministically |
| REQ-V51-143-006 | 143 | P0 | PASS | reconnect + resubscribe | test_market_data_coordinator_shards_and_reconnects_deterministically |
| REQ-V51-143-007 | 143 | P0 | PASS | sequence/state recovery | test_orderbook_gap_invalidates_until_fresh_snapshot_resync |
| REQ-V51-143-008 | 143 | P0 | PASS | bounded queues | test_market_data_coordinator_preserves_high_priority_under_backpressure |
| REQ-V51-143-009 | 143 | P0 | PASS | per-symbol freshness state | test_market_data_coordinator_tracks_symbol_freshness_without_global_halt |
| REQ-V51-143-010 | 143 | P0 | PASS | priority tiers | test_market_data_coordinator_preserves_high_priority_under_backpressure |
| REQ-V51-143-011 | 143 | P0 | PASS | rate-limit budget manager | test_market_data_coordinator_runtime_rate_budget_and_jittered_reconciliation |
| REQ-V51-143-012 | 143 | P0 | PASS | request weight/order limit telemetry | test_market_data_coordinator_runtime_rate_budget_and_jittered_reconciliation |
| REQ-V51-143-013 | 143 | P0 | PASS | REST reconciliation budget | test_market_data_coordinator_runtime_rate_budget_and_jittered_reconciliation |
| REQ-V51-143-014 | 143 | P0 | PASS | jittered refresh schedules | test_market_data_coordinator_runtime_rate_budget_and_jittered_reconciliation |
| REQ-V51-143-015 | 143 | P0 | PASS | private order/fill events | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-143-016 | 143 | P0 | PASS | protective position data | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-143-017 | 143 | P0 | PASS | best bid/ask + execution-critical book | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-143-018 | 143 | P0 | PASS | active-position market data | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-143-019 | 143 | P0 | PASS | candidate market data | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-143-020 | 143 | P0 | PASS | low-priority scanner data | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-144-001 | 144 | P0 | PASS | Bölüm 144 (MULTI-SYMBOL EXECUTION ISOLATION / CONCURRENCY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate |
| REQ-V51-144-002 | 144 | P0 | PASS | symbol-scoped order intent idempotency | test_durable_intent_id_collision_with_different_symbol_fails_closed_without_submit |
| REQ-V51-144-003 | 144 | P0 | PASS | account-level capital reservation | test_live_execution_requires_fencing_and_reservation |
| REQ-V51-144-004 | 144 | P0 | PASS | per-symbol state machine | test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate |
| REQ-V51-144-005 | 144 | P0 | PASS | concurrent candidate reconciliation | test_concurrent_candidate_reconciliation_never_double_allocates_shared_cycle_budget |
| REQ-V51-144-006 | 144 | P0 | PASS | deterministic ordering/priority policy | test_market_data_priority_tiers_follow_v51_ordering |
| REQ-V51-144-007 | 144 | P0 | PASS | duplicate intent prevention across worker/process instances | test_durable_intent_id_collision_with_different_symbol_fails_closed_without_submit, test_live_execution_requires_fencing_and_reservation |
| REQ-V51-144-008 | 144 | P0 | PASS | distributed lock kullanılıyorsa fencing/expiry semantics | test_live_execution_requires_fencing_and_reservation |
| REQ-V51-144-009 | 144 | P0 | PASS | lock failure durumunda risk artırıcı emir yok | test_execution_lock_failure_prevents_exchange_side_effect |
| REQ-V51-145-001 | 145 | P0 | PASS | Bölüm 145 (ASSET-SPECIFIC NORMALIZATION / PARAMETER POLICY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-002 | 145 | P0 | PASS | GLOBAL SAFETY LIMITS | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-003 | 145 | P0 | PASS | ASSET/LIQUIDITY-CLASS LIMITS | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-004 | 145 | P0 | PASS | STRATEGY-ASSET CALIBRATED PARAMETERS | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-005 | 145 | P0 | PASS | CORE_HIGH_LIQUIDITY | test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade |
| REQ-V51-145-006 | 145 | P0 | PASS | LARGE_CAP | test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade |
| REQ-V51-145-007 | 145 | P0 | PASS | MID_LIQUIDITY | test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade |
| REQ-V51-145-008 | 145 | P0 | PASS | NEW_LISTING | test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade |
| REQ-V51-145-009 | 145 | P0 | PASS | HIGH_VOLATILITY | test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade |
| REQ-V51-145-010 | 145 | P0 | PASS | RESTRICTED/NO_TRADE | test_all_asset_liquidity_classes_exist_and_restricted_is_no_trade |
| REQ-V51-145-011 | 145 | P0 | PASS | ATR percent / normalized ATR | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-012 | 145 | P0 | PASS | spread bps | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-013 | 145 | P0 | PASS | volume in quote notional | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-014 | 145 | P0 | PASS | depth notional | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-145-015 | 145 | P0 | PASS | return/volatility standardized values | test_asset_parameter_policy_intersects_global_class_and_strategy_parameters_using_normalized_features |
| REQ-V51-146-001 | 146 | P0 | PASS | Bölüm 146 (MULTI-ASSET BACKTEST / SURVIVORSHIP-BIAS KORUMASI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_dataset_manifest_detects_change |
| REQ-V51-146-002 | 146 | P0 | PASS | point-in-time universe membership | test_dataset_manifest_detects_change |
| REQ-V51-146-003 | 146 | P0 | PASS | listing/delisting zamanları | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-146-004 | 146 | P0 | PASS | historical symbol/filter versions mümkünse | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-146-005 | 146 | P0 | PASS | eşzamanlı candidate yarışması | test_concurrent_multi_symbol_reservations_never_overcommit_available_capital |
| REQ-V51-146-006 | 146 | P0 | PASS | capital contention | test_concurrent_candidate_reconciliation_never_double_allocates_shared_cycle_budget |
| REQ-V51-146-007 | 146 | P0 | PASS | max open positions | test_exposure_blocks |
| REQ-V51-146-008 | 146 | P0 | PASS | portfolio heat | test_exposure_blocks |
| REQ-V51-146-009 | 146 | P0 | PASS | correlated exposure | test_exposure_blocks |
| REQ-V51-146-010 | 146 | P0 | PASS | order timing across symbols | test_next_bar_entry_and_costs |
| REQ-V51-146-011 | 146 | P0 | PASS | shared account balance | test_multi_asset_backtest_uses_point_in_time_universe_and_shared_equity_curve |
| REQ-V51-146-012 | 146 | P0 | PASS | per-symbol fees/slippage/liquidity | test_multi_asset_delisting_forces_exit_and_costs_are_charged |
| REQ-V51-146-013 | 146 | P0 | PASS | quote-asset risk | test_exposure_blocks |
| REQ-V51-146-014 | 146 | P0 | PASS | delisting/suspension exit policy | test_multi_asset_delisting_forces_exit_and_costs_are_charged |
| REQ-V51-146-015 | 146 | P0 | PASS | missing-data policy | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-016 | 146 | P0 | PASS | Bugünün en başarılı 50 coinini seçip geçmişe test etmek YASAK. | test_dataset_manifest_detects_change |
| REQ-V51-146-017 | 146 | P0 | PASS | portfolio equity curve | test_multi_asset_backtest_uses_point_in_time_universe_and_shared_equity_curve |
| REQ-V51-146-018 | 146 | P0 | PASS | per-asset contribution | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-019 | 146 | P0 | PASS | per-strategy contribution | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-020 | 146 | P0 | PASS | turnover | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-021 | 146 | P0 | PASS | concentration | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-022 | 146 | P0 | PASS | average/maximum number of concurrent positions | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-023 | 146 | P0 | PASS | correlation-adjusted drawdown | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-024 | 146 | P0 | PASS | universe turnover | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-025 | 146 | P0 | PASS | excluded-symbol reason distribution | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-026 | 146 | P0 | PASS | delisted asset contribution | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-146-027 | 146 | P0 | PASS | selection/ranking attribution | test_performance_attribution_reports_asset_strategy_turnover_concentration_concurrency_drawdown_universe_and_selection_effects |
| REQ-V51-147-001 | 147 | P0 | PASS | Bölüm 147 (MULTI-ASSET RESEARCH / MULTIPLE-TESTING CONTROL) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-002 | 147 | P0 | PASS | asset universe version | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-003 | 147 | P0 | PASS | symbol set | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-004 | 147 | P0 | PASS | strategy version | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-005 | 147 | P0 | PASS | parameter search space | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-006 | 147 | P0 | PASS | feature set | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-007 | 147 | P0 | PASS | timeframe set | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-008 | 147 | P0 | PASS | train/OOS windows | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-009 | 147 | P0 | PASS | number of trials | test_research_registry_keeps_failures |
| REQ-V51-147-010 | 147 | P0 | PASS | primary metric | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-011 | 147 | P0 | PASS | gelecekteki universe membership | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-012 | 147 | P0 | PASS | future market-cap/category tag | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-013 | 147 | P0 | PASS | revised metadata | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-014 | 147 | P0 | PASS | future liquidity rank | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-147-015 | 147 | P0 | PASS | end-of-day bilgiyi intraday erken kullanma | test_research_manifest_is_complete_and_rejects_future_membership_metadata_liquidity_and_intraday_eod_information |
| REQ-V51-148-001 | 148 | P0 | PASS | Bölüm 148 (QUOTE / VENUE / MARKET-TYPE ROUTING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability |
| REQ-V51-148-002 | 148 | P0 | PASS | InstrumentRouter oluştur. | test_routing_prefers_cost |
| REQ-V51-148-003 | 148 | P0 | PASS | approved quote asset | test_routing_prefers_cost |
| REQ-V51-148-004 | 148 | P0 | PASS | spread | test_routing_prefers_cost |
| REQ-V51-148-005 | 148 | P0 | PASS | depth | test_routing_prefers_cost |
| REQ-V51-148-006 | 148 | P0 | PASS | fee tier | test_routing_prefers_cost |
| REQ-V51-148-007 | 148 | P0 | PASS | slippage | test_routing_prefers_cost |
| REQ-V51-148-008 | 148 | P0 | PASS | venue health | test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability |
| REQ-V51-148-009 | 148 | P0 | PASS | quote depeg risk | test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability |
| REQ-V51-148-010 | 148 | P0 | PASS | market type | test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability |
| REQ-V51-148-011 | 148 | P0 | PASS | funding/basis | test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability |
| REQ-V51-148-012 | 148 | P0 | PASS | user/account capability | test_phase21_route_policy_checks_venue_quote_market_type_funding_and_account_capability |
| REQ-V51-148-013 | 148 | P0 | PASS | UnderlyingExposureAggregator oluştur. | test_routing_prefers_cost |
| REQ-V51-149-001 | 149 | P0 | PASS | Bölüm 149 (ASSET IDENTITY / METADATA VERSIONING) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-002 | 149 | P0 | PASS | AssetMaster ve SymbolMaster oluştur. | test_exchange_symbol_and_asset_metadata_are_from_exchange_info |
| REQ-V51-149-003 | 149 | P0 | PASS | asset_id | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-004 | 149 | P0 | PASS | canonical_symbol | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-005 | 149 | P0 | PASS | display_name | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-006 | 149 | P0 | PASS | chain/network bilgisi gerekiyorsa | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-007 | 149 | P0 | PASS | contract identifier yalnızca güvenilir kaynaktan | test_asset_contract_identifier_requires_trusted_source_and_validity_ranges_do_not_overlap, test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-008 | 149 | P0 | PASS | decimals metadata | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-149-009 | 149 | P0 | PASS | active_from/to | test_asset_contract_identifier_requires_trusted_source_and_validity_ranges_do_not_overlap, test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-010 | 149 | P0 | PASS | metadata_source | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-149-011 | 149 | P0 | PASS | metadata_version | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-149-012 | 149 | P0 | PASS | exchange | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-013 | 149 | P0 | PASS | market_type | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-014 | 149 | P0 | PASS | symbol | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-015 | 149 | P0 | PASS | base_asset_id | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-016 | 149 | P0 | PASS | quote_asset_id | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-017 | 149 | P0 | PASS | contract_type | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-018 | 149 | P0 | PASS | status | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-019 | 149 | P0 | PASS | filters | test_symbol_metadata_history_is_point_in_time_versioned_and_future_safe |
| REQ-V51-149-020 | 149 | P0 | PASS | onboard/open time | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-021 | 149 | P0 | PASS | expire/delist time | test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-149-022 | 149 | P0 | PASS | version validity range | test_asset_contract_identifier_requires_trusted_source_and_validity_ranges_do_not_overlap, test_asset_metadata_versions_preserve_identity_market_fields_and_point_in_time_validity |
| REQ-V51-150-001 | 150 | P0 | PASS | Bölüm 150 (HIGH-RISK ASSET / NEW-LISTING / MICROCAP POLICY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-002 | 150 | P0 | PASS | NORMAL | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-003 | 150 | P0 | PASS | ELEVATED_VOLATILITY | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-004 | 150 | P0 | PASS | NEW_LISTING | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-005 | 150 | P0 | PASS | THIN_LIQUIDITY | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-006 | 150 | P0 | PASS | QUOTE_RISK | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-007 | 150 | P0 | PASS | VENUE_RISK | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-008 | 150 | P0 | PASS | RESTRICTED | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-009 | 150 | P0 | PASS | NO_TRADE | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-010 | 150 | P0 | PASS | Risk profile sinyal üretiminden bağımsız bir gate olmalı. | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-011 | 150 | P0 | PASS | reduced max position size | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-012 | 150 | P0 | PASS | higher required net edge | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-013 | 150 | P0 | PASS | lower max slippage tolerance | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-014 | 150 | P0 | PASS | stricter spread/depth filter | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-015 | 150 | P0 | PASS | manual confirmation required | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-016 | 150 | P0 | PASS | paper-only | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-150-017 | 150 | P0 | PASS | no-trade | test_high_risk_asset_policy_is_signal_independent_and_applies_stricter_controls |
| REQ-V51-151-001 | 151 | P0 | PASS | Bölüm 151 (MARKET BREADTH / LEADER-LAGGARD CONTEXT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-002 | 151 | P0 | PASS | Opsiyonel cross-asset regime features oluştur: | test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers |
| REQ-V51-151-003 | 151 | P0 | PASS | eligible universe içinde yükselen/düşen oranı | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-004 | 151 | P0 | PASS | median return | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-005 | 151 | P0 | PASS | median realized volatility | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-006 | 151 | P0 | PASS | percentage above EMA/SMA | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-007 | 151 | P0 | PASS | breadth thrust benzeri ölçüler metodolojik olarak doğrulanırsa | test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers |
| REQ-V51-151-008 | 151 | P0 | PASS | BTC/ETH leadership | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-009 | 151 | P0 | PASS | altcoin breadth | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-010 | 151 | P0 | PASS | dispersion | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-011 | 151 | P0 | PASS | cross-sectional momentum dispersion | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-151-012 | 151 | P0 | PASS | Portfolio/rejim bağlamını geliştiren yardımcı sinyaller olmalı. | test_phase21_breadth_context_requires_point_in_time_universe_and_exposes_cross_asset_helpers |
| REQ-V51-151-013 | 151 | P0 | PASS | Breadth hesaplanırken point-in-time universe kullan. | test_market_breadth_uses_point_in_time_universe_and_cross_asset_context |
| REQ-V51-152-001 | 152 | P0 | PASS | Bölüm 152 (MULTI-ASSET DASHBOARD / OPERASYON EKRANI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_dashboard_endpoint_exposes_user_facing_operational_snapshot |
| REQ-V51-152-002 | 152 | P0 | PASS | Dashboard yalnızca tek coin grafiği olmamalı. | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-003 | 152 | P0 | PASS | Market Scanner | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-004 | 152 | P0 | PASS | Universe Health | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-005 | 152 | P0 | PASS | Candidate Ranking | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-006 | 152 | P0 | PASS | Portfolio & Exposure | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-007 | 152 | P0 | PASS | Correlation / Concentration | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-008 | 152 | P0 | PASS | Active Positions | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-009 | 152 | P0 | PASS | Orders & Fills | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-010 | 152 | P0 | PASS | Per-Asset Analysis | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-011 | 152 | P0 | PASS | Strategy Health | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-012 | 152 | P0 | PASS | Data/Exchange Health | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-013 | 152 | P0 | PASS | Backtest/Research | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-014 | 152 | P0 | PASS | Risk Events | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-015 | 152 | P0 | PASS | symbol | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-016 | 152 | P0 | PASS | price | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-017 | 152 | P0 | PASS | 24h quote volume | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-018 | 152 | P0 | PASS | spread bps | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-019 | 152 | P0 | PASS | volatility | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-020 | 152 | P0 | PASS | regime | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-021 | 152 | P0 | PASS | signal | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-022 | 152 | P0 | PASS | score | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-023 | 152 | P0 | PASS | confidence | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-024 | 152 | P0 | PASS | net edge | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-025 | 152 | P0 | PASS | liquidity score | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-026 | 152 | P0 | PASS | rank | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-027 | 152 | P0 | PASS | block reason | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-028 | 152 | P0 | PASS | data age | test_universe_scanner_metadata_and_breadth |
| REQ-V51-152-029 | 152 | P0 | PASS | Kullanıcı aynı anda tüm coinlere emir gönderen tehlikeli 'trade all' butonuna sahip olmamalı. | test_multi_asset_operator_ui_exposes_required_primary_areas_without_trade_all_control |
| REQ-V51-152-030 | 152 | P0 | PASS | Scanner varsayılan görünümü kullanıcıyı veriyle boğmamalı. İlk görünümde yalnızca karar için gerekli kolonlar; gelişmiş mikro-yapı ve diagnostik kolonları opsiyonel olmalı. | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-152-031 | 152 | P0 | PASS | column hide/show | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-152-032 | 152 | P0 | PASS | search/filter | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-152-033 | 152 | P0 | PASS | stable sorting | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-152-034 | 152 | P0 | PASS | saved views | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-152-035 | 152 | P0 | PASS | pagination/virtualization | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-152-036 | 152 | P0 | PASS | mobile card fallback | test_phase21_scanner_default_is_decision_focused_with_hide_show_search_stable_sort_paging_saved_view_and_mobile |
| REQ-V51-153-001 | 153 | P0 | PASS | Bölüm 153 (MULTI-ASSET OBSERVABILITY / SLO) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-002 | 153 | P0 | PASS | universe_size | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-003 | 153 | P0 | PASS | eligible_symbols | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-004 | 153 | P0 | PASS | excluded_symbols | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-005 | 153 | P0 | PASS | universe_refresh_failures | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-006 | 153 | P0 | PASS | scanner_cycle_duration | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-007 | 153 | P0 | PASS | scanner_candidates_total | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-008 | 153 | P0 | PASS | stale_symbols | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-153-009 | 153 | P0 | PASS | websocket_subscriptions | test_market_data_subscription_telemetry_is_bounded_and_matches_registry |
| REQ-V51-153-010 | 153 | P0 | PASS | websocket_shards | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-011 | 153 | P0 | PASS | rate_limit_budget_remaining uygun ise | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-012 | 153 | P0 | PASS | symbol_data_latency | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-013 | 153 | P0 | PASS | symbol_order_reject_rate | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-014 | 153 | P0 | PASS | symbol_slippage | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-015 | 153 | P0 | PASS | portfolio_concentration | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-016 | 153 | P0 | PASS | correlated_cluster_exposure | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-017 | 153 | P0 | PASS | quote_asset_exposure | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-018 | 153 | P0 | PASS | capital_reserved | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-019 | 153 | P0 | PASS | capital_available | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-153-020 | 153 | P0 | PASS | High-cardinality detayları DB/log/trace katmanında tut; metrics'te bounded yaklaşım kullan. | test_multiasset_metrics_are_bounded_and_cover_operational_risk_fields |
| REQ-V51-154-001 | 154 | P0 | PASS | Bölüm 154 (MULTI-ASSET FINAL ACCEPTANCE / CHAOS / LOAD TESTLERİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-002 | 154 | P0 | PASS | dynamic universe discovery | test_dynamic_universe_scanner_emits_cycle_health_and_enforces_configured_max |
| REQ-V51-154-003 | 154 | P0 | PASS | allowlist/blocklist | test_dynamic_universe_policy_applies_allowlist_blocklist_and_quote_filter |
| REQ-V51-154-004 | 154 | P0 | PASS | quote filter | test_dynamic_universe_policy_applies_allowlist_blocklist_and_quote_filter |
| REQ-V51-154-005 | 154 | P0 | PASS | non-TRADING symbol exclusion | test_exclusion_reasons |
| REQ-V51-154-006 | 154 | P0 | PASS | insufficient history exclusion | test_exclusion_reasons |
| REQ-V51-154-007 | 154 | P0 | PASS | new listing quarantine | test_exclusion_reasons |
| REQ-V51-154-008 | 154 | P0 | PASS | delisting/suspension block | test_exclusion_reasons |
| REQ-V51-154-009 | 154 | P0 | PASS | point-in-time membership | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-154-010 | 154 | P0 | PASS | historical delisted symbol retention | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-154-011 | 154 | P0 | PASS | survivorship-bias regression test | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-154-012 | 154 | P0 | PASS | 10 / 50 / configured max symbol tarama | test_scanner_respects_requested_10_50_and_configured_max_limits |
| REQ-V51-154-013 | 154 | P0 | PASS | candidate ranking determinism | test_ranking_deterministic |
| REQ-V51-154-014 | 154 | P0 | PASS | no candidate => NO_TRADE | test_no_candidate_explicitly_returns_no_trade |
| REQ-V51-154-015 | 154 | P0 | PASS | stale symbol isolation | test_exclusion_reasons |
| REQ-V51-154-016 | 154 | P0 | PASS | liquidity/spread exclusion | test_exclusion_reasons |
| REQ-V51-154-017 | 154 | P0 | PASS | ranking tie handling | test_ranking_deterministic |
| REQ-V51-154-018 | 154 | P0 | PASS | max single asset exposure | test_asset_exposure_blocks |
| REQ-V51-154-019 | 154 | P0 | PASS | correlated cluster limit | test_cluster_exposure |
| REQ-V51-154-020 | 154 | P0 | PASS | quote asset limit | test_quote_asset_exposure_blocks |
| REQ-V51-154-021 | 154 | P0 | PASS | simultaneous candidate capital contention | test_concurrent_multi_symbol_reservations_never_overcommit_available_capital |
| REQ-V51-154-022 | 154 | P0 | PASS | reserved balance | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-023 | 154 | P0 | PASS | drawdown-adaptive allocation | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-024 | 154 | P0 | PASS | stress correlation spike | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-154-025 | 154 | P0 | PASS | simultaneous orders on different symbols | test_concurrent_multi_symbol_reservations_never_overcommit_available_capital |
| REQ-V51-154-026 | 154 | P0 | PASS | same-symbol duplicate prevention | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-027 | 154 | P0 | PASS | account-level risk lock | test_account_level_risk_lock_serializes_same_account_critical_sections |
| REQ-V51-154-028 | 154 | P0 | PASS | one symbol UNKNOWN order while others operate safely | test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate |
| REQ-V51-154-029 | 154 | P0 | PASS | shared balance changed between candidate ranking and submit | test_shared_balance_changed_between_ranking_and_live_submit_fails_closed |
| REQ-V51-154-030 | 154 | P0 | PASS | metadata/filter changed immediately before order | test_symbol_filter_change_between_validation_and_submit_fails_closed |
| REQ-V51-154-031 | 154 | P0 | PASS | configured max universe WebSocket subscription | test_configured_max_universe_websocket_subscription_coverage_is_exact |
| REQ-V51-154-032 | 154 | P0 | PASS | reconnect + resubscribe all shards | test_reconnect_resubscribes_every_market_data_shard_without_loss |
| REQ-V51-154-033 | 154 | P0 | PASS | backpressure under burst | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-034 | 154 | P0 | PASS | rate-limit exhaustion simulation | test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed |
| REQ-V51-154-035 | 154 | P0 | PASS | REST fallback budget | test_rate_limit_exhaustion_and_rest_fallback_budget_fail_closed |
| REQ-V51-154-036 | 154 | P0 | PASS | one-symbol poison/bad message isolation | test_one_symbol_poison_message_isolated_without_reconnect_storm |
| REQ-V51-154-037 | 154 | P0 | PASS | memory growth/soak test | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-038 | 154 | P0 | PASS | token rename | test_asset_lifecycle_manager_versions_warns_revalidates_and_never_auto_transfers |
| REQ-V51-154-039 | 154 | P0 | PASS | symbol migration | test_asset_lifecycle_manager_versions_warns_revalidates_and_never_auto_transfers |
| REQ-V51-154-040 | 154 | P0 | PASS | precision/filter change | test_symbol_filter_change_between_validation_and_submit_fails_closed |
| REQ-V51-154-041 | 154 | P0 | PASS | scheduled listing | test_asset_lifecycle_manager_versions_warns_revalidates_and_never_auto_transfers |
| REQ-V51-154-042 | 154 | P0 | PASS | delisting while flat | test_asset_lifecycle_manager_versions_warns_revalidates_and_never_auto_transfers |
| REQ-V51-154-043 | 154 | P0 | PASS | delisting while position open | test_multi_asset_delisting_forces_exit_and_costs_are_charged |
| REQ-V51-154-044 | 154 | P0 | PASS | historical point-in-time universe | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-154-045 | 154 | P0 | PASS | capital competition between assets | test_concurrent_multi_symbol_reservations_never_overcommit_available_capital |
| REQ-V51-154-046 | 154 | P0 | PASS | same timestamp multiple candidate ordering | test_concurrent_multi_symbol_reservations_never_overcommit_available_capital |
| REQ-V51-154-047 | 154 | P0 | PASS | delisted asset included historically | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-154-048 | 154 | P0 | PASS | future listing excluded historically | test_point_in_time_universe_excludes_future_listing_and_delisted_symbol |
| REQ-V51-154-049 | 154 | P0 | PASS | multi-asset fee/slippage correctness | test_multi_asset_delisting_forces_exit_and_costs_are_charged |
| REQ-V51-154-050 | 154 | P0 | PASS | correlation/concentration gate reproduction | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-154-051 | 154 | P0 | PASS | universe/scanner PAPER validation | test_scanner_ranking_applies_listing_quarantine_stale_and_risk_filters |
| REQ-V51-154-052 | 154 | P0 | PASS | representative liquidity classes | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-053 | 154 | P0 | PASS | multi-position reconciliation | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-054 | 154 | P0 | PASS | multi-symbol order/fill handling | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-055 | 154 | P0 | PASS | portfolio concentration controls | test_multi_asset_correlation_snapshot_tracks_exposure_beta_covariance_clusters_and_stress |
| REQ-V51-154-056 | 154 | P0 | PASS | quote-asset risk controls | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-057 | 154 | P0 | PASS | load/soak test | test_backpressure_drops_low_when_full |
| REQ-V51-154-058 | 154 | P0 | PASS | unresolved critical incident = 0 | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-059 | 154 | P0 | PASS | human approval | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-060 | 154 | P0 | PASS | PASS / FAIL / SKIPPED | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-061 | 154 | P0 | PASS | test environment | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-062 | 154 | P0 | PASS | exact reason | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-063 | 154 | P0 | PASS | evidence/log reference | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-064 | 154 | P0 | PASS | known limitation | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-154-065 | 154 | P0 | PASS | "Test yazıldı" ile "test çalıştırıldı ve geçti" ayrımını kesin yap. | test_multiasset_acceptance_evidence_distinguishes_executed_pass_from_written_test_and_requires_zero_critical_incidents |
| REQ-V51-155-001 | 155 | P1 | PASS | Bölüm 155 (PRODUCT UX PRINCIPLES / KULLANICI ODAKLI TASARIM) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract |
| REQ-V51-155-002 | 155 | P1 | PASS | ZORUNLU UX ilkeleri: | test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract |
| REQ-V51-155-003 | 155 | P1 | PASS | progressive disclosure: temel kullanıcıya sade görünüm, uzman kullanıcıya gelişmiş detay | test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract |
| REQ-V51-155-004 | 155 | P1 | PASS | safe defaults | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-005 | 155 | P1 | PASS | mode awareness | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-006 | 155 | P1 | PASS | visible system status | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-007 | 155 | P1 | PASS | explainable decisions | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-008 | 155 | P1 | PASS | undo/cancel yalnızca gerçekten güvenli ve teknik olarak mümkün aksiyonlarda | test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract |
| REQ-V51-155-009 | 155 | P1 | PASS | destructive/high-risk action confirmation | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-010 | 155 | P1 | PASS | no dark patterns | test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract |
| REQ-V51-155-011 | 155 | P1 | PASS | no ambiguous BUY/SELL state | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-012 | 155 | P1 | PASS | latency/staleness görünürlüğü | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-155-013 | 155 | P1 | PASS | consistent terminology | test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms |
| REQ-V51-156-001 | 156 | P1 | PASS | Bölüm 156 (ALWAYS-ON TRADING SERVER / CLIENT AYRIMI) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-002 | 156 | P1 | PASS | Trading engine 7/24 çalışan server-side servis olmalı. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-003 | 156 | P1 | PASS | Browser kapanınca trading engine durmamalı. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-004 | 156 | P1 | PASS | Tauri app kapanınca trading engine durmamalı. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-005 | 156 | P1 | PASS | Frontend deploy/restart trading state'i bozmamalı. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-006 | 156 | P1 | PASS | UI yalnızca server'ın doğrulanmış state'ini göstermeli. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-007 | 156 | P1 | PASS | UI doğrudan exchange private API secret ile işlem yapmamalı. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-008 | 156 | P1 | PASS | Gerçek emir yetkisi backend execution/risk katmanında kalmalı. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-009 | 156 | P1 | PASS | Server restart sonrası mevcut reconciliation kuralları zorunlu. | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-010 | 156 | P1 | PASS | LOCAL_DEMO = PAPER / geliştirici testi | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-011 | 156 | P1 | PASS | SERVER_PRODUCTION = 7/24 Linux host/VPS/dedicated server | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-156-012 | 156 | P1 | PASS | DESKTOP_CLIENT = server'a bağlanan Tauri shell; engine değildir | test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only |
| REQ-V51-157-001 | 157 | P1 | PASS | Bölüm 157 (FRONTEND STACK / STATE / REAL-TIME DELIVERY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-002 | 157 | P1 | PASS | React 19.x veya güncel uyumlu stable | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-003 | 157 | P1 | PASS | TypeScript strict | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-004 | 157 | P1 | PASS | Vite | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-005 | 157 | P1 | PASS | Material UI stable | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-006 | 157 | P1 | PASS | TanStack Query veya eşdeğer server-state cache | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-007 | 157 | P1 | PASS | küçük local UI state için hafif state store | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-008 | 157 | P1 | PASS | React Router veya eşdeğer typed routing | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-009 | 157 | P1 | PASS | REST ile initial snapshot | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-010 | 157 | P1 | PASS | authenticated WebSocket ile incremental event/update | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-011 | 157 | P1 | PASS | sequence/version ile out-of-order update koruması | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-012 | 157 | P1 | PASS | reconnect sonrası resync snapshot | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-157-013 | 157 | P1 | PASS | stale-data göstergesi | test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state |
| REQ-V51-158-001 | 158 | P1 | PASS | Bölüm 158 (INFORMATION ARCHITECTURE / NAVIGATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-002 | 158 | P1 | PASS | Ana Ekran | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-003 | 158 | P1 | PASS | Piyasa / Scanner | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-004 | 158 | P1 | PASS | Analiz | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-005 | 158 | P1 | PASS | Pozisyonlar & Emirler | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-006 | 158 | P1 | PASS | Alarmlar | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-007 | 158 | P1 | PASS | Backtest & Araştırma | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-008 | 158 | P1 | PASS | Performans & Risk | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-009 | 158 | P1 | PASS | Ayarlar / Sistem | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-158-010 | 158 | P1 | PASS | Exchange | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-011 | 158 | P1 | PASS | Telegram/Bildirim | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-012 | 158 | P1 | PASS | Risk | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-013 | 158 | P1 | PASS | Coin Universe | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-014 | 158 | P1 | PASS | Strategy | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-015 | 158 | P1 | PASS | Kullanıcı & Güvenlik | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-016 | 158 | P1 | PASS | Sistem Sağlığı | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-017 | 158 | P1 | PASS | Yedekleme | test_phase121_settings_information_architecture_exposes_required_domains |
| REQ-V51-158-018 | 158 | P1 | PASS | URL/deep-link state güvenli olmalı. | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-159-001 | 159 | P1 | PASS | Bölüm 159 (FIRST-RUN SETUP WIZARD) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-159-002 | 159 | P1 | PASS | İlk kullanım terminal dosyası düzenlemeye bağlı olmamalı. | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-003 | 159 | P1 | PASS | server health | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-004 | 159 | P1 | PASS | version | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-005 | 159 | P1 | PASS | database/redis readiness | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-006 | 159 | P1 | PASS | clock sync | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-007 | 159 | P1 | PASS | exchange seçimi | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-008 | 159 | P1 | PASS | API key / secret girişi | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-159-009 | 159 | P1 | PASS | connection test | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-010 | 159 | P1 | PASS | permission test | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-011 | 159 | P1 | PASS | withdrawal permission rejection | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-012 | 159 | P1 | PASS | account mode / market capability discovery | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-013 | 159 | P1 | PASS | token/chat id | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-014 | 159 | P1 | PASS | test message | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-015 | 159 | P1 | PASS | komut güvenlik durumu | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-016 | 159 | P1 | PASS | PAPER önerilen/default | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-159-017 | 159 | P1 | PASS | TESTNET | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-018 | 159 | P1 | PASS | LIVE kilitli veya gate durumu | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-019 | 159 | P1 | PASS | MUHAFAZAKÂR | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-020 | 159 | P1 | PASS | DENGELİ | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-021 | 159 | P1 | PASS | AGRESİF | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-022 | 159 | P1 | PASS | ÖZEL | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-023 | 159 | P1 | PASS | Ancak preset bir "sihirli risk" olmamalı. | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-024 | 159 | P1 | PASS | OTOMATİK UYGUNLUK = önerilen | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-025 | 159 | P1 | PASS | allowlist/blocklist | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-026 | 159 | P1 | PASS | quote asset | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-027 | 159 | P1 | PASS | max universe size | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-028 | 159 | P1 | PASS | new listing policy | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-029 | 159 | P1 | PASS | timezone | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-030 | 159 | P1 | PASS | number/date format | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-031 | 159 | P1 | PASS | language | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-032 | 159 | P1 | PASS | güvenlik checklist | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-033 | 159 | P1 | PASS | config summary | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-159-034 | 159 | P1 | PASS | secret dışındaki ayarların özeti | test_setup_api_persists_resume_sanitizes_secrets_and_forces_paper |
| REQ-V51-159-035 | 159 | P1 | PASS | PAPER MODE ile başlat | test_phase119_first_run_profile_covers_health_exchange_notification_risk_universe_locale_security_and_forces_paper |
| REQ-V51-160-001 | 160 | P1 | PASS | Bölüm 160 (HOME DASHBOARD / DAILY OPERATIONS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-002 | 160 | P1 | PASS | Mode: PAPER / TESTNET / LIVE | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-003 | 160 | P1 | PASS | Exchange: Connected/Degraded/Offline | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-004 | 160 | P1 | PASS | Market Data: Fresh/Stale | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-005 | 160 | P1 | PASS | Engine: Running/Halted/Reducing Only | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-006 | 160 | P1 | PASS | Risk: Normal/Restricted | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-007 | 160 | P1 | PASS | Server time + local display time | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-008 | 160 | P1 | PASS | Portfolio Value | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-009 | 160 | P1 | PASS | Daily P&L | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-010 | 160 | P1 | PASS | Open Risk | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-011 | 160 | P1 | PASS | Drawdown | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-012 | 160 | P1 | PASS | Open Positions | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-013 | 160 | P1 | PASS | Top Candidate | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-014 | 160 | P1 | PASS | Critical Alerts | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-015 | 160 | P1 | PASS | symbol | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-016 | 160 | P1 | PASS | signal | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-017 | 160 | P1 | PASS | score | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-018 | 160 | P1 | PASS | confidence | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-019 | 160 | P1 | PASS | regime | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-020 | 160 | P1 | PASS | net edge | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-160-021 | 160 | P1 | PASS | risk/block reason | test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason |
| REQ-V51-161-001 | 161 | P1 | PASS | Bölüm 161 (RESPONSIVE WEB / MOBILE / PWA) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll |
| REQ-V51-161-002 | 161 | P1 | PASS | Web UI desktop-first değil responsive-by-design olmalı. | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-003 | 161 | P1 | PASS | desktop wide | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-004 | 161 | P1 | PASS | laptop | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-005 | 161 | P1 | PASS | tablet landscape/portrait | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-006 | 161 | P1 | PASS | mobile | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-007 | 161 | P1 | PASS | büyük tablolar card/list mode'a dönüşebilmeli | test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll |
| REQ-V51-161-008 | 161 | P1 | PASS | kritik status üstte kalmalı | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-009 | 161 | P1 | PASS | grafik gesture/zoom çalışmalı | test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup |
| REQ-V51-161-010 | 161 | P1 | PASS | order/risk detayları okunabilir olmalı | test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll |
| REQ-V51-161-011 | 161 | P1 | PASS | yatay scroll zorunluluğu minimum olmalı | test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll |
| REQ-V51-161-012 | 161 | P1 | PASS | installable manifest | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-013 | 161 | P1 | PASS | app icons | test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll, test_phase121_pwa_manifest_has_installable_application_icons |
| REQ-V51-161-014 | 161 | P1 | PASS | offline shell yalnızca read-only cache için kullanılabilir | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-015 | 161 | P1 | PASS | service worker trading engine görevi ÜSTLENEMEZ | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-016 | 161 | P1 | PASS | offline iken LIVE işlem kontrolü yapılmamalı | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-161-017 | 161 | P1 | PASS | stale cached market data açık şekilde işaretlenmeli | test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety |
| REQ-V51-162-001 | 162 | P1 | PASS | Bölüm 162 (TAURI DESKTOP CLIENT — OPSİYONEL) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase134_tauri_shell_initializes_updater_plugin_but_real_build_and_signing_remain_unclaimed |
| REQ-V51-162-002 | 162 | P1 | PASS | mevcut React UI'yı paketler | test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities |
| REQ-V51-162-003 | 162 | P1 | PASS | server API/WebSocket'e güvenli bağlanır | test_phase130_desktop_api_boundary_requires_https_no_url_credentials_and_wss |
| REQ-V51-162-004 | 162 | P1 | PASS | native notification opsiyonel destekler | test_phase133_tauri_native_notification_is_opt_in_without_broad_client_permissions |
| REQ-V51-162-005 | 162 | P1 | PASS | auto-update mekanizması signature verification ile uygulanabilir | test_phase134_tauri_shell_initializes_updater_plugin_but_real_build_and_signing_remain_unclaimed |
| REQ-V51-162-006 | 162 | P1 | PASS | Exchange API secret'ı Tauri frontend webview içinde saklama. | test_phase130_optional_tauri_shell_packages_react_but_keeps_trading_server_side_and_minimal_capabilities |
| REQ-V51-162-007 | 162 | P1 | PASS | Client compromise tek başına withdrawal yetkisi veremez. | test_phase130_desktop_shell_has_no_execution_ownership_and_cannot_grant_withdrawal_by_client_compromise |
| REQ-V51-162-008 | 162 | P1 | PASS | Desktop app kapatılması açık pozisyon yönetimini durdurmaz. | test_phase130_desktop_shell_has_no_execution_ownership_and_cannot_grant_withdrawal_by_client_compromise |
| REQ-V51-162-009 | 162 | P1 | PASS | Client version / backend API compatibility kontrolü yap. | test_phase130_client_server_compatibility_is_fail_closed_for_high_risk_ui_boot |
| REQ-V51-162-010 | 162 | P1 | PASS | incompatible client'a high-risk action izni verme. | test_phase130_client_server_compatibility_is_fail_closed_for_high_risk_ui_boot |
| REQ-V51-163-001 | 163 | P1 | PASS | Bölüm 163 (HUMAN-READABLE STATUS / ERROR / RECOVERY UX) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-163-002 | 163 | P1 | PASS | Her sistem durumu teknik kod + kullanıcı mesajına sahip olmalı. | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-163-003 | 163 | P1 | PASS | ne oldu | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-163-004 | 163 | P1 | PASS | etkisi ne | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-163-005 | 163 | P1 | PASS | sistem otomatik ne yapıyor | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-163-006 | 163 | P1 | PASS | kullanıcıdan aksiyon gerekiyor mu | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-163-007 | 163 | P1 | PASS | correlation/event id | test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id |
| REQ-V51-164-001 | 164 | P1 | PASS | Bölüm 164 (HIGH-RISK ACTION UX / LIVE SAFETY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-002 | 164 | P1 | PASS | LIVE enable | test_live_requires_one_time_nonce_and_all_gates, test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-003 | 164 | P1 | PASS | AUTO_EXECUTION enable | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-004 | 164 | P1 | PASS | risk limit artırma | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-005 | 164 | P1 | PASS | max position artırma | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-006 | 164 | P1 | PASS | cross margin enable | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-007 | 164 | P1 | PASS | API credential değiştirme | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-008 | 164 | P1 | PASS | panic close | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-009 | 164 | P1 | PASS | manual LIVE order | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-010 | 164 | P1 | PASS | emergency stop override | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-011 | 164 | P1 | PASS | ZORUNLU UX: | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-012 | 164 | P1 | PASS | re-authentication / MFA uygun ise | test_live_requires_one_time_nonce_and_all_gates, test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-013 | 164 | P1 | PASS | ikinci confirmation ekranı | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-014 | 164 | P1 | PASS | mode + account + symbol + side + quantity + estimated notional | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-015 | 164 | P1 | PASS | fee/slippage tahmini | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-016 | 164 | P1 | PASS | risk amount / risk percent | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-017 | 164 | P1 | PASS | SL/TP/protection state | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-018 | 164 | P1 | PASS | açık uyarı | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-164-019 | 164 | P1 | PASS | audit reason | test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields |
| REQ-V51-165-001 | 165 | P1 | PASS | Bölüm 165 (ACCESSIBILITY / LOCALIZATION / VISUAL CONSISTENCY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase131_section165_accessibility_localization_contract_is_complete_at_source_level |
| REQ-V51-165-002 | 165 | P1 | PASS | WCAG 2.2 AA'ya mümkün olduğunca uyum | test_phase131_section165_accessibility_localization_contract_is_complete_at_source_level |
| REQ-V51-165-003 | 165 | P1 | PASS | keyboard navigation | test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text |
| REQ-V51-165-004 | 165 | P1 | PASS | visible focus state | test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text |
| REQ-V51-165-005 | 165 | P1 | PASS | semantic labels | test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text |
| REQ-V51-165-006 | 165 | P1 | PASS | screen-reader accessible form controls | test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text |
| REQ-V51-165-007 | 165 | P1 | PASS | contrast kontrolü | test_phase131_explicit_theme_tokens_meet_wcag_aa_core_contrast_budget |
| REQ-V51-165-008 | 165 | P1 | PASS | yalnızca renk ile anlam verme YASAK | test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text |
| REQ-V51-165-009 | 165 | P1 | PASS | error mesajları alanla ilişkilendirilmeli | test_phase125_login_error_is_programmatically_associated_with_field |
| REQ-V51-165-010 | 165 | P1 | PASS | Türkçe birinci sınıf dil desteği olmalı. | test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text |
| REQ-V51-166-001 | 166 | P1 | PASS | Bölüm 166 (FRONTEND SECURITY / SESSION / DATA PRIVACY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary |
| REQ-V51-166-002 | 166 | P1 | PASS | exchange secret görmemeli | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary, test_prod_websocket_requires_session |
| REQ-V51-166-003 | 166 | P1 | PASS | auth token'ı URL'ye yazmamalı | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary |
| REQ-V51-166-004 | 166 | P1 | PASS | localStorage'da long-lived sensitive token tutmamalı | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary, test_prod_websocket_requires_session |
| REQ-V51-166-005 | 166 | P1 | PASS | XSS/CSP kurallarına uymalı | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary |
| REQ-V51-166-006 | 166 | P1 | PASS | websocket auth expiry/reconnect yönetmeli | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary, test_private_stream_auth_expiry_requires_fresh_auth_before_healthy_reconnect, test_prod_websocket_requires_session |
| REQ-V51-166-007 | 166 | P1 | PASS | CSRF modeline uygun mutation koruması kullanmalı | test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary, test_prod_websocket_requires_session |
| REQ-V51-167-001 | 167 | P1 | NOT_TESTED | Bölüm 167 (FRONTEND PERFORMANCE / STABILITY BUDGET) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-167-002 | 167 | P1 | PASS | large scanner table virtualization | test_phase125_virtualized_rows_bounds_large_client_render_work |
| REQ-V51-167-003 | 167 | P1 | PASS | lazy route loading | test_phase107_information_architecture_has_core_navigation_and_safe_deep_links |
| REQ-V51-167-004 | 167 | P1 | PASS | chart data windowing/downsampling uygun ise | test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup |
| REQ-V51-167-005 | 167 | P1 | PASS | WebSocket update coalescing | test_backpressure_drops_low_when_full |
| REQ-V51-167-006 | 167 | P1 | PASS | memory leak test | test_phase132_frontend_realtime_state_memory_soak_has_bounded_heap_growth |
| REQ-V51-167-007 | 167 | P1 | PASS | unmounted component subscription cleanup | test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup |
| REQ-V51-167-008 | 167 | P1 | PASS | reconnect storm protection | test_backpressure_drops_low_when_full |
| REQ-V51-167-009 | 167 | P1 | PASS | bounded client caches | test_backpressure_drops_low_when_full |
| REQ-V51-167-010 | 167 | P1 | NOT_TESTED | dashboard first meaningful render |  |
| REQ-V51-167-011 | 167 | P1 | NOT_TESTED | scanner interaction latency |  |
| REQ-V51-167-012 | 167 | P1 | NOT_TESTED | chart update latency |  |
| REQ-V51-167-013 | 167 | P1 | PASS | websocket message backlog | test_backpressure_drops_low_when_full |
| REQ-V51-167-014 | 167 | P1 | NOT_TESTED | browser memory after soak |  |
| REQ-V51-168-001 | 168 | P1 | NOT_TESTED | Bölüm 168 (UI / UX / E2E ACCEPTANCE TESTLERİ) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-168-002 | 168 | P1 | NOT_TESTED | Vitest/Jest + React Testing Library veya eşdeğer |  |
| REQ-V51-168-003 | 168 | P1 | NOT_TESTED | form validation |  |
| REQ-V51-168-004 | 168 | P1 | NOT_TESTED | permissions |  |
| REQ-V51-168-005 | 168 | P1 | NOT_TESTED | state mapping |  |
| REQ-V51-168-006 | 168 | P1 | NOT_TESTED | risk summary |  |
| REQ-V51-168-007 | 168 | P1 | NOT_TESTED | number/precision display |  |
| REQ-V51-168-008 | 168 | P1 | NOT_TESTED | login/logout/session expiry |  |
| REQ-V51-168-009 | 168 | P1 | NOT_TESTED | first-run wizard |  |
| REQ-V51-168-010 | 168 | P1 | NOT_TESTED | invalid exchange credential |  |
| REQ-V51-168-011 | 168 | P1 | NOT_TESTED | withdrawal permission rejection |  |
| REQ-V51-168-012 | 168 | P1 | NOT_TESTED | PAPER default |  |
| REQ-V51-168-013 | 168 | P1 | NOT_TESTED | scanner load/filter/sort |  |
| REQ-V51-168-014 | 168 | P1 | NOT_TESTED | per-asset analysis navigation |  |
| REQ-V51-168-015 | 168 | P1 | PASS | stale-data banner | test_phase134_stale_data_banner_state_is_executed_with_local_typescript_fixture |
| REQ-V51-168-016 | 168 | P1 | NOT_TESTED | WebSocket disconnect/reconnect/resync |  |
| REQ-V51-168-017 | 168 | P1 | NOT_TESTED | open position display |  |
| REQ-V51-168-018 | 168 | P1 | NOT_TESTED | SL/TP marker display |  |
| REQ-V51-168-019 | 168 | P1 | NOT_TESTED | LIVE enable blocked by gate |  |
| REQ-V51-168-020 | 168 | P1 | NOT_TESTED | successful controlled LIVE approval flow using mock/testnet |  |
| REQ-V51-168-021 | 168 | P1 | NOT_TESTED | double-click/duplicate submit protection |  |
| REQ-V51-168-022 | 168 | P1 | NOT_TESTED | risk setting increase confirmation |  |
| REQ-V51-168-023 | 168 | P1 | NOT_TESTED | panic close confirmation using testnet/mock |  |
| REQ-V51-168-024 | 168 | P1 | NOT_TESTED | mobile navigation |  |
| REQ-V51-168-025 | 168 | P1 | NOT_TESTED | accessibility smoke |  |
| REQ-V51-168-026 | 168 | P1 | NOT_TESTED | Chromium/Chrome current |  |
| REQ-V51-168-027 | 168 | P1 | NOT_TESTED | Edge current |  |
| REQ-V51-168-028 | 168 | P1 | NOT_TESTED | Firefox current |  |
| REQ-V51-168-029 | 168 | P1 | NOT_TESTED | WebKit/Safari equivalent through supported E2E tooling |  |
| REQ-V51-168-030 | 168 | P1 | NOT_TESTED | 1920x1080 |  |
| REQ-V51-168-031 | 168 | P1 | NOT_TESTED | common laptop width |  |
| REQ-V51-168-032 | 168 | P1 | NOT_TESTED | tablet |  |
| REQ-V51-168-033 | 168 | P1 | NOT_TESTED | representative mobile |  |
| REQ-V51-168-034 | 168 | P1 | NOT_TESTED | core dashboard |  |
| REQ-V51-168-035 | 168 | P1 | NOT_TESTED | scanner |  |
| REQ-V51-168-036 | 168 | P1 | NOT_TESTED | asset analysis |  |
| REQ-V51-168-037 | 168 | P1 | NOT_TESTED | LIVE warning modal |  |
| REQ-V51-168-038 | 168 | P1 | NOT_TESTED | critical error banner |  |
| REQ-V51-169-001 | 169 | P1 | PASS | Bölüm 169 (PACKAGING / UPDATE / ROLLBACK / USER DELIVERY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-169-002 | 169 | P1 | PASS | Docker Compose | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-003 | 169 | P1 | PASS | migration | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-004 | 169 | P1 | PASS | backup/restore | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-005 | 169 | P1 | PASS | health checks | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-006 | 169 | P1 | PASS | reverse proxy/TLS guide | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-007 | 169 | P1 | NOT_TESTED | production static build |  |
| REQ-V51-169-008 | 169 | P1 | PASS | versioned assets | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-009 | 169 | P1 | PASS | compatibility metadata | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-010 | 169 | P1 | NOT_TESTED | signed installer/package mümkünse |  |
| REQ-V51-169-011 | 169 | P1 | PASS | version display | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-012 | 169 | P1 | PASS | server compatibility check | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-013 | 169 | P1 | PASS | signed auto-update veya açık manuel update süreci | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-169-014 | 169 | P1 | PASS | database migration backup öncesi kontrol | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-015 | 169 | P1 | PASS | rolling/restart prosedürü | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-016 | 169 | P1 | PASS | backward compatibility window | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-017 | 169 | P1 | PASS | rollback plan | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-018 | 169 | P1 | PASS | config migration | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-019 | 169 | P1 | PASS | frontend/backend API version compatibility | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-020 | 169 | P1 | PASS | Hızlı Başlangıç Kılavuzu | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-021 | 169 | P1 | PASS | İlk Kurulum Kılavuzu | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-022 | 169 | P1 | PASS | PAPER Kullanım Kılavuzu | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-023 | 169 | P1 | PASS | LIVE Güvenlik Kılavuzu | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-024 | 169 | P1 | PASS | Sorun Giderme | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-025 | 169 | P1 | PASS | Backup/Restore | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-169-026 | 169 | P1 | PASS | Acil Durum Prosedürü | test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks |
| REQ-V51-170-001 | 170 | P1 | PASS | Bölüm 170 (SON KURAL) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase134_final_system_conformance_keeps_real_code_local_fixture_boundary_and_paper_default |
| REQ-V51-170-002 | 170 | P1 | PASS | PROFESYONEL, KULLANICI DOSTU, RESPONSIVE, DENETLENEBİLİR, TEST EDİLEBİLİR, GÜVENLİ, MODÜLER, 7/24 SERVER-SIDE ÇALIŞAN, WEB/PWA VE OPSİYONEL TAURI İSTEMCİLİ, MULTI-ASSET, POINT-IN-TIME VERİ VE POINT-IN-TIME UNIVERSE ZAMANLAMASINI KONTROL EDEN, BACKTEST + PURGED/EMBARGO VALIDATION + WALK-FORWARD + PAPER + TESTNET + LIVE-SHADOW + LIVE MODLARI OLAN, TELEGRAM BİLDİRİMLİ, DİNAMİK COIN EVRENİ / LİKİDİTE FİLTRELERİ / CROSS-SECTIONAL SCANNER / STOP LOSS / TAKE PROFIT / TRAILING STOP / COST-AWARE EXPECTANCY / POSITION SIZING / KORELASYON-KONSANTRASYON KONTROLLÜ DRAWDOWN-ADAPTIVE PORTFÖY RİSK YÖNETİMİ / CIRCUIT BREAKER / ORDER RECONCILIATION / MODEL HEALTH / AUDIT LOG / DISASTER RECOVERY / PERFORMANCE ATTRIBUTION özelliklerine sahip tam teşekküllü bir kripto algorithmic trading platformudur. | test_phase134_final_system_conformance_keeps_real_code_local_fixture_boundary_and_paper_default |
| REQ-V51-170-003 | 170 | P1 | PASS | SONRA PROJEYİ OLUŞTUR. | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-004 | 170 | P1 | PASS | oluşturulan dosyaların tamamını listele | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-005 | 170 | P1 | PASS | nasıl kurulacağını anlat | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-006 | 170 | P1 | PASS | hangi testlerin geçtiğini listele | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-007 | 170 | P1 | PASS | hangi özelliklerin gerçek, hangilerinin mock olduğunu belirt | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-008 | 170 | P1 | PASS | backtest sonuçlarını raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-009 | 170 | P1 | PASS | OOS / walk-forward / purged-embargo sonuçlarını raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-010 | 170 | P1 | PASS | multiple-testing / DSR kanıtını raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-011 | 170 | P1 | PASS | paper trading durumunu raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-012 | 170 | P1 | PASS | testnet durumunu raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-013 | 170 | P1 | PASS | live-shadow durumunu raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-014 | 170 | P1 | PASS | execution ve PnL attribution raporunu ver | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-015 | 170 | P1 | PASS | effective sample size ve confidence interval raporunu ver | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-016 | 170 | P1 | PASS | LIVE trading'in neden varsayılan olarak kapalı olduğunu belirt | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-017 | 170 | P1 | PASS | UI/UX acceptance test sonuçlarını raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-018 | 170 | P1 | PASS | browser/viewport test matrisini raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-019 | 170 | P1 | PASS | ilk kurulum sihirbazı testini raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-020 | 170 | P1 | PASS | web/PWA build durumunu raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-021 | 170 | P1 | PASS | Tauri masaüstü istemcisi üretildiyse build/signing durumunu raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-022 | 170 | P1 | PASS | frontend/backend version compatibility durumunu raporla | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-023 | 170 | P1 | PASS | kullanıcı kılavuzlarının yerini belirt | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-024 | 170 | P1 | PASS | SİSTEM İLK ÇALIŞTIRMADA PAPER MODE'DA OLMALI. | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-170-025 | 170 | P1 | PASS | AMA TÜM LIVE TRADING KODU VE ADAPTERI HAZIR OLMALI. | test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance |
| REQ-V51-171-001 | 171 | P0 | PASS | Bölüm 171 (V5.1 PRODUCTION-HARDENING OVERRIDE / REQUIREMENT PRECEDENCE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-171-002 | 171 | P0 | PASS | Sermaye ve açık pozisyon güvenliği | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-171-003 | 171 | P0 | PASS | Exchange/account gerçekliği ve execution correctness | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-171-004 | 171 | P0 | PASS | Veri bütünlüğü / point-in-time doğruluk | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-171-005 | 171 | P0 | PASS | Kimlik, secret ve erişim güvenliği | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-171-006 | 171 | P0 | PASS | Muhasebe / ledger / audit doğruluğu | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-171-007 | 171 | P0 | PASS | Deterministik recovery ve replay | test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift, test_runtime_checkpoint_signed_and_restore_requires_exact_config_event_state |
| REQ-V51-171-008 | 171 | P0 | PASS | İstatistiksel geçerlilik | test_advanced_research_validation_covers_oos_walkforward_stresses_regimes_psr_dsr_bootstrap_and_multiple_testing |
| REQ-V51-171-009 | 171 | P0 | PASS | Kullanılabilirlik / performans / UX | test_phase21_production_hardening_precedence_prefers_capital_exchange_data_identity_ledger_over_ux |
| REQ-V51-172-001 | 172 | P0 | PASS | Bölüm 172 (CANONICAL IMPLEMENTATION PROFILE / ARCHITECTURE DECISIONS) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-002 | 172 | P0 | PASS | KOD YAZMADAN ÖNCE zorunlu olarak: | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-003 | 172 | P0 | PASS | oluştur. | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-004 | 172 | P0 | PASS | Python package/dependency manager | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-005 | 172 | P0 | PASS | async/runtime yaklaşımı | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-006 | 172 | P0 | PASS | scheduler / worker modeli | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-007 | 172 | P0 | PASS | event bus / internal queue yaklaşımı | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-008 | 172 | P0 | PASS | PostgreSQL bağlantı/pooling yöntemi | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-009 | 172 | P0 | PASS | Redis kullanım amacı ve persistence beklentisi | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-010 | 172 | P0 | PASS | reverse proxy seçimi | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-011 | 172 | P0 | PASS | frontend package manager | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-012 | 172 | P0 | PASS | test frameworkleri | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-013 | 172 | P0 | PASS | auth/session modeli | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-014 | 172 | P0 | PASS | secret provider | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-015 | 172 | P0 | PASS | deployment profile | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-016 | 172 | P0 | PASS | backup profile | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-017 | 172 | P0 | PASS | observability stack | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-018 | 172 | P0 | PASS | supported exchange + market type matrisi | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-019 | 172 | P0 | PASS | ADR_ID | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-020 | 172 | P0 | PASS | selected_option | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-021 | 172 | P0 | PASS | alternatives_considered | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-022 | 172 | P0 | PASS | rationale | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-023 | 172 | P0 | PASS | operational_tradeoff | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-024 | 172 | P0 | PASS | security_tradeoff | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-025 | 172 | P0 | PASS | rollback/migration impact | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-172-026 | 172 | P0 | PASS | sakla. | test_canonical_architecture_profile_and_adrs_cover_required_decision_fields |
| REQ-V51-173-001 | 173 | P0 | PASS | Bölüm 173 (EXCHANGE ACCOUNT BOUNDARY / SUBACCOUNT / EXTERNAL ACTIVITY DETECTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_external_balance_change_requires_review |
| REQ-V51-173-002 | 173 | P0 | PASS | exchange_account_id | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-003 | 173 | P0 | PASS | exchange | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-004 | 173 | P0 | PASS | account/subaccount identifier veya güvenli fingerprint | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-005 | 173 | P0 | PASS | market_type | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-006 | 173 | P0 | PASS | margin_mode | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-007 | 173 | P0 | PASS | position_mode | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-008 | 173 | P0 | PASS | capabilities | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-009 | 173 | P0 | PASS | permission snapshot | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-010 | 173 | P0 | PASS | API key fingerprint | test_exchange_account_boundary_includes_margin_position_permission_identity |
| REQ-V51-173-011 | 173 | P0 | PASS | created_at | test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace |
| REQ-V51-173-012 | 173 | P0 | PASS | last_reconciled_at | test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace |
| REQ-V51-173-013 | 173 | P0 | PASS | status | test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace |
| REQ-V51-173-014 | 173 | P0 | PASS | Manuel trading veya başka botlar aynı hesapta varsayılan olarak kullanılmamalıdır. | test_unknown_exchange_order_is_never_silently_adopted |
| REQ-V51-173-015 | 173 | P0 | PASS | Bot-owned order'ları deterministic client_order_id namespace ile tanımla. | test_phase21_account_lifecycle_tracks_created_reconciled_status_and_deterministic_namespace |
| REQ-V51-173-016 | 173 | P0 | PASS | Sürekli ACCOUNT_DRIFT_DETECTION yap: | test_external_activity_detects_balance_position_and_order_drift |
| REQ-V51-173-017 | 173 | P0 | PASS | bilinmeyen açık emir | test_external_activity_detects_balance_position_and_order_drift |
| REQ-V51-173-018 | 173 | P0 | PASS | bilinmeyen fill/trade | test_unknown_submit_resolves_from_fill_truth_and_otherwise_manual_reviews |
| REQ-V51-173-019 | 173 | P0 | PASS | bot ledger'ı ile açıklanamayan balance değişimi | test_external_activity_detects_balance_position_and_order_drift |
| REQ-V51-173-020 | 173 | P0 | PASS | position quantity drift | test_external_activity_detects_balance_position_and_order_drift |
| REQ-V51-173-021 | 173 | P0 | PASS | external transfer | test_external_balance_change_requires_review, test_unknown_exchange_order_is_never_silently_adopted |
| REQ-V51-173-022 | 173 | P0 | PASS | manual trade | test_external_balance_change_requires_review, test_unknown_exchange_order_is_never_silently_adopted |
| REQ-V51-173-023 | 173 | P0 | PASS | başka API key kaynaklı activity mümkünse | test_external_activity_detects_balance_position_and_order_drift |
| REQ-V51-173-024 | 173 | P0 | PASS | Reconciliation sonucunu immutable audit event olarak sakla. | test_reconciliation_result_is_bound_to_immutable_audit_chain |
| REQ-V51-174-001 | 174 | P0 | PASS | Bölüm 174 (STRATEGY POSITION OWNERSHIP / VIRTUAL SLEEVES / LOT ATTRIBUTION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-002 | 174 | P0 | PASS | Tanımla: | test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-003 | 174 | P0 | PASS | account-level net position | test_account_level_net_position_aggregates_all_sources, test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-004 | 174 | P0 | PASS | strategy virtual sleeve | test_strategy_ownership_prevents_cross_exit, test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-005 | 174 | P0 | PASS | strategy allocation lot | test_strategy_ownership_prevents_cross_exit, test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-006 | 174 | P0 | PASS | entry/fill attribution | test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-007 | 174 | P0 | PASS | realized PnL attribution | test_strategy_ownership_prevents_cross_exit, test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-008 | 174 | P0 | PASS | fee/funding attribution | test_strategy_virtual_sleeves_attribute_entries_pnl_fees_funding_and_account_net |
| REQ-V51-174-009 | 174 | P0 | PASS | netting policy | test_strategy_sleeve_conflict_policy_blocks_cross_strategy_exit_and_unapproved_transfer |
| REQ-V51-174-010 | 174 | P0 | PASS | hedging policy market type destekliyorsa | test_strategy_sleeve_hedging_policy_is_explicit_and_fail_closed_when_unsupported |
| REQ-V51-174-011 | 174 | P0 | PASS | ownership transfer policy | test_strategy_sleeve_conflict_policy_blocks_cross_strategy_exit_and_unapproved_transfer |
| REQ-V51-174-012 | 174 | P0 | PASS | conflict policy | test_strategy_sleeve_conflict_policy_blocks_cross_strategy_exit_and_unapproved_transfer |
| REQ-V51-175-001 | 175 | P0 | PASS | Bölüm 175 (SELF-TRADE PREVENTION / ORDER-INTENT CONFLICT CONTROL) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_capabilities_are_discovered_not_assumed, test_self_trade_prevention_blocks_crossing_platform_order |
| REQ-V51-175-002 | 175 | P0 | PASS | Aynı account/symbol üzerinde platformun kendi emirlerinin birbirine karşı işlem yapmasını engelle. | test_self_trade_prevention_blocks_crossing_platform_order |
| REQ-V51-175-003 | 175 | P0 | PASS | Exchange resmi olarak Self-Trade Prevention (STP) destekliyorsa capability discovery yap ve desteklenen STP mode'larını kaydet. | test_capabilities_are_discovered_not_assumed, test_self_trade_prevention_blocks_crossing_platform_order |
| REQ-V51-175-004 | 175 | P0 | PASS | opposite-side live order | test_capabilities_are_discovered_not_assumed |
| REQ-V51-175-005 | 175 | P0 | PASS | overlapping stop/TP | test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only |
| REQ-V51-175-006 | 175 | P0 | PASS | stale replace order | test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only |
| REQ-V51-175-007 | 175 | P0 | PASS | strategy conflict | test_capabilities_are_discovered_not_assumed |
| REQ-V51-175-008 | 175 | P0 | PASS | cancel/replace race | test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only |
| REQ-V51-175-009 | 175 | P0 | PASS | reduce-only conflict | test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only |
| REQ-V51-175-010 | 175 | P0 | PASS | uygula. | test_phase21_protective_order_conflicts_cover_overlap_stale_replace_cancel_race_and_reduce_only |
| REQ-V51-176-001 | 176 | P0 | PASS | Bölüm 176 (DOMAIN EVENT SCHEMA VERSIONING / REPLAY COMPATIBILITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_replay_gap_hard_fails |
| REQ-V51-176-002 | 176 | P0 | PASS | event_id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-003 | 176 | P0 | PASS | event_type | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-004 | 176 | P0 | PASS | schema_version | test_replay_gap_hard_fails |
| REQ-V51-176-005 | 176 | P0 | PASS | aggregate_id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-006 | 176 | P0 | PASS | correlation_id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-007 | 176 | P0 | PASS | causation_id | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-008 | 176 | P0 | PASS | sequence | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-009 | 176 | P0 | PASS | event_time | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-010 | 176 | P0 | PASS | received_at | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-011 | 176 | P0 | PASS | producer_version | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-012 | 176 | P0 | PASS | payload_hash | test_domain_event_record_contains_required_audit_and_replay_fields |
| REQ-V51-176-013 | 176 | P0 | PASS | backward-compatible event reader | test_replay_gap_hard_fails |
| REQ-V51-176-014 | 176 | P0 | PASS | schema registry veya açık event schema dizini | test_event_schema_registry_tolerates_additive_unknown_fields_but_requires_semantics |
| REQ-V51-176-015 | 176 | P0 | PASS | event upcaster/migration | test_event_schema_upcaster_requires_registered_latest_schema, test_replay_gap_hard_fails |
| REQ-V51-176-016 | 176 | P0 | PASS | replay compatibility test | test_replay_gap_hard_fails |
| REQ-V51-176-017 | 176 | P0 | PASS | unknown-field tolerance uygun yerlerde | test_event_schema_registry_tolerates_additive_unknown_fields_but_requires_semantics |
| REQ-V51-176-018 | 176 | P0 | PASS | required semantic change için hard fail + manual migration | test_event_schema_registry_tolerates_additive_unknown_fields_but_requires_semantics, test_event_schema_upcaster_requires_registered_latest_schema |
| REQ-V51-177-001 | 177 | P0 | PASS | Bölüm 177 (DEAD-LETTER / POISON EVENT / RETRY BUDGET) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow |
| REQ-V51-177-002 | 177 | P0 | PASS | Kritik event consumer sonsuz retry loop'a girmemelidir. | test_retry_policy_is_bounded_classified_and_jittered |
| REQ-V51-177-003 | 177 | P0 | PASS | retry policy | test_outbox_failure_to_dlq |
| REQ-V51-177-004 | 177 | P0 | PASS | max attempts | test_dead_letter_schema_contains_forensic_retry_fields, test_outbox_failure_to_dlq |
| REQ-V51-177-005 | 177 | P0 | PASS | exponential backoff | test_outbox_failure_to_dlq |
| REQ-V51-177-006 | 177 | P0 | PASS | jitter | test_retry_policy_is_bounded_classified_and_jittered |
| REQ-V51-177-007 | 177 | P0 | PASS | retryable/non-retryable error classification | test_retry_policy_is_bounded_classified_and_jittered |
| REQ-V51-177-008 | 177 | P0 | PASS | idempotency key | test_outbox_failure_to_dlq |
| REQ-V51-177-009 | 177 | P0 | PASS | retry metric | test_retry_policy_is_bounded_classified_and_jittered |
| REQ-V51-177-010 | 177 | P0 | PASS | tanımla. | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-011 | 177 | P0 | PASS | İşlenemeyen event için quarantine / DEAD_LETTER_QUEUE veya eşdeğer durable mekanizma oluştur. | test_outbox_failure_to_dlq |
| REQ-V51-177-012 | 177 | P0 | PASS | original_event_id | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-013 | 177 | P0 | PASS | event_type/schema_version | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-014 | 177 | P0 | PASS | payload reference/hash | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-015 | 177 | P0 | PASS | failure reason | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-016 | 177 | P0 | PASS | stack/error correlation id | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-017 | 177 | P0 | PASS | attempts | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-018 | 177 | P0 | PASS | first_failed_at | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-019 | 177 | P0 | PASS | last_failed_at | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-020 | 177 | P0 | PASS | consumer_version | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-021 | 177 | P0 | PASS | resolution state | test_dead_letter_schema_contains_forensic_retry_fields |
| REQ-V51-177-022 | 177 | P0 | PASS | inspect | test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow |
| REQ-V51-177-023 | 177 | P0 | PASS | fix/migrate | test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow |
| REQ-V51-177-024 | 177 | P0 | PASS | safe replay | test_deterministic_replay_checkpoint_detects_state_or_event_chain_drift, test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow |
| REQ-V51-177-025 | 177 | P0 | PASS | mark resolved | test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow |
| REQ-V51-177-026 | 177 | P0 | PASS | akışı oluştur. | test_dlq_operator_inspect_migrate_safe_replay_and_resolve_flow |
| REQ-V51-178-001 | 178 | P0 | NOT_TESTED | Bölüm 178 (BACKUP / RPO / RTO / PITR / RESTORE DRILL) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-178-002 | 178 | P0 | PASS | Production deployment için açık hedefler tanımla: | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-003 | 178 | P0 | PASS | RPO (Recovery Point Objective) | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-004 | 178 | P0 | PASS | RTO (Recovery Time Objective) | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-005 | 178 | P0 | PASS | backup frequency | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-006 | 178 | P0 | PASS | retention policy | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-007 | 178 | P0 | PASS | off-host/off-machine copy | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-008 | 178 | P0 | PASS | encryption at rest | test_backup_crypto_detects_tampering |
| REQ-V51-178-009 | 178 | P0 | PASS | access control | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-010 | 178 | P0 | PASS | integrity verification | test_backup_crypto_detects_tampering |
| REQ-V51-178-011 | 178 | P0 | PASS | PostgreSQL için production profile'da mümkünse Point-in-Time Recovery (PITR) destekle veya managed database eşdeğeri kullan. | test_backup_recovery_policy_enforces_rpo_rto_frequency_retention_and_offhost_controls |
| REQ-V51-178-012 | 178 | P0 | NOT_TESTED | Zorunlu periyodik RESTORE DRILL: |  |
| REQ-V51-178-013 | 178 | P0 | NOT_TESTED | izole test ortamı aç |  |
| REQ-V51-178-014 | 178 | P0 | NOT_TESTED | backup/PITR restore et |  |
| REQ-V51-178-015 | 178 | P0 | NOT_TESTED | migration/schema doğrula |  |
| REQ-V51-178-016 | 178 | P0 | PASS | ledger/order/fill referential integrity test et | test_execution_referential_integrity_accepts_valid_order_fill_ledger |
| REQ-V51-178-017 | 178 | P0 | NOT_TESTED | checksums/evidence doğrula |  |
| REQ-V51-178-018 | 178 | P0 | NOT_TESTED | uygulama read-only smoke test çalıştır |  |
| REQ-V51-178-019 | 178 | P0 | NOT_TESTED | sonuç raporla |  |
| REQ-V51-179-001 | 179 | P0 | PASS | Bölüm 179 (EXTERNAL WATCHDOG / ALERT REDUNDANCY / HEARTBEAT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-002 | 179 | P0 | PASS | Bu nedenle trading engine'den bağımsız external watchdog mekanizması oluştur. | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-003 | 179 | P0 | PASS | process heartbeat | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-004 | 179 | P0 | PASS | /health | test_phase22_health_and_ready_are_separate_and_readiness_fails_closed |
| REQ-V51-179-005 | 179 | P0 | PASS | /ready | test_phase22_health_and_ready_are_separate_and_readiness_fails_closed |
| REQ-V51-179-006 | 179 | P0 | PASS | last market data age | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-007 | 179 | P0 | PASS | private stream age | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-008 | 179 | P0 | PASS | risk state | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-009 | 179 | P0 | PASS | last reconciliation time | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-010 | 179 | P0 | PASS | outbox backlog | test_external_watchdog_validates_signature_freshness_data_stream_and_backlog |
| REQ-V51-179-011 | 179 | P0 | PASS | Critical alert channel tek Telegram'a bağımlı olmamalı. | test_alert_fallback |
| REQ-V51-179-012 | 179 | P0 | PASS | Configurable fallback destekle: | test_alert_fallback |
| REQ-V51-179-013 | 179 | P0 | PASS | email | test_secondary_alert_channels_are_transport_injected_and_fail_closed |
| REQ-V51-179-014 | 179 | P0 | PASS | webhook | test_secondary_alert_channels_are_transport_injected_and_fail_closed |
| REQ-V51-179-015 | 179 | P0 | PASS | web push veya eşdeğer güvenilir ikinci kanal | test_secondary_alert_channels_are_transport_injected_and_fail_closed |
| REQ-V51-179-016 | 179 | P0 | PASS | Notification sistemi trade state source-of-truth değildir; ancak kritik uyarı kanallarının tamamı çalışmıyorsa health degraded görünmelidir. | test_alert_escalation_survives_restart_and_stops_after_ack |
| REQ-V51-180-001 | 180 | P0 | PASS | Bölüm 180 (USER IDENTITY / PASSWORD HASHING / MFA RECOVERY SECURITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_recovery_token_expires_and_wrong_principal_fails_closed |
| REQ-V51-180-002 | 180 | P0 | PASS | Argon2id veya implementasyon anındaki güncel güvenilir memory-hard password hashing standardı | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-003 | 180 | P0 | PASS | unique salt | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-004 | 180 | P0 | PASS | güvenli work-factor/config | test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract |
| REQ-V51-180-005 | 180 | P0 | PASS | constant-time verification uygun yerde | test_privileged_recovery_requires_mfa_and_admin_approval_and_is_one_time |
| REQ-V51-180-006 | 180 | P0 | PASS | password hash upgrade-on-login stratejisi | test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract |
| REQ-V51-180-007 | 180 | P0 | PASS | enrollment confirmation | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-008 | 180 | P0 | PASS | recovery code'ları yalnızca hash'li saklama | test_mfa_login_and_single_use_recovery, test_recovery_token_expires_and_wrong_principal_fails_closed |
| REQ-V51-180-009 | 180 | P0 | PASS | tek kullanımlık recovery semantics | test_privileged_recovery_requires_mfa_and_admin_approval_and_is_one_time, test_recovery_token_expires_and_wrong_principal_fails_closed |
| REQ-V51-180-010 | 180 | P0 | PASS | re-authentication | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-011 | 180 | P0 | PASS | MFA reset audit | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-012 | 180 | P0 | PASS | admin/trader için güçlü recovery policy | test_privileged_recovery_requires_mfa_and_admin_approval_and_is_one_time, test_recovery_token_expires_and_wrong_principal_fails_closed |
| REQ-V51-180-013 | 180 | P0 | PASS | tanımla. | test_phase22_password_policy_requires_safe_work_factor_and_upgrade_on_login_contract |
| REQ-V51-180-014 | 180 | P0 | PASS | high entropy | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-015 | 180 | P0 | PASS | short-lived | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-016 | 180 | P0 | PASS | single-use | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-017 | 180 | P0 | PASS | hashed at rest uygun ise | test_mfa_login_and_single_use_recovery |
| REQ-V51-180-018 | 180 | P0 | PASS | replay protected | test_mfa_login_and_single_use_recovery |
| REQ-V51-181-001 | 181 | P0 | PASS | Bölüm 181 (TAMPER-EVIDENT AUDIT / EVIDENCE INTEGRITY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_database_audit_detects_tampering |
| REQ-V51-181-002 | 181 | P0 | PASS | Immutable audit log kavramsal olarak yeterli değildir; kritik production evidence sonradan değiştirilip değiştirilmediği doğrulanabilir olmalıdır. | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-003 | 181 | P0 | PASS | LIVE mode enable/disable | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-004 | 181 | P0 | PASS | risk limit değişikliği | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-005 | 181 | P0 | PASS | API credential metadata değişikliği | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-006 | 181 | P0 | PASS | order intent | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-007 | 181 | P0 | PASS | order/fill reconciliation | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-008 | 181 | P0 | PASS | manual/external activity acceptance | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-009 | 181 | P0 | PASS | panic close | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-010 | 181 | P0 | PASS | strategy promotion | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-011 | 181 | P0 | PASS | deployment/release | test_worm_audit_export_covers_all_critical_actions_and_detects_tampering |
| REQ-V51-181-012 | 181 | P0 | PASS | olaylarında tamper-evident yaklaşım kullan. | test_database_audit_detects_tampering |
| REQ-V51-181-013 | 181 | P0 | PASS | hash chain | test_database_audit_detects_tampering |
| REQ-V51-181-014 | 181 | P0 | PASS | Merkle/checkpoint yaklaşımı | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-015 | 181 | P0 | PASS | signed periodic checkpoint | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-016 | 181 | P0 | NOT_TESTED | append-only/WORM-capable storage |  |
| REQ-V51-181-017 | 181 | P0 | PASS | previous_hash/reference | test_database_audit_detects_tampering |
| REQ-V51-181-018 | 181 | P0 | PASS | current_hash | test_database_audit_detects_tampering |
| REQ-V51-181-019 | 181 | P0 | PASS | actor | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-020 | 181 | P0 | PASS | action | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-021 | 181 | P0 | PASS | object | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-022 | 181 | P0 | PASS | correlation id | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-023 | 181 | P0 | PASS | timestamp | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-024 | 181 | P0 | PASS | reason | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-025 | 181 | P0 | PASS | release/version | test_signed_merkle_checkpoint_detects_record_or_chain_tampering_and_captures_required_audit_fields |
| REQ-V51-181-026 | 181 | P0 | PASS | Audit verification CLI/test oluştur. | test_database_audit_detects_tampering |
| REQ-V51-182-001 | 182 | P0 | PASS | Bölüm 182 (DEV / TEST / STAGING / PROD ENVIRONMENT SEPARATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_nonprod_live_forbidden |
| REQ-V51-182-002 | 182 | P0 | PASS | ayrımı oluştur. | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-182-003 | 182 | P0 | PASS | ZORUNLU ISOLATION: | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-182-004 | 182 | P0 | PASS | ayrı DB/schema veya instance | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-182-005 | 182 | P0 | PASS | ayrı Redis namespace/instance uygun ise | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-182-006 | 182 | P0 | PASS | ayrı secrets | test_nonprod_live_forbidden |
| REQ-V51-182-007 | 182 | P0 | PASS | ayrı exchange credentials | test_nonprod_live_forbidden |
| REQ-V51-182-008 | 182 | P0 | PASS | ayrı Telegram/webhook endpoints mümkünse | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-182-009 | 182 | P0 | PASS | ayrı encryption keys production için | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-182-010 | 182 | P0 | PASS | STAGING production'a mümkün olduğunca benzer olmalı fakat gerçek sermaye kullanmamalıdır. | test_environment_isolation_rejects_shared_security_boundaries_and_nonprod_capital |
| REQ-V51-183-001 | 183 | P0 | PASS | Bölüm 183 (DATABASE MIGRATION SAFETY / EXPAND-CONTRACT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_immutable_initial_migration_matches_runtime_table_set |
| REQ-V51-183-002 | 183 | P0 | PASS | Production schema değişikliklerinde varsayılan: | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-003 | 183 | P0 | PASS | yaklaşımı kullan. | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-004 | 183 | P0 | PASS | backward compatible migration window | test_immutable_initial_migration_matches_runtime_table_set |
| REQ-V51-183-005 | 183 | P0 | PASS | pre-migration backup/checkpoint | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-006 | 183 | P0 | PASS | schema compatibility test old/new app version ile | test_immutable_initial_migration_matches_runtime_table_set |
| REQ-V51-183-007 | 183 | P0 | PASS | large-table migration time/lock assessment | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-008 | 183 | P0 | PASS | online index creation uygun ise | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-009 | 183 | P0 | PASS | backfill throttling | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-010 | 183 | P0 | PASS | migration observability | test_production_migration_plan_requires_expand_contract_checkpoint_lock_budget_throttling_observability_and_rollback |
| REQ-V51-183-011 | 183 | P0 | PASS | rollback/roll-forward plan | test_immutable_initial_migration_matches_runtime_table_set |
| REQ-V51-184-001 | 184 | P0 | NOT_TESTED | Bölüm 184 (PRODUCTION AVAILABILITY PROFILES / HA / STANDBY) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. |  |
| REQ-V51-184-002 | 184 | P0 | PASS | bir production host olabilir | test_single_host_profile_requires_external_backup_restart_reconciliation_and_downtime_disclosure |
| REQ-V51-184-003 | 184 | P0 | PASS | external backup zorunlu | test_single_host_profile_requires_external_backup_restart_reconciliation_and_downtime_disclosure |
| REQ-V51-184-004 | 184 | P0 | PASS | process restart/reconciliation zorunlu | test_single_host_profile_requires_external_backup_restart_reconciliation_and_downtime_disclosure |
| REQ-V51-184-005 | 184 | P0 | PASS | kullanıcıya host failure durumunda downtime olabileceği açıkça gösterilir | test_single_host_profile_requires_external_backup_restart_reconciliation_and_downtime_disclosure |
| REQ-V51-184-006 | 184 | P0 | PASS | database HA/managed HA veya tested replication | test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover |
| REQ-V51-184-007 | 184 | P0 | PASS | Redis dependency kritikse failover/persistence tasarımı | test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover |
| REQ-V51-184-008 | 184 | P0 | PASS | standby trading engine instance | test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover |
| REQ-V51-184-009 | 184 | P0 | PASS | single active leader + fencing token | test_fencing_guard_never_accepts_older_token_after_newer_seen, test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-184-010 | 184 | P0 | PASS | external watchdog | test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover |
| REQ-V51-184-011 | 184 | P0 | PASS | deterministic failover/reconciliation | test_ha_profile_requires_database_redis_standby_watchdog_and_deterministic_failover |
| REQ-V51-184-012 | 184 | P0 | PASS | active process kill | test_committed_account_state_survives_abrupt_worker_exit |
| REQ-V51-184-013 | 184 | P0 | NOT_TESTED | host loss simulation |  |
| REQ-V51-184-014 | 184 | P0 | NOT_TESTED | DB failover |  |
| REQ-V51-184-015 | 184 | P0 | NOT_TESTED | Redis failover uygun ise |  |
| REQ-V51-184-016 | 184 | P0 | NOT_TESTED | network partition |  |
| REQ-V51-184-017 | 184 | P0 | PASS | stale leader fencing | test_fencing_guard_never_accepts_older_token_after_newer_seen, test_persistent_fencing_token_increases_after_expiry |
| REQ-V51-184-018 | 184 | P0 | PASS | private-stream reconnect/reconciliation | test_private_stream_reconnect_performs_rest_reconciliation_before_recovery |
| REQ-V51-185-001 | 185 | P0 | PASS | Bölüm 185 (REST / WEBSOCKET API VERSIONING / DEPRECATION CONTRACT) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_api_deprecation_contract_has_warning_window_successor_and_breaking_criteria |
| REQ-V51-185-002 | 185 | P0 | PASS | schema_version | test_websocket_contract |
| REQ-V51-185-003 | 185 | P0 | PASS | message_type | test_websocket_contract |
| REQ-V51-185-004 | 185 | P0 | PASS | sequence/version | test_websocket_contract |
| REQ-V51-185-005 | 185 | P0 | PASS | Tanımla: | test_phase22_api_deprecation_contract_has_warning_window_successor_and_breaking_criteria |
| REQ-V51-185-006 | 185 | P0 | PASS | API version policy | test_api_version_policy_enforces_backward_compatibility_window_deprecation_warning_and_breaking_change_definition |
| REQ-V51-185-007 | 185 | P0 | PASS | backward compatibility window | test_api_version_policy_enforces_backward_compatibility_window_deprecation_warning_and_breaking_change_definition |
| REQ-V51-185-008 | 185 | P0 | PASS | deprecation warning | test_api_version_policy_enforces_backward_compatibility_window_deprecation_warning_and_breaking_change_definition |
| REQ-V51-185-009 | 185 | P0 | PASS | breaking-change criteria | test_api_version_policy_enforces_backward_compatibility_window_deprecation_warning_and_breaking_change_definition |
| REQ-V51-185-010 | 185 | P0 | PASS | supported client/server compatibility matrix | test_compatibility |
| REQ-V51-185-011 | 185 | P0 | PASS | Frontend açılışta server compatibility endpoint/metadata kontrol etmelidir. | test_compatibility |
| REQ-V51-186-001 | 186 | P0 | PASS | Bölüm 186 (INCIDENT RESPONSE / SEVERITY / RUNBOOK / POSTMORTEM) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_sev1_requires_recovery_validation |
| REQ-V51-186-002 | 186 | P0 | PASS | Severity sınıfları tanımla, örneğin: | test_sev1_requires_recovery_validation |
| REQ-V51-186-003 | 186 | P0 | PASS | SEV1 = sermaye/execution/security bütünlüğünü etkileyen kritik olay | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-004 | 186 | P0 | PASS | Kritik event için: | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-005 | 186 | P0 | PASS | incident_id | test_sev1_requires_recovery_validation |
| REQ-V51-186-006 | 186 | P0 | PASS | severity | test_sev1_requires_recovery_validation |
| REQ-V51-186-007 | 186 | P0 | PASS | detected_at | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-008 | 186 | P0 | PASS | affected account/symbol/service | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-009 | 186 | P0 | PASS | automatic action | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-010 | 186 | P0 | PASS | risk state | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-011 | 186 | P0 | PASS | operator actions | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-012 | 186 | P0 | PASS | evidence/correlation ids | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-013 | 186 | P0 | PASS | resolved_at | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-014 | 186 | P0 | PASS | recovery validation | test_sev1_requires_recovery_validation |
| REQ-V51-186-015 | 186 | P0 | PASS | sakla. | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-016 | 186 | P0 | PASS | UNKNOWN order | test_unknown_order_isolated_to_one_symbol_while_other_symbol_can_operate |
| REQ-V51-186-017 | 186 | P0 | PASS | orphan order | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-018 | 186 | P0 | PASS | unprotected position | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-019 | 186 | P0 | PASS | external/manual account activity | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-020 | 186 | P0 | PASS | stale private stream | test_private_stream_reconnect_performs_rest_reconciliation_before_recovery |
| REQ-V51-186-021 | 186 | P0 | PASS | venue divergence | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-022 | 186 | P0 | PASS | DB outage | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-023 | 186 | P0 | PASS | Redis outage | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-024 | 186 | P0 | PASS | disk full | test_disk_full_on_durability_critical_audit_write_halts_new_risk |
| REQ-V51-186-025 | 186 | P0 | PASS | security compromise/key rotation | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-026 | 186 | P0 | PASS | bad deployment | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-027 | 186 | P0 | PASS | data corruption | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-186-028 | 186 | P0 | PASS | backup restore | test_typed_sev1_incident_requires_complete_recovery_evidence |
| REQ-V51-187-001 | 187 | P0 | PASS | Bölüm 187 (OPENTELEMETRY / END-TO-END TRACE / LATENCY DECOMPOSITION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-002 | 187 | P0 | PASS | Structured log ve correlation ID'ye ek olarak OpenTelemetry veya eşdeğer distributed tracing destekle. | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-003 | 187 | P0 | PASS | market-data receive latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-004 | 187 | P0 | PASS | feature/signal compute latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-005 | 187 | P0 | PASS | risk decision latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-006 | 187 | P0 | PASS | submit network latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-007 | 187 | P0 | PASS | exchange ack latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-008 | 187 | P0 | PASS | fill latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-009 | 187 | P0 | PASS | private-stream propagation latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-010 | 187 | P0 | PASS | DB persistence latency | test_latency_tracer_decomposes_required_stages_and_is_bounded |
| REQ-V51-187-011 | 187 | P0 | PASS | Tracing yüksek cardinality/volume nedeniyle trading engine'i yavaşlatmamalı; sampling/bounded policy uygula. | test_latency_tracer_sampling_can_disable_high_cardinality_storage_and_clock_regression_fails |
| REQ-V51-188-001 | 188 | P0 | PASS | Bölüm 188 (DATA PROVIDER GOVERNANCE / LICENSE / RETENTION / PROVENANCE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_provider_registry_enforces_license_retention_provenance_contract |
| REQ-V51-188-002 | 188 | P0 | PASS | Her provider için registry oluştur: | test_phase22_provider_registry_enforces_license_retention_provenance_contract |
| REQ-V51-188-003 | 188 | P0 | PASS | provider_id | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-004 | 188 | P0 | PASS | data_type | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-005 | 188 | P0 | PASS | official/documented source | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-006 | 188 | P0 | PASS | license/TOS metadata | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-007 | 188 | P0 | PASS | redistribution allowed/not allowed | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-008 | 188 | P0 | PASS | attribution requirements | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-009 | 188 | P0 | PASS | retention restrictions | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-010 | 188 | P0 | PASS | rate limits | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-011 | 188 | P0 | PASS | commercial/non-commercial constraints | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-012 | 188 | P0 | PASS | timezone/timestamp semantics | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-013 | 188 | P0 | PASS | revision/vintage semantics | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-014 | 188 | P0 | PASS | data quality owner | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-188-015 | 188 | P0 | PASS | adapter version | test_provider_registry_requires_governance_metadata_and_has_stable_snapshot_hash |
| REQ-V51-189-001 | 189 | P0 | PASS | Bölüm 189 (BUILD PROVENANCE / ARTIFACT SIGNING / RELEASE ATTESTATION) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_phase22_release_attestation_requires_all_production_provenance_fields_and_is_tamper_fingerprinted |
| REQ-V51-189-002 | 189 | P0 | PASS | release_id/version | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-003 | 189 | P0 | PASS | git commit SHA | test_local_git_provenance_has_real_clean_commit_and_immutable_tag |
| REQ-V51-189-004 | 189 | P0 | PASS | source tree hash | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-005 | 189 | P0 | NOT_TESTED | CI run id |  |
| REQ-V51-189-006 | 189 | P0 | PASS | build timestamp | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-007 | 189 | P0 | NOT_TESTED | dependency lock hash |  |
| REQ-V51-189-008 | 189 | P0 | NOT_TESTED | SBOM hash |  |
| REQ-V51-189-009 | 189 | P0 | NOT_TESTED | container digest |  |
| REQ-V51-189-010 | 189 | P0 | NOT_TESTED | frontend artifact hash |  |
| REQ-V51-189-011 | 189 | P0 | PASS | migration version | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-012 | 189 | P0 | PASS | architecture profile hash | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-013 | 189 | P0 | PASS | requirement matrix hash | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-014 | 189 | P0 | PASS | test evidence reference | test_release_manifest_is_fail_closed_and_matches_local_acceptance_identity |
| REQ-V51-189-015 | 189 | P0 | PASS | sakla. | test_release_attestation_is_tamper_evident_and_requires_production_provenance |
| REQ-V51-189-016 | 189 | P0 | NOT_TESTED | Mümkünse container/image ve desktop package signing uygula. |  |
| REQ-V51-189-017 | 189 | P0 | NOT_TESTED | Signed artifact destekleniyorsa deployment sırasında signature verification yap. |  |
| REQ-V51-190-001 | 190 | P0 | PASS | Bölüm 190 (REQUIREMENT TRACEABILITY / ACCEPTANCE MATRIX / DEFINITION OF DONE) hükümlerini canonical profile ve v5.1 precedence kurallarıyla uygulama. | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-002 | 190 | P0 | PASS | Zorunlu machine-readable dosya: | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-003 | 190 | P0 | PASS | requirement_id | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-004 | 190 | P0 | PASS | section | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-005 | 190 | P0 | PASS | requirement_text_summary | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-006 | 190 | P0 | PASS | priority = P0/P1/P2 | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-007 | 190 | P0 | PASS | implementation_modules | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-008 | 190 | P0 | PASS | test_ids | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-009 | 190 | P0 | PASS | evidence_refs | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-010 | 190 | P0 | PASS | status | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-011 | 190 | P0 | PASS | supported_modes | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-012 | 190 | P0 | PASS | supported_market_types | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-013 | 190 | P0 | PASS | mock_or_real | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-014 | 190 | P0 | PASS | known_limitations | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-015 | 190 | P0 | PASS | owner/component | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-016 | 190 | P0 | PASS | last_verified_release | test_machine_readable_traceability_is_evidence_bound_and_consistent |
| REQ-V51-190-017 | 190 | P0 | PASS | sakla. | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-018 | 190 | P0 | PASS | kod implementasyonu mevcut | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-019 | 190 | P0 | PASS | static/type/lint kontrolleri geçiyor | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-020 | 190 | P0 | PASS | ilgili unit/integration/safety testi var ve gerçekten çalıştırılmış | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-021 | 190 | P0 | PASS | gerekiyorsa E2E/contract/load/chaos testi geçiyor | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-022 | 190 | P0 | PASS | evidence referansı mevcut | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-023 | 190 | P0 | PASS | dokümantasyon/runbook gerekiyorsa mevcut | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-024 | 190 | P0 | PASS | mock ise PASS olarak gizlenmiyor | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-025 | 190 | P0 | PASS | known critical issue yok | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-026 | 190 | P0 | PASS | Teslimatta ayrıca zorunlu olarak üret: | test_definition_of_done_is_fail_closed_for_missing_evidence_mock_disclosure_or_known_critical_issue |
| REQ-V51-190-027 | 190 | P0 | PASS | ARCHITECTURE_DECISIONS.md | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-028 | 190 | P0 | PASS | architecture_profile.yaml | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-029 | 190 | P0 | PASS | REQUIREMENTS_TRACEABILITY.md | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-030 | 190 | P0 | PASS | requirements_acceptance_matrix.yaml | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-031 | 190 | P0 | PASS | INCIDENT_RUNBOOKS.md | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-032 | 190 | P0 | PASS | BACKUP_RESTORE_DRILL.md | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-033 | 190 | P0 | PASS | RELEASE_MANIFEST.json | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-034 | 190 | P0 | PASS | DATA_PROVIDER_REGISTRY.yaml varsa external provider kullanılıyorsa | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
| REQ-V51-190-035 | 190 | P0 | PASS | EVENT_SCHEMA_REGISTRY.md veya machine-readable eşdeğeri | test_v51_mandatory_traceability_and_runbook_artifacts_exist |
