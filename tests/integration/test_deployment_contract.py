from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]

def test_base_compose_is_pinned_and_postgres18_volume_is_correct():
    data=yaml.safe_load((ROOT/'docker-compose.yml').read_text())
    assert data['services']['postgres']['image'].startswith('postgres:18.6-bookworm@sha256:')
    assert 'postgres_data:/var/lib/postgresql' in data['services']['postgres']['volumes']
    assert data['services']['redis']['image'].startswith('redis:8.10.0-alpine@sha256:')
    assert data['services']['prometheus']['image'].startswith('prom/prometheus:v3.14.0-distroless@sha256:')
    assert data['services']['nginx']['image'].startswith('nginxinc/nginx-unprivileged:1.30.4-alpine@sha256:')
    assert data['services']['test']['build']['target']=='test'
    assert data['services']['app']['build']['target']=='runtime'

def test_prod_override_requires_tls_prod_isolation_and_wal_archiving():
    text=(ROOT/'docker-compose.prod.yml').read_text()
    data=yaml.safe_load(text)
    assert data['services']['app']['environment']['ENVIRONMENT']=='PROD'
    assert data['services']['app']['environment']['MODE']=='PAPER'
    assert 'PUBLIC_HOSTNAME' in text
    assert 'archive_mode=on' in data['services']['postgres']['command']
    assert 'postgres_wal_archive:/wal_archive' in data['services']['postgres']['volumes']
    nginx=(ROOT/'docker/nginx/nginx.prod.conf').read_text()
    assert 'listen 8443 ssl;' in nginx
    assert 'ssl_protocols TLSv1.2 TLSv1.3;' in nginx
    assert 'Strict-Transport-Security' in nginx
    assert 'return 308 https://$host$request_uri;' in nginx
