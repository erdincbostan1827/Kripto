# DEPLOYMENT_ARCHITECTURE.md

## Baseline
Nginx -> FastAPI API/engine + frontend static assets. PostgreSQL stores authoritative state; Redis is cache/fan-out. A separate worker handles research jobs and an independent watchdog checks signed heartbeat/health.

## Environments
DEV, TEST, STAGING, PROD are isolated from PAPER/TESTNET/LIVE mode. PROD credentials never enter tests. Promotion uses the same immutable artifact.

## Single-node production
External encrypted backups, restart/reconciliation and watchdog are mandatory. Host failure can cause downtime; protective exchange-native orders are preferred for open-position safety.

## HA profile
Active-standby only with leader lease + fencing token. A stale leader cannot submit orders. Failover requires exchange reconciliation before promotion.

## Reverse proxy / TLS
Production ingress terminates HTTPS/TLS at Nginx using mounted certificate/private-key secrets. HTTP should redirect to HTTPS, trusted proxy headers must be constrained to the known reverse proxy, and backend secure-cookie/HSTS/CSP behavior must remain enabled behind the proxy. Certificate renewal must not expose private key material to the frontend or application image.
