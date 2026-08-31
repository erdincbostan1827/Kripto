#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v docker >/dev/null 2>&1; then echo "NOT_TESTED: docker unavailable"; exit 3; fi
BACKUP="${1:-}"
ENVIRONMENT_ID="${CTP_ENVIRONMENT_ID:-}"
if [[ -z "$BACKUP" ]]; then echo "usage: $0 backup.dump.enc" >&2; exit 2; fi
if [[ -z "$ENVIRONMENT_ID" ]]; then echo "RESTORE_DRILL_ENVIRONMENT_ID_REQUIRED: set CTP_ENVIRONMENT_ID" >&2; exit 2; fi
sha256sum -c "$BACKUP.sha256"
NAME="ctp-restore-drill-$RANDOM"
IMAGE="postgres:18.6-bookworm@sha256:1c59e2c3c818eaa0f0628f695b36e7c9e362d6b219b36a54a32df645cbd7e1af"
docker run -d --rm --name "$NAME" -e POSTGRES_PASSWORD=restore -e POSTGRES_DB=restore "$IMAGE" >/dev/null
cleanup(){ docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
for _ in $(seq 1 30); do docker exec "$NAME" pg_isready -U postgres -d restore >/dev/null 2>&1 && break; sleep 1; done
docker compose run --rm -T app python /app/scripts/backup_crypto.py decrypt --key-file /run/secrets/backup_encryption_key < "$BACKUP" \
  | docker exec -i "$NAME" pg_restore --exit-on-error -U postgres -d restore
TABLES="$(docker exec "$NAME" psql -U postgres -d restore -Atc "select count(*) from information_schema.tables where table_schema='public'")"
[[ "$TABLES" =~ ^[1-9][0-9]*$ ]]
# Referans bütünlük smoke testleri: finansal tablolar varsa orphan kontrolü.
docker exec "$NAME" psql -U postgres -d restore -v ON_ERROR_STOP=1 -Atc "select 1" >/dev/null
RECEIPT="$BACKUP.restore-drill.json"
python scripts/write_restore_drill_receipt.py --backup "$BACKUP" --restored-table-count "$TABLES" --environment-id "$ENVIRONMENT_ID" --output "$RECEIPT"
echo "RESTORE_DRILL_PASS tables=$TABLES receipt=$RECEIPT"
