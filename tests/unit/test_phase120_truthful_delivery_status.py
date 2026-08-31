from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase120_final_delivery_status_reports_every_required_delivery_surface_without_fabricating_external_acceptance():
    s=(ROOT/'docs/FINAL_DELIVERY_STATUS.md').read_text(encoding='utf-8')
    for token in (
        'PACKAGE_MANIFEST.json','README.md','docs/QUICKSTART.md','reports/LATEST_PYTEST.txt',
        'REAL_MOCK_UNSUPPORTED_MATRIX.md','Default startup mode is PAPER','LIVE release remains fail-closed',
        'In-sample backtest result','Out-of-sample result','Walk-forward result','Purged/embargo validation',
        'DSR / multiple-testing evidence','Paper trading campaign','TESTNET execution','LIVE-shadow campaign',
        'Execution/PnL attribution','Effective sample size / confidence intervals','UI / browser status',
        'First-run wizard','Tauri is optional','Frontend/backend compatibility','docs/UPDATE_ROLLBACK.md',
        'Why LIVE is off by default','EXTERNAL_ACCEPTANCE_REQUIRED','NOT_CLAIMED_WITHOUT_CANONICAL_DATASET_EVIDENCE',
    ):
        assert token in s
    assert 'PRODUCTION_READY' not in s and 'guaranteed profit' not in s.lower()
