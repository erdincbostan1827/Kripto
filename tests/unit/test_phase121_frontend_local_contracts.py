from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def text(p): return (ROOT/p).read_text(encoding='utf-8')

def test_phase121_progressive_disclosure_safe_cancel_and_no_dark_pattern_contract():
    settings=text('frontend/src/pages/Settings.tsx'); high=text('frontend/src/components/HighRiskConfirmation.tsx')
    assert '<details>' in settings and 'Gelişmiş ayrıntılar' in settings and 'Risk artırıcı ayarlar varsayılan olarak seçili değildir' in settings
    assert 'onCancel' in high and 'İptal' in high and 'ikinci onay' in high

def test_phase121_settings_information_architecture_exposes_required_domains():
    s=text('frontend/src/pages/Settings.tsx')
    for label in ('Exchange','Telegram/Bildirim','Risk','Coin Universe','Strategy','Kullanıcı & Güvenlik','Sistem Sağlığı','Yedekleme'): assert label in s

def test_phase121_mobile_scanner_uses_card_mode_and_desktop_table_to_reduce_horizontal_scroll():
    s=text('frontend/src/pages/Scanner.tsx')
    assert "breakpoints.down('sm')" in s and 'CandidateCard' in s and 'Scanner kart görünümü' in s and 'Scanner tablo görünümü' in s
    for token in ('Sembol','Sinyal','Skor','Confidence','Rejim','Net Edge','Risk/Block Nedeni'): assert token in s

def test_phase121_pwa_manifest_has_installable_application_icons():
    m=text('frontend/public/manifest.webmanifest')
    assert '"icons"' in m and '/icons/icon-192.svg' in m and '/icons/icon-512.svg' in m
    assert (ROOT/'frontend/public/icons/icon-192.svg').is_file() and (ROOT/'frontend/public/icons/icon-512.svg').is_file()
