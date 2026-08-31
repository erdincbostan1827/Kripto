param([string]$BackupDir = ".\backups")
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..")
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$out = Join-Path $BackupDir "trading_$stamp.dump.enc"
$tmp = "$out.tmp"
$cmd = "docker compose exec -T postgres pg_dump -U trading --format=custom --no-owner --no-acl trading | docker compose exec -T app python /app/scripts/backup_crypto.py encrypt --key-file /run/secrets/backup_encryption_key > `"$tmp`""
cmd.exe /d /s /c $cmd
if ($LASTEXITCODE -ne 0) { Remove-Item -Force -ErrorAction SilentlyContinue $tmp; throw "encrypted backup pipeline failed" }
Move-Item -Force $tmp $out
$hash = (Get-FileHash -Algorithm SHA256 $out).Hash.ToLower()
"$hash  $(Split-Path -Leaf $out)" | Set-Content -Encoding ascii "$out.sha256"
Write-Output $out
