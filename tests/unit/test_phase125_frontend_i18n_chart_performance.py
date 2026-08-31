from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def text(p): return (ROOT/p).read_text(encoding='utf-8')

def test_phase125_turkish_first_i18n_centralizes_shell_strings():
    i=text('frontend/src/i18n/tr.ts'); app=text('frontend/src/App.tsx')
    for token in ('nav.dashboard','nav.scanner','nav.analysis','app.title','TranslationKey','function t('): assert token in i
    assert "from './i18n/tr'" in app and "t('nav.dashboard')" in app and "t('app.title')" in app

def test_phase125_market_chart_has_gesture_zoom_bounded_windowing_indicators_and_trade_levels_with_cleanup():
    s=text('frontend/src/components/MarketChart.tsx')
    for token in ('createChart','addSeries(CandlestickSeries','addSeries(HistogramSeries','addSeries(LineSeries','handleScroll:true','handleScale:true','MAX_VISIBLE_POINTS','slice(-MAX_VISIBLE_POINTS)','ENTRY','STOP','TP${i+1}','ResizeObserver','resize.disconnect()','chart.remove()'): assert token in s

def test_phase125_virtualized_rows_bounds_large_client_render_work():
    s=text('frontend/src/components/VirtualizedRows.tsx')
    for token in ('ROW_HEIGHT','OVERSCAN','scrollTop','items.slice(range.start,range.end)','data-virtualized="true"','overflowY'): assert token in s

def test_phase125_login_error_is_programmatically_associated_with_field():
    s=text('frontend/src/components/AuthGate.tsx')
    assert 'id="login-error"' in s and 'aria-describedby="login-error"' in s and 'helperText=' in s and 'error={Boolean(state.error)}' in s

def test_phase125_local_ui_state_is_component_scoped_and_third_party_attribution_is_explicit():
    app=text('frontend/src/App.tsx'); notices=text('THIRD_PARTY_NOTICES.md'); pkg=text('frontend/package.json')
    assert 'useState' in app and 'createStore' not in app and 'configureStore' not in app
    assert 'lightweight-charts' in pkg and 'TradingView Lightweight Charts' in notices and 'license' in notices.lower() and 'attribution' in notices.lower()
