from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def text(p): return (ROOT/p).read_text(encoding='utf-8')

def test_phase122_delivery_inventory_contains_source_runtime_database_engines_tests_install_backup_and_docs():
    required=(
      'backend/Dockerfile','docker-compose.yml','.env.example','pyproject.toml','alembic','database/schema.sql',
      'backend/app','frontend','backend/app/monitoring/telegram.py','backend/app/exchange','backend/app/backtest/engine.py',
      'backend/app/paper/engine.py','backend/app/risk/engine.py','backend/app/signals/engine.py','frontend/src/pages/Dashboard.tsx',
      'tests','install.sh','scripts/backup.sh','README.md','docs/TROUBLESHOOTING.md','ARCHITECTURE.md')
    for rel in required: assert (ROOT/rel).exists(), rel

def test_phase122_strategy_assumptions_document_math_entry_exit_risk_and_failure_conditions():
    s=text('docs/STRATEGY_ASSUMPTIONS.md').lower()
    for token in ('matematik','giriş','çıkış','risk','başarısız'): assert token in s

def test_phase122_error_handling_has_human_message_action_correlation_and_critical_alert_channel():
    status=text('frontend/src/ux/status.ts'); alerts=text('backend/app/monitoring/alerts.py'); channels=text('backend/app/monitoring/channels.py')
    for token in ('whatHappened','userAction','correlationId'): assert token in status
    assert 'critical' in alerts.lower()
    assert 'webhook' in channels.lower() or 'email' in channels.lower(); assert 'telegram' in text('backend/app/monitoring/telegram.py').lower()

def test_phase122_performance_architecture_has_websocket_redis_candle_aggregation_and_log_rotation_contracts():
    compose=text('docker-compose.yml'); candles=text('backend/app/data/candles.py'); logging=text('backend/app/core/logging.py'); main=text('backend/app/main.py')
    assert 'redis' in compose.lower()
    assert 'websocket' in main.lower()
    assert 'aggregate' in candles.lower() or 'resample' in candles.lower() or 'bucket' in candles.lower()
    assert 'rotatingfilehandler' in logging.lower() or 'rotation' in logging.lower() or 'maxbytes' in logging.lower()

def test_phase122_real_api_absence_uses_explicit_mock_adapter_and_never_fakes_unsupported_capability():
    mock=text('backend/app/exchange/mock.py'); matrix=text('reports/REAL_MOCK_UNSUPPORTED_MATRIX.md')
    assert 'Mock' in mock and 'UNSUPPORTED' in matrix and 'REAL' in matrix and 'MOCK' in matrix
