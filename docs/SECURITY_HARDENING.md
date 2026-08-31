# Production Security Hardening

Production credentials must be delivered through Docker secrets or an OS/cloud secret store; credentials must not be baked into images. TESTNET and LIVE exchange keys are separate identities and withdrawal permission remains disabled. Where infrastructure permits it, apply an IP allowlist at the exchange account and/or reverse-proxy/firewall boundary.

Container policy uses minimal/slim or distroless base images, non-root users, `no-new-privileges`, dropped capabilities, read-only filesystems where practical, no Docker socket mounts, only required published ports, and explicit CPU/memory resource limits for trading-facing services. These are configuration contracts; real runtime acceptance remains a separate gate.
