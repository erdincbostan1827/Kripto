from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]

def _lum(hex_color:str)->float:
    rgb=[int(hex_color[i:i+2],16)/255 for i in (1,3,5)]
    def linear(c:float)->float:return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    r,g,b=(linear(c) for c in rgb)
    return 0.2126*r+0.7152*g+0.0722*b

def _ratio(a:str,b:str)->float:
    x,y=sorted((_lum(a),_lum(b)),reverse=True)
    return (x+0.05)/(y+0.05)

def _tokens():
    s=(ROOT/'frontend/src/ux/theme.ts').read_text()
    return dict(re.findall(r"(background|text|primary|onPrimary|warning):'(#[0-9A-F]{6})'",s))

def test_phase131_explicit_theme_tokens_meet_wcag_aa_core_contrast_budget():
    s=(ROOT/'frontend/src/ux/theme.ts').read_text()
    groups=re.findall(r"(light|dark):\{background:'(#[0-9A-F]{6})',text:'(#[0-9A-F]{6})',primary:'(#[0-9A-F]{6})',onPrimary:'(#[0-9A-F]{6})',warning:'(#[0-9A-F]{6})'\}",s)
    assert len(groups)==2
    for _,background,text,primary,on_primary,warning in groups:
        assert _ratio(text,background)>=4.5
        assert _ratio(on_primary,primary)>=4.5
        assert _ratio(warning,background)>=4.5

def test_phase131_theme_is_used_by_application_and_accessibility_contract_is_not_color_only():
    main=(ROOT/'frontend/src/main.tsx').read_text()
    theme=(ROOT/'frontend/src/ux/theme.ts').read_text()
    mode=(ROOT/'frontend/src/components/ModeBadge.tsx').read_text()
    status=(ROOT/'frontend/src/components/StatusStrip.tsx').read_text()
    assert "import {appTheme} from './ux/theme'" in main
    assert '<ThemeProvider theme={appTheme}>' in main
    assert 'Explicit high-contrast core tokens' in theme
    # Existing UI expresses status with text/labels; color is supplemental.
    assert 'GERÇEK PARA' in mode and 'label=' in mode and ('label' in status or 'Typography' in status)

def test_phase131_section165_accessibility_localization_contract_is_complete_at_source_level():
    theme=(ROOT/'frontend/src/ux/theme.ts').read_text()
    app=(ROOT/'frontend/src/App.tsx').read_text().lower()
    auth=(ROOT/'frontend/src/components/AuthGate.tsx').read_text().lower()
    tr=(ROOT/'frontend/src/i18n/tr.ts').read_text()
    # Contrast is numeric-tested above; the remaining contract is semantic/keyboard/textual.
    assert 'accessible' in theme.lower() or 'contrast' in theme.lower()
    assert ('aria-' in app or 'navlink' in app) and 'aria-describedby' in auth
    assert 'türkçe' in tr.lower() or 'ana ekran' in tr.lower()
