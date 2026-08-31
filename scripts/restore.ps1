param([Parameter(Mandatory=$true)][string]$Backup,[string]$TargetDatabase="trading_restore")
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..")

if (-not (Test-Path -LiteralPath $Backup -PathType Leaf)) { throw "RESTORE_REFUSED backup_not_found" }
$ChecksumPath = "$Backup.sha256"
if (-not (Test-Path -LiteralPath $ChecksumPath -PathType Leaf)) { throw "RESTORE_REFUSED checksum_not_found" }
if ($TargetDatabase -notmatch '^[A-Za-z_][A-Za-z0-9_]{0,62}$') { throw "RESTORE_REFUSED invalid_target_database" }
if ($TargetDatabase -in @('trading','postgres','template0','template1')) { throw "RESTORE_REFUSED protected_target_database=$TargetDatabase" }

$expected = ((Get-Content -LiteralPath $ChecksumPath) -split '\s+')[0].ToLower()
$actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $Backup).Hash.ToLower()
if ($expected -ne $actual) { throw "backup checksum mismatch" }

$existing = docker compose exec -T postgres psql -U trading -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$TargetDatabase'"
if ($LASTEXITCODE -ne 0) { throw "RESTORE_REFUSED database_preflight_failed" }
if (($existing | Out-String).Trim() -eq '1') { throw "RESTORE_REFUSED target_database_exists=$TargetDatabase" }

$Staging = "restore_stage_$([System.Diagnostics.Process]::GetCurrentProcess().Id)_$([Random]::Shared.Next(100000,999999))"
$created = $false
try {
    docker compose exec -T postgres createdb -U trading $Staging
    if ($LASTEXITCODE -ne 0) { throw "restore staging database create failed" }
    $created = $true

    $cmd = "docker compose run --rm -T app python /app/scripts/backup_crypto.py decrypt --key-file /run/secrets/backup_encryption_key < `"$Backup`" | docker compose exec -T postgres pg_restore --exit-on-error --no-owner --no-acl -U trading --dbname=$Staging"
    cmd.exe /d /s /c $cmd
    if ($LASTEXITCODE -ne 0) { throw "restore failed" }

    docker compose exec -T postgres psql -U trading -d postgres -v ON_ERROR_STOP=1 -c "ALTER DATABASE `"$Staging`" RENAME TO `"$TargetDatabase`";"
    if ($LASTEXITCODE -ne 0) { throw "restore promotion failed" }
    $created = $false
    Write-Host "RESTORE_PASS database=$TargetDatabase promotion=atomic source=encrypted_backup"
}
finally {
    if ($created) {
        docker compose exec -T postgres dropdb -U trading --if-exists $Staging 2>$null | Out-Null
    }
}
