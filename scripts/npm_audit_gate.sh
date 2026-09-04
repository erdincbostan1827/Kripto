#!/usr/bin/env bash
set -euo pipefail

MAX_ATTEMPTS="${NPM_AUDIT_MAX_ATTEMPTS:-3}"
ATTEMPT_TIMEOUT_SECONDS="${NPM_AUDIT_ATTEMPT_TIMEOUT_SECONDS:-120}"
OUTPUT="${NPM_AUDIT_OUTPUT:-reports/NPM_AUDIT.txt}"

case "$MAX_ATTEMPTS" in
  ''|*[!0-9]*) echo "NPM_AUDIT_MAX_ATTEMPTS must be a positive integer" >&2; exit 2 ;;
esac
case "$ATTEMPT_TIMEOUT_SECONDS" in
  ''|*[!0-9]*) echo "NPM_AUDIT_ATTEMPT_TIMEOUT_SECONDS must be a positive integer" >&2; exit 2 ;;
esac
if [ "$MAX_ATTEMPTS" -lt 1 ] || [ "$ATTEMPT_TIMEOUT_SECONDS" -lt 1 ]; then
  echo "npm audit retry settings must be positive" >&2
  exit 2
fi

mkdir -p "$(dirname "$OUTPUT")"
: > "$OUTPUT"

is_retryable_network_failure() {
  local file="$1"
  grep -Eiq \
    'network timeout|audit endpoint returned an error|ECONNRESET|ETIMEDOUT|EAI_AGAIN|ENETUNREACH|ECONNREFUSED|socket hang up|fetch failed|network request failed|temporary failure in name resolution' \
    "$file"
}

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  tmp="$(mktemp)"
  {
    printf '=== npm audit attempt %s/%s ===\n' "$attempt" "$MAX_ATTEMPTS"
    printf 'audit_level=critical\n'
  } | tee -a "$OUTPUT"

  set +e
  npm_config_fetch_timeout=60000 \
  npm_config_fetch_retries=1 \
  npm_config_fetch_retry_mintimeout=1000 \
  npm_config_fetch_retry_maxtimeout=10000 \
    timeout --signal=TERM --kill-after=10s "${ATTEMPT_TIMEOUT_SECONDS}s" \
      npm audit --audit-level=critical >"$tmp" 2>&1
  rc=$?
  set -e

  cat "$tmp" | tee -a "$OUTPUT"

  if [ "$rc" -eq 0 ]; then
    printf 'NPM_AUDIT_GATE=PASS attempt=%s\n' "$attempt" | tee -a "$OUTPUT"
    rm -f "$tmp"
    exit 0
  fi

  retryable=0
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
    retryable=1
    printf 'retry_reason=bounded_timeout rc=%s\n' "$rc" | tee -a "$OUTPUT"
  elif is_retryable_network_failure "$tmp"; then
    retryable=1
    printf 'retry_reason=explicit_network_failure rc=%s\n' "$rc" | tee -a "$OUTPUT"
  fi

  rm -f "$tmp"

  if [ "$retryable" -ne 1 ]; then
    printf 'NPM_AUDIT_GATE=FAIL_NON_NETWORK rc=%s\n' "$rc" | tee -a "$OUTPUT" >&2
    exit "$rc"
  fi

  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    printf 'NPM_AUDIT_GATE=FAIL_NETWORK_RETRIES_EXHAUSTED attempts=%s\n' "$MAX_ATTEMPTS" | tee -a "$OUTPUT" >&2
    exit 75
  fi

  sleep "$attempt"
  attempt=$((attempt + 1))
done

printf 'NPM_AUDIT_GATE=FAIL_UNREACHABLE\n' | tee -a "$OUTPUT" >&2
exit 2
