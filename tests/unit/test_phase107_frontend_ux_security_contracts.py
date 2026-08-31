from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def text(rel:str)->str: return (ROOT/rel).read_text(encoding='utf-8')


def test_phase107_product_ux_principles_have_safe_defaults_mode_status_explainability_confirmation_staleness_and_consistent_trade_terms():
    app=text('frontend/src/App.tsx'); status=text('frontend/src/components/StatusStrip.tsx'); dash=text('frontend/src/pages/Dashboard.tsx'); high=text('frontend/src/components/HighRiskConfirmation.tsx'); human=text('frontend/src/ux/status.ts')
    assert 'PAPER' in status and 'LIVE varsayılan olarak kapalıdır' in status
    assert 'role="status"' in status and 'Market Data: Fresh' in status and 'Risk: Normal' in status
    assert 'Risk/Block Nedeni' in dash and 'Net Edge' in dash and 'NO_TRADE' in dash
    assert 'ikinci onay' in high and 'İptal' in high and 'Audit reason' in high
    assert 'DATA_STALE_OR_INCOMPLETE' not in app  # UX terms are human-readable, not raw internal decision codes.
    assert 'whatHappened' in human and 'impact' in human and 'automaticAction' in human and 'userAction' in human


def test_phase107_always_on_server_client_boundary_keeps_execution_backend_owned_and_browser_pwa_read_only():
    api=text('frontend/src/api/client.ts'); sw=text('frontend/public/sw.js'); runtime=text('backend/app/services/runtime.py'); execution=text('backend/app/execution/service.py')
    assert "credentials:'include'" in api and 'API secret' not in api and 'api_key' not in api.lower()
    assert 'never submits orders' in sw and 'trading engine' in sw
    assert 'class Runtime' in runtime or 'runtime' in runtime.lower()
    assert 'OrderIntent' in execution or 'Execution' in execution


def test_phase107_frontend_stack_and_realtime_delivery_use_react_query_typed_routing_snapshot_sequence_resync_and_stale_state():
    pkg=text('frontend/package.json'); main=text('frontend/src/main.tsx'); app=text('frontend/src/App.tsx'); rt=text('frontend/src/realtime/versionedState.ts')
    for dep in ('react','typescript','vite','@mui/material','@tanstack/react-query','react-router-dom'): assert dep in pkg
    assert 'QueryClient' in main and 'BrowserRouter' in main and 'Routes' in app
    assert 'applySnapshot' in rt and 'applyIncremental' in rt and 'SEQUENCE_GAP' in rt and 'VERSION_MISMATCH' in rt and 'needsResync' in rt and 'stale' in rt


def test_phase107_information_architecture_has_core_navigation_and_safe_deep_links():
    app=text('frontend/src/App.tsx'); i18n=text('frontend/src/i18n/tr.ts')
    for label in ('Ana Ekran','Piyasa / Scanner','Analiz','Pozisyonlar & Emirler','Alarmlar','Backtest & Araştırma','Performans & Risk','Ayarlar / Sistem'): assert label in app+i18n
    for route in ('/scanner','/analysis','/orders','/alerts','/research','/performance','/settings'): assert f'path="{route}"' in app
    assert 'BrowserRouter' in text('frontend/src/main.tsx') and 'AuthGate' in text('frontend/src/main.tsx')


def test_phase107_home_dashboard_exposes_mode_connectivity_freshness_engine_risk_time_portfolio_drawdown_positions_candidates_and_block_reason():
    status=text('frontend/src/components/StatusStrip.tsx'); dash=text('frontend/src/pages/Dashboard.tsx')
    for token in ('PAPER','Exchange:','Market Data:','Engine:','Risk:','Server/Local:'): assert token in status
    for token in ('Portföy','Günlük P&L','Açık Risk','Drawdown','Açık Pozisyon','Kritik Uyarı','Sembol','Sinyal','Skor','Confidence','Rejim','Net Edge','Risk/Block Nedeni'): assert token in dash


def test_phase107_responsive_web_pwa_has_mobile_navigation_install_manifest_read_only_offline_shell_and_stale_safety():
    app=text('frontend/src/App.tsx'); manifest=text('frontend/public/manifest.webmanifest'); sw=text('frontend/public/sw.js'); main=text('frontend/src/main.tsx'); rt=text('frontend/src/realtime/versionedState.ts')
    assert "useMediaQuery" in app and "display:{md:'none'}" in app and "ml:{xs:0,md:'250px'}" in app
    assert 'standalone' in manifest and 'start_url' in manifest and 'scope' in manifest
    assert "request.method!=='GET'" in sw and "startsWith('/api/')" in sw and 'never submits orders' in sw
    assert "serviceWorker.register('/sw.js')" in main and 'stale:true' in rt and 'needsResync:true' in rt


def test_phase107_human_readable_status_has_technical_code_explanation_impact_automatic_recovery_user_action_and_correlation_id():
    s=text('frontend/src/ux/status.ts')
    for token in ('SystemStatusCode','whatHappened','impact','automaticAction','userAction','correlationId','DEGRADED','STALE','HALTED','REDUCE_ONLY','BLOCKED','RECONCILING'): assert token in s


def test_phase107_high_risk_action_confirmation_covers_all_sensitive_actions_and_required_trade_risk_protection_audit_fields():
    s=text('frontend/src/components/HighRiskConfirmation.tsx')
    for token in ('ENABLE_AUTO_EXECUTION','INCREASE_RISK_LIMIT','INCREASE_MAX_POSITION','ENABLE_CROSS_MARGIN','CHANGE_API_CREDENTIAL','PANIC_CLOSE','MANUAL_LIVE_ORDER','OVERRIDE_EMERGENCY_STOP'): assert token in s
    for token in ('mode','account','symbol','side','quantity','estimatedNotional','estimatedFees','estimatedSlippage','riskAmount','riskPercent','protectionState','Audit reason','ikinci onay'): assert token in s


def test_phase107_accessibility_localization_and_visual_consistency_have_turkish_semantics_keyboard_native_controls_focus_and_non_color_status_text():
    index=text('frontend/index.html'); app=text('frontend/src/App.tsx'); status=text('frontend/src/components/StatusStrip.tsx'); high=text('frontend/src/components/HighRiskConfirmation.tsx')
    assert 'lang="tr"' in index and 'aria-label="Menüyü aç"' in app and 'aria-label="Ana navigasyon"' in app
    assert 'aria-live="polite"' in status and 'Market Data: Fresh' in status and 'Engine: Safe' in status
    assert '<Button' in high and '<TextField' in high and 'aria-labelledby' in high


def test_phase107_frontend_security_uses_http_only_cookie_session_csrf_no_url_token_and_csp_compatible_fetch_boundary():
    api=text('frontend/src/api/client.ts'); main=text('frontend/src/main.tsx'); security=text('backend/app/core/http_security.py')
    assert "credentials:'include'" in api and "X-CSRF-Token" in api and 'localStorage' not in api and 'sessionStorage' not in api
    assert '?token=' not in api.lower() and '&token=' not in api.lower() and 'bootstrap_token' in api  # bootstrap token is JSON body, never URL state.
    assert 'CSP' in security or 'Content-Security-Policy' in security
    assert 'Compatibility' in api and 'Uyumsuz istemci/sunucu' in main
