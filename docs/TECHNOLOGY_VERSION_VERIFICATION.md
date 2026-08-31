# Technology Version Verification — 2026-08-29

Classification: **REFERENCE VERIFIED — DEPENDENCY RESOLUTION / BUILD NOT ACCEPTED**

The project does not blindly copy prompt-era versions. Stable-version references are checked against official upstream release pages before manifest changes. On 2026-08-29 the official Tauri ecosystem release index lists:

- Tauri core: `2.11.5` (2026-07-01)
- Tauri CLI / `@tauri-apps/cli`: `2.11.4` (2026-06-28)
- `tauri-build`: `2.6.3` (2026-06-17)
- Tauri notification plugin: `2.3.3` (2025-10-27)

Official references:
- `https://tauri.app/release/`
- `https://tauri.app/release/tauri/all-versions/`
- `https://tauri.app/release/tauri-build/all-versions/`
- `https://tauri.app/release/tauri-cli/all-versions/`

## Upgrade policy

1. A major upgrade is never applied solely because a prompt names a newer version.
2. Major upgrades require upstream migration/release-note review plus focused regression coverage before merge.
3. Exact direct dependency versions may be recorded in manifests, but **a lockfile is required before production dependency acceptance**.
4. This environment currently cannot resolve the required npm/Python/Rust dependency graphs, so no lockfile, desktop build, installer, vulnerability result, or transitive-SBOM result is claimed.
5. The optional Tauri source shell is therefore **source-contract ready, build NOT_TESTED**.

## Desktop security boundary

The optional desktop client packages the existing React UI only. Trading, order reconciliation, position management, risk controls, scheduler state and protective-order ownership remain server-side. The shell exposes no command for exchange API secrets, private-key storage, withdrawals, or execution-engine ownership. A closed desktop client therefore cannot stop server-side open-position management.
