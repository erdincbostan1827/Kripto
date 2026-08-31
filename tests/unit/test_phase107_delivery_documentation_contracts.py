from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def t(p): return (ROOT/p).read_text(encoding='utf-8')

def test_phase107_delivery_packaging_has_compose_migrations_backup_health_tls_compatibility_version_rollback_and_user_runbooks():
    for p in ('docker-compose.yml','docker-compose.prod.yml','alembic.ini','BACKUP_RESTORE_DRILL.md','DEPLOYMENT_ARCHITECTURE.md','README.md','docs/QUICK_START.md','docs/PAPER_GUIDE.md','docs/LIVE_SAFETY_GUIDE.md','docs/TROUBLESHOOTING.md','docs/DISASTER_RECOVERY.md','docs/EMERGENCY_PROCEDURE.md','docs/UPDATE_ROLLBACK.md','docs/API_VERSIONING.md'):
        assert (ROOT/p).is_file(),p
    compose=(t('docker-compose.yml')+'\n'+t('docker-compose.prod.yml')).lower(); assert 'healthcheck' in compose and ('postgres' in compose or 'db' in compose) and 'redis' in compose
    assert 'tls' in t('DEPLOYMENT_ARCHITECTURE.md').lower() or 'https' in t('DEPLOYMENT_ARCHITECTURE.md').lower()
    assert 'compatib' in t('docs/API_VERSIONING.md').lower()
    main=t('frontend/src/main.tsx'); api=t('frontend/src/api/client.ts'); assert 'CLIENT_VERSION' in main and 'getCompatibility' in main and 'server_version' in api
    update=t('docs/UPDATE_ROLLBACK.md').lower(); assert 'backup' in update and 'migration' in update and 'rollback' in update and 'config migration' in update and 'compatibility' in update
    for doc in ('docs/QUICK_START.md','docs/PAPER_GUIDE.md','docs/LIVE_SAFETY_GUIDE.md','docs/TROUBLESHOOTING.md','BACKUP_RESTORE_DRILL.md','docs/EMERGENCY_PROCEDURE.md'):
        assert len(t(doc).strip())>80
