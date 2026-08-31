# SECURITY_MODEL.md

- Roles: viewer, trader, admin; least privilege.
- Passwords: Argon2id; MFA: TOTP; recovery codes hashed and single-use.
- Session: opaque server-side id; Secure/HttpOnly/SameSite=Strict; inactivity timeout and revocation.
- High-risk actions: re-auth + one-time confirmation nonce; backend gate remains authoritative.
- Exchange credentials: never sent to frontend after submission; encrypted at application boundary when persisted; fingerprints only in UI/logs.
- API permissions: READ+TRADE only; withdrawal permission blocks LIVE.
- Browser: CSP/HSTS/frame protection/content-type protection, CORS allowlist, CSRF protection for cookie-auth mutations.
- Audit: hash chained tamper-evident entries for LIVE/config/credential/order/reconciliation/deployment events.
- Containers: non-root, no Docker socket, no privileged mode, drop capabilities, read-only filesystem where possible.

### Phase 192 deployment evidence boundary

Deployment audit acceptance is hash chained and fail closed on any earlier-chain tamper. Externally supplied signatures are not trusted merely because signature bytes exist; a distinct verifier identity must validate the subject hash, canonical digest, and signing identity before trusted provenance can be represented. This local contract prepares and verifies evidence structure but does not substitute for a real CI/KMS/Sigstore trust provider.
