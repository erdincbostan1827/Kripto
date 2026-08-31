from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def text(p): return (ROOT/p).read_text(encoding='utf-8')

def test_phase124_frontend_is_react_typescript_responsive_accessible_theme_capable_and_route_error_bounded():
    pkg=text('frontend/package.json'); ts=text('frontend/tsconfig.json'); app=text('frontend/src/App.tsx'); main=text('frontend/src/main.tsx')
    assert 'react' in pkg and 'typescript' in pkg and 'strict' in ts.lower()
    assert 'useMediaQuery' in app and 'ErrorBoundary' in app and 'aria-label' in app
    theme=text('frontend/src/ux/theme.ts'); assert 'colorSchemes' in theme and 'dark:' in theme
    assert 'Suspense' in app and 'CircularProgress' in app and 'AuthGate' in main

def test_phase124_frontend_server_state_is_rest_snapshot_plus_authenticated_websocket_sequence_resync_and_cleanup():
    s=text('frontend/src/realtime/serverState.ts')
    for token in ("apiUrl('/api/v1/dashboard')","credentials:'include'",'new WebSocket',"websocketUrl('/api/v1/ws')",'applySnapshot','applyIncremental','stale:true','needsResync:true','stop()','close()'): assert token in s

def test_phase124_frontend_navigation_status_universe_decision_and_no_trade_all_contracts_are_visible():
    app=text('frontend/src/App.tsx'); i18n=text('frontend/src/i18n/tr.ts'); status=text('frontend/src/components/StatusStrip.tsx'); badge=text('frontend/src/components/ModeBadge.tsx'); scanner=text('frontend/src/pages/Scanner.tsx'); analysis=text('frontend/src/pages/Analysis.tsx')
    for label in ('Ana Ekran','Piyasa / Scanner','Analiz','Pozisyonlar & Emirler','Alarmlar','Backtest & Araştırma','Performans & Risk','Ayarlar / Sistem'): assert label in app+i18n
    assert 'PAPER' in status and 'LIVE varsayılan olarak kapalıdır' in status and 'GERÇEK PARA' in badge and 'TESTNET' in badge
    for token in ('Aktif Universe','Hariç bırakılma gerekçeleri','Likidite / Spread / Volume','Korelasyon matrisi','cluster-tema konsantrasyonu','quote-asset exposure','Per-symbol data health','new-listing risk badge','suspension/delisting','Net Edge','Risk/Block Nedeni'): assert token in scanner
    for token in ('Reasons','Risks','Entry','Stop','TP1/TP2/TP3','risk amount + risk percent','Confidence','data timestamp','mode'): assert token in analysis
    assert 'TRADE ALL' not in app+scanner+analysis
