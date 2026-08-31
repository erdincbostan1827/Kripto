#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 backup.dump.enc [target_database]" >&2
  exit 2
fi

BACKUP="$1"
TARGET="${2:-trading_restore}"
CHECKSUM="$BACKUP.sha256"

if [[ ! -f "$BACKUP" ]]; then
  echo "RESTORE_REFUSED backup_not_found=$BACKUP" >&2
  exit 2
fi
if [[ ! -f "$CHECKSUM" ]]; then
  echo "RESTORE_REFUSED checksum_not_found=$CHECKSUM" >&2
  exit 2
fi
if [[ ! "$TARGET" =~ ^[A-Za-z_][A-Za-z0-9_]{0,62}$ ]]; then
  echo "RESTORE_REFUSED invalid_target_database" >&2
  exit 2
fi
if [[ "$TARGET" == "trading" || "$TARGET" == "postgres" || "$TARGET" == "template0" || "$TARGET" == "template1" ]]; then
  echo "RESTORE_REFUSED protected_target_database=$TARGET" >&2
  exit 2
fi

sha256sum -c "$CHECKSUM"

# Restore never writes into an existing database.  It first restores into a
# disposable staging database; only a fully successful pg_restore is promoted
# by an atomic PostgreSQL database rename.
if docker compose exec -T postgres psql -U trading -d postgres -tAc \
  "SELECT 1 FROM pg_database WHERE datname='$TARGET'" | grep -qx '1'; then
  echo "RESTORE_REFUSED target_database_exists=$TARGET" >&2
  exit 3
fi

STAGING="restore_stage_${RANDOM}_$$"
created=0
cleanup() {
  if [[ "$created" == "1" ]]; then
    docker compose exec -T postgres dropdb -U trading --if-exists "$STAGING" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

docker compose exec -T postgres createdb -U trading "$STAGING"
created=1

docker compose run --rm -T app python /app/scripts/backup_crypto.py decrypt --key-file /run/secrets/backup_encryption_key < "$BACKUP" \
  | docker compose exec -T postgres pg_restore --exit-on-error --no-owner --no-acl -U trading --dbname="$STAGING"

docker compose exec -T postgres psql -U trading -d postgres -v ON_ERROR_STOP=1 -c \
  "ALTER DATABASE \"$STAGING\" RENAME TO \"$TARGET\";" >/dev/null
created=0
trap - EXIT INT TERM

echo "RESTORE_PASS database=$TARGET promotion=atomic source=encrypted_backup"
