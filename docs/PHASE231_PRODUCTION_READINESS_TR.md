# Phase 231 — Production Runner Readiness Kapanışı

Bu aşama, Phase 230 ile hazırlanmış Windows self-hosted `production-acceptance` runner üzerinde `Production Runner Readiness` workflow'unu exact commit SHA'ya bağlı ve fail-closed şekilde çalıştırır.

> Bu aşamanın PASS olması production-ready veya LIVE yetkisi vermez. Yalnız runner önkoşullarının gerçek Windows ortamında doğrulandığını kanıtlar.

## Önkoşullar

- Repository güncel olmalı.
- Windows PowerShell Yönetici olarak açılmalı.
- `gh auth status` başarılı olmalı.
- Self-hosted runner daha önce `tools/bootstrap_production_acceptance_runner_windows.ps1` ile hazırlanmış ve çalışıyor olmalı.
- Docker daemon, Docker Compose v2, Git Bash ve CPython 3.12.10 x64 + pip hazır olmalı.

## En kısa kullanım

Repository kök dizininde:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\run_phase231_production_readiness.ps1
```

`CandidateRef` verilmezse script GitHub `main` HEAD SHA'sını çözer ve bunu exact 40-hex SHA'ya sabitler.

Belirli bir exact SHA ile çalıştırmak için:

```powershell
.\tools\run_phase231_production_readiness.ps1 `
  -CandidateRef <40-karakter-exact-sha>
```

## Scriptin yaptığı doğrulamalar

1. GitHub CLI ve oturum doğrulaması.
2. Candidate ref'in exact 40 karakter SHA olması.
3. `tools/resolve_python312_windows.ps1` üzerinden sabit CPython 3.12.10 doğrulaması.
4. `Production Runner Readiness` workflow dispatch.
5. Workflow sonucunu `gh run watch --exit-status` ile PASS olmadan kabul etmeme.
6. `production-runner-readiness-<exact-sha>` artifact'ını indirme.
7. `PRODUCTION_RUNNER_READINESS.json` içinde:
   - classification doğrulaması,
   - `verified=true`,
   - `GIT_HEAD == exact candidate SHA`,
   - `runner_context.os == Windows`
   kontrolleri.
8. Yerel `PHASE231_RESULT.json` üretimi.

Başarılı kapanışta terminalde:

```text
PHASE231_READINESS=PASS
```

görülmelidir.

## PASS sonrası gerçek sonraki sınır

Phase 231 PASS sonrasında hâlâ aşağıdaki gerçek dış kanıtlar gereklidir:

1. `production-acceptance` GitHub Environment gerçek environment ID/topology hash ile hazırlanmalı.
2. TESTNET ve restart/PITR/HA/WORM/provenance/challenge/ledger protected secret'ları gerçek değerlerle girilmeli.
3. Aynı immutable SHA için `Production Acceptance` workflow çalıştırılmalı.
4. Real-target preflight ve bütün drill/evidence kapıları PASS olmalı.
5. Final release gate PASS olmadan `production_ready=true` veya LIVE execution etkinleştirilmemeli.
