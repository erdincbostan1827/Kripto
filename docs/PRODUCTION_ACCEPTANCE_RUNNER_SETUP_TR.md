# Production Acceptance Self-Hosted Runner Kurulumu

Bu belge `PROD LIVE` yetkisi vermez. Amaç, gerçek production acceptance workflow'unun ihtiyaç duyduğu self-hosted runner ve GitHub Environment önkoşullarını eksiksiz hazırlamaktır.

## 1. Runner için minimum sözleşme

GitHub Actions runner aşağıdaki iki label ile kayıtlı olmalıdır:

- `self-hosted`
- `production-acceptance`

Runner üzerinde çalışır durumda olması gereken temel araçlar:

- Git
- Bash
- Docker Engine / Docker daemon
- Docker Compose v2 (`docker compose`)

Production workflow Python 3.12 ve gerekli Python araç zincirini ayrıca pinli biçimde kurar. Runner kullanıcısının Docker daemon'a erişimi olmalıdır.

## 2. Önce secret-free readiness çalıştır

GitHub > Actions > **Production Runner Readiness** workflow'unu aç.

`candidate_ref` alanına doğrulanacak immutable exact commit SHA veya release tag gir. Main için güncel exact SHA'yı kullan; `main` gibi hareketli branch adı kullanma.

Workflow şu koşulları fail-closed kontrol eder:

- job gerçekten `[self-hosted, production-acceptance]` runner üzerinde çalışabiliyor mu,
- Git/Bash/Docker mevcut mu,
- Docker daemon erişilebilir mi,
- Docker Compose v2 çalışıyor mu,
- `docker compose config --quiet` başarılı mı,
- exact candidate Git HEAD okunabiliyor mu,
- `uv.lock` ve `frontend/package-lock.json` source-lock sözleşmesine uyuyor mu,
- evidence dizini yazılabilir mi.

Çıktı artifact'i:

`reports/production_acceptance/PRODUCTION_RUNNER_READINESS.json`

Bu rapor hiçbir TESTNET API anahtarı veya production secret değeri içermez.

## 3. GitHub Environment

Repository Settings > Environments altında `production-acceptance` isimli protected environment oluşturulmuş olmalıdır.

Environment variable olarak gerekenler:

- `ACCEPTANCE_ENVIRONMENT_ID`
- `ACCEPTANCE_TOPOLOGY_HASH`

`ACCEPTANCE_TOPOLOGY_HASH` gerçek acceptance hedef topolojisinin SHA-256 kimliğidir ve 64 hex karakter olmalıdır.

## 4. Protected secrets

Aşağıdaki değerleri repository dosyalarına veya `.env` dosyasına commit etme. Yalnız protected `production-acceptance` environment secret olarak tanımla:

- `BINANCE_TESTNET_API_KEY`
- `BINANCE_TESTNET_API_SECRET`
- `PITR_DRILL_COMMAND`
- `PITR_EVIDENCE_JSON`
- `HA_DRILL_COMMAND`
- `HA_EVIDENCE_JSON`
- `WORM_ACCEPTANCE_COMMAND`
- `WORM_EVIDENCE_JSON`
- `RESTART_DRILL_COMMAND`
- `RESTART_EVIDENCE_JSON`
- `PROVENANCE_SIGN_VERIFY_COMMAND`
- `ACCEPTANCE_CHALLENGE_VERIFY_COMMAND`
- `LEDGER_CHECKPOINT_SIGN_COMMAND`
- `ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND`

Komut secret'ları yalnız onaylı gerçek altyapıyı çağırmalıdır; sahte/mock evidence üretmek production acceptance sayılmaz.

## 5. Drill evidence gereksinimleri

PITR, HA, WORM ve restart komutları gerçek hedef ortamda çalışmalı ve ilgili `*_EVIDENCE_JSON` yoluna makine tarafından doğrulanabilir kanıt bırakmalıdır.

- PITR: izole restore tatbikatı
- HA: gerçek failover/failback tatbikatı
- WORM: değiştirilemez saklama kabul testi
- Restart: Redis/Postgres restart sonrası semantik sağlık kanıtı
- Provenance: detached signature + doğrulama kanıtı
- Ledger checkpoint: dış KMS/HSM/WORM imzası ve doğrulaması

## 6. TESTNET

Binance TESTNET anahtarları yalnız TESTNET hesabına ait olmalıdır. Production workflow `BINANCE_TESTNET_EXECUTE=YES` değerini kendisi verir; anahtar/secret olmadan testnet acceptance fail-closed kalır.

## 7. Gerçek Production Acceptance

Runner readiness PASS olduktan ve protected environment eksiksiz yapılandırıldıktan sonra GitHub > Actions > **Production Acceptance** workflow'unu aç.

`acceptance_ref` olarak yalnız immutable exact SHA veya release tag kullan.

Workflow sırası özetle:

1. Hosted CI build evidence
2. Immutable container image + digest
3. Bandit / Semgrep / Gitleaks / Trivy / Syft / SBOM / provenance
4. Aynı evidence'in self-hosted runner'a aktarılması
5. Fail-closed production real-target preflight
6. Runtime / restart / PITR / HA / WORM / TESTNET / provenance / campaign acceptance
7. Merged evidence verification
8. Final release gate

`production_ready=true` ve final release gate PASS olmadan LIVE açılmaz.

## 8. Sorun teşhisi

İlk önce `Production Runner Readiness` artifact'ini kontrol et. Runner readiness PASS ise `Production Acceptance` içindeki `real-target-evidence-<SHA>` artifact'inde:

- `reports/production_acceptance/PRODUCTION_ACCEPTANCE_PREFLIGHT.json`
- `reports/PRODUCTION_ACCEPTANCE_ORCHESTRATION.json`
- `reports/external_acceptance/**`

alanları gerçek blokajı gösterir.

Eksik secret veya dış altyapı hiçbir zaman PASS olarak yorumlanmamalıdır.
