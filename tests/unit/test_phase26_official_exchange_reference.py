from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase26_official_binance_reference_is_date_stamped_and_runtime_capability_remains_source_of_truth():
    text = (ROOT / 'reports' / 'PHASE26_BINANCE_OFFICIAL_API_VERIFICATION.md').read_text()
    assert '2026-08-29' in text
    assert 'https://developers.binance.com/' in text
    assert 'exchangeInfo' in text
    assert 'Runtime source-of-truth policy' in text
    assert 'fail safe' in text
    assert 'not' in text.lower() and 'credentialed TESTNET acceptance' in text
