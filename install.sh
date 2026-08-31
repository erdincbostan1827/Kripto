#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${CTP_INSTALL_LOCK_HELD:-0}" != "1" ]]; then
  exec python scripts/operation_lock_exec.py --lock-dir .. --operation install --env-json '{"CTP_INSTALL_LOCK_HELD":"1"}' -- bash "$0" "$@"
fi
command -v docker >/dev/null || { echo "Docker gerekli"; exit 2; }
docker compose version >/dev/null
command -v python >/dev/null || { echo "Python 3 gerekli"; exit 2; }
python scripts/bootstrap_dependency_locks.py --recover-only
if [ ! -f uv.lock ] || [ ! -f frontend/package-lock.json ]; then
  echo "Dependency lock dosyaları atomik olarak üretiliyor..."
  python scripts/bootstrap_dependency_locks.py
fi
python scripts/bootstrap_env.py
python scripts/bootstrap_secrets.py
docker compose --profile test build test app frontend nginx
docker compose up -d postgres redis
for _ in $(seq 1 30); do docker compose exec -T postgres pg_isready -U trading -d trading >/dev/null 2>&1 && break; sleep 1; done
docker compose run --rm app alembic -c /app/alembic.ini upgrade head
docker compose --profile test run --rm test
docker compose up -d
curl -fsS http://localhost:8080/api/v1/health >/dev/null
python scripts/deployment_audit_chain.py append --root .. --event-type INSTALL_ACCEPTED --subjects-json '{"mode":"PAPER","health":"PASS"}' >/dev/null
printf '\nKurulum tamamlandı. İlk mod PAPER.\n'
printf 'İlk admin bootstrap tokenı secrets/admin_bootstrap_token.txt dosyasındadır; değeri loglara veya sohbete kopyalamayın.\n'
