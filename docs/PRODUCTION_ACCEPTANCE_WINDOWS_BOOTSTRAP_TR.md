# Windows Production Acceptance Bootstrap

Bu belge ve `tools/bootstrap_production_acceptance_runner_windows.ps1` production kabul altyapısını hazırlamayı otomatikleştirir. Bootstrap tek başına `PROD LIVE` yetkisi vermez; gerçek dış kanıt kapıları PASS olmadan sistem fail-closed kalır.

## Önkoşullar

Windows makinede **Yönetici olarak PowerShell** aç. Aşağıdakiler kurulu ve çalışır olmalıdır:

- GitHub CLI (`gh`) ve repository sahibi/yöneticisi hesabıyla `gh auth login`
- Git + Git Bash (`bash` PATH üzerinde)
- Docker ve çalışan Docker daemon
- Docker Compose v2 (`docker compose`)
- CPython **3.12.x x64** ve çalışan `pip`

Python 3.12 kurulu değilse yönetici PowerShell'de:

```powershell
winget install --id Python.Python.3.12 -e --scope machine --accept-source-agreements --accept-package-agreements
```

Kurulumdan sonra yeni bir PowerShell açıp mümkünse doğrula:

```powershell
python --version
python -m pip --version
```

`python` mevcut oturumun PATH'inde henüz görünmese bile `tools/resolve_python312_windows.ps1` PATH, Windows Python registry kayıtları ve standart kurulum dizinlerini kontrol eder. Yalnız gerçek bir `3.12.x` yorumlayıcı ve çalışan `pip` bulursa devam eder; aksi durumda acceptance fail-closed kalır.

Bootstrap GitHub Actions Runner **v2.337.0** Windows x64 paketini indirir ve sabit SHA-256 ile doğrular. Hash eşleşmezse işlem durur.

## En kısa güvenli kullanım

Repository'yi klonladıktan sonra exact SHA'yı belirle ve foreground runner kur/doğrula:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\tools\bootstrap_production_acceptance_runner_windows.ps1 `
  -CandidateRef <40-karakter-exact-main-SHA> `
  -Mode Foreground
```

`-CandidateRef` verilmezse script o anda `main` HEAD'ini GitHub API üzerinden çözer ve sonrasında yalnız çözülen exact 40-hex SHA'yı kullanır.

Aynı `C:\actions-runner-kripto-prod` dizininde daha önce yapılandırılmış runner varsa bootstrap kaydı silmez veya ikinci kez yapılandırmaya zorlamaz. Mevcut `.runner` kaydını yeniden kullanır; foreground listener zaten çalışıyorsa mevcut PID'yi doğrular, çalışmıyorsa `run.cmd` ile başlatır. Bu davranış, geçerli production-acceptance runner kaydının yanlışlıkla bozulmasını önler.

Foreground modu, özellikle Docker Desktop kullanan Windows masaüstlerinde servis hesabı/Docker named-pipe erişim sorunlarını ayırmak için önerilen ilk doğrulamadır. Runner başladıktan sonra `Production Runner Readiness` workflow'u aynı exact SHA ile PASS olmalıdır.

## Production Runner Readiness çalıştırma

Bootstrap PASS olduktan sonra exact SHA için:

```powershell
gh workflow run "Production Runner Readiness" `
  --ref main `
  -f candidate_ref=<40-karakter-exact-main-SHA>
```

Readiness workflow'u self-hosted Windows runner üzerinde repository'deki `tools/resolve_python312_windows.ps1` ile Python 3.12'yi doğrular ve workflow PATH'ine bağlar. Python runtime doğrulanmazsa readiness PASS sayılmaz.

## Protected environment değişkenlerini de hazırlamak

Gerçek hedef ortam kimliği ve topoloji descriptor dosyası hazırsa:

```powershell
.\tools\bootstrap_production_acceptance_runner_windows.ps1 `
  -CandidateRef <40-karakter-exact-main-SHA> `
  -Mode Foreground `
  -AcceptanceEnvironmentId "<gercek-ortam-kimligi>" `
  -TopologyDescriptorPath "C:\secure\production-topology.json"
```

Script:

- `production-acceptance` GitHub Environment'ını oluşturur/doğrular,
- `ACCEPTANCE_ENVIRONMENT_ID` variable'ını ayarlar,
- descriptor dosyasının SHA-256 değerini hesaplayıp `ACCEPTANCE_TOPOLOGY_HASH` olarak ayarlar.

Topoloji hash'i uydurulmaz; gerçek descriptor dosyasından üretilir.

## Protected secret'ları interaktif girmek

Gerçek TESTNET ve drill komut/evidence değerleri hazırsa `-ConfigureProtectedSecrets` ekle:

```powershell
.\tools\bootstrap_production_acceptance_runner_windows.ps1 `
  -CandidateRef <40-karakter-exact-main-SHA> `
  -Mode Foreground `
  -AcceptanceEnvironmentId "<gercek-ortam-kimligi>" `
  -TopologyDescriptorPath "C:\secure\production-topology.json" `
  -ConfigureProtectedSecrets
```

GitHub CLI her secret'ı interaktif olarak alır. Bootstrap secret değerini repository dosyasına yazmaz ve komut satırı `--body` argümanına koymaz.

İstenen protected secret'lar:

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

Bu değerlerin mock/sahte karşılıkları kullanılmamalıdır.

## Servis modu

Foreground readiness PASS olduktan ve kullandığın Docker kurulumu servis hesabından erişilebilir olduğundan emin olduktan sonra kalıcı runner için Service modu kullanılabilir. Mevcut runner foreground olarak yapılandırılmışsa bootstrap onu sessizce servis moduna dönüştürmez; bunun için runner'ın açık ve bilinçli biçimde yeniden yapılandırılması gerekir.

Temiz servis kurulumu örneği:

```powershell
.\tools\bootstrap_production_acceptance_runner_windows.ps1 `
  -RunnerDirectory "C:\actions-runner-kripto-prod-service" `
  -CandidateRef <40-karakter-exact-main-SHA> `
  -Mode Service
```

Windows servis yapılandırması runner `config.cmd --runasservice` aşamasında yapılır. Servis başladıktan sonra readiness workflow'unu yeniden çalıştır ve PASS olmadan Production Acceptance'a geçme.

## Kabul sırası

1. CPython 3.12.x + pip — gerçek Windows runner üzerinde PASS
2. `Production Runner Readiness` — exact SHA — PASS
3. Protected environment variable/secrets gerçek değerlerle hazır
4. `Production Acceptance` — aynı immutable SHA — çalıştır
5. real-target preflight — PASS
6. restart/PITR/HA/WORM/TESTNET/provenance/challenge/ledger evidence — PASS
7. merged external evidence verification — PASS
8. final release gate — PASS
9. `production_ready=true`

Bu zincirin tamamı aynı release-bound challenge üzerinde doğrulanmadan gerçek para/LIVE execution etkinleştirilmez.
