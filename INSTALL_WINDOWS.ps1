$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if ($env:CTP_INSTALL_LOCK_HELD -ne "1") {
  python scripts/operation_lock_exec.py --lock-dir .. --operation install --env-json '{"CTP_INSTALL_LOCK_HELD":"1"}' -- powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath
  exit $LASTEXITCODE
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker Desktop gerekli." }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3 gerekli." }
docker compose version | Out-Null
python scripts/bootstrap_dependency_locks.py --recover-only
if ($LASTEXITCODE -ne 0) { throw "Yarım kalmış dependency-lock transaction kurtarılamadı." }
if ((-not (Test-Path uv.lock)) -or (-not (Test-Path frontend/package-lock.json))) {
  Write-Host "Dependency lock dosyaları atomik olarak üretiliyor..."
  python scripts/bootstrap_dependency_locks.py
  if ($LASTEXITCODE -ne 0) { throw "Dependency lock dosyaları üretilemedi; canonical lock state değiştirilmedi." }
}
python scripts/bootstrap_env.py
if ($LASTEXITCODE -ne 0) { throw ".env bootstrap güvenli biçimde tamamlanamadı." }
python scripts/bootstrap_secrets.py
docker compose --profile test build test app frontend nginx
if ($LASTEXITCODE -ne 0) { throw "Docker build başarısız." }
docker compose up -d postgres redis
Start-Sleep -Seconds 3
docker compose run --rm app alembic -c /app/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { throw "Migration başarısız." }
docker compose --profile test run --rm test
if ($LASTEXITCODE -ne 0) { throw "Testler başarısız. LIVE açmayın." }
docker compose up -d
Invoke-WebRequest -UseBasicParsing http://localhost:8080/api/v1/health | Out-Null
python scripts/deployment_audit_chain.py append --root .. --event-type INSTALL_ACCEPTED --subjects-json '{"mode":"PAPER","health":"PASS"}' | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Deployment audit kaydı yazılamadı." }
Write-Host "Kurulum tamamlandı. İlk mod PAPER."
Write-Host "İlk admin bootstrap tokenı secrets/admin_bootstrap_token.txt dosyasındadır; değeri loglara veya sohbete kopyalamayın."
