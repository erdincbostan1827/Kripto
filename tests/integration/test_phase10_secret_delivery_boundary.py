from pathlib import Path

from app.core.logging import redact

ROOT=Path(__file__).resolve().parents[2]


def test_secret_material_is_excluded_from_git_docker_frontend_and_logs():
    gitignore=(ROOT/'.gitignore').read_text(encoding='utf-8')
    dockerignore=(ROOT/'.dockerignore').read_text(encoding='utf-8')
    assert '.env' in gitignore and 'secrets/*' in gitignore
    assert '.env' in dockerignore and 'secrets/' in dockerignore

    backend=(ROOT/'backend/Dockerfile').read_text(encoding='utf-8')
    frontend_docker=(ROOT/'frontend/Dockerfile').read_text(encoding='utf-8')
    assert 'COPY . ' not in backend
    assert 'COPY . ' not in frontend_docker

    frontend_text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in (ROOT/'frontend/src').rglob('*') if p.is_file())
    forbidden=('VITE_BINANCE_API_KEY','VITE_BINANCE_API_SECRET','VITE_TELEGRAM_BOT_TOKEN','localStorage.setItem("token"','localStorage.setItem(\'token\'')
    assert not any(x in frontend_text for x in forbidden)

    payload=redact({'api_key':'abc','api_secret':'def','authorization':'Bearer secret','nested':{'password':'pw'}})
    assert payload=={'api_key':'[REDACTED]','api_secret':'[REDACTED]','authorization':'[REDACTED]','nested':{'password':'[REDACTED]'}}
