#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo "Docker gerekli" >&2; exit 2; }
OUT_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$OUT_DIR/trading_${STAMP}.dump.enc"
TMP="$OUT.tmp"
trap 'rm -f "$TMP"' EXIT
# pg_dump plaintext'i pipe üzerinden doğrudan authenticated encryption katmanına gider; kalıcı plaintext dump yazılmaz.
docker compose exec -T postgres pg_dump -U trading --format=custom --no-owner --no-acl trading \
  | docker compose exec -T app python /app/scripts/backup_crypto.py encrypt --key-file /run/secrets/backup_encryption_key > "$TMP"
mv "$TMP" "$OUT"
sha256sum "$OUT" > "$OUT.sha256"
chmod 600 "$OUT" "$OUT.sha256"
echo "$OUT"
