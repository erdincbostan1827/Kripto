[CmdletBinding()]
param(
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$RunnerDirectory = "C:\actions-runner-kripto-prod",
    [string]$RunnerName = "kripto-production-acceptance-$env:COMPUTERNAME",
    [string]$CandidateRef = "",
    [ValidateSet("Foreground", "Service")]
    [string]$Mode = "Foreground",
    [string]$AcceptanceEnvironmentId = "",
    [string]$TopologyDescriptorPath = "",
    [switch]$ConfigureProtectedSecrets
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$RunnerVersion = "2.337.0"
$RunnerArchive = "actions-runner-win-x64-$RunnerVersion.zip"
$RunnerUrl = "https://github.com/actions/runner/releases/download/v$RunnerVersion/$RunnerArchive"
$RunnerSha256 = "1150692afa94e71f872017e254ea55b6eece1eece3fe7e3a6d4c93d0a1b85cfc"
$EnvironmentName = "production-acceptance"
$RequiredSecretNames = @(
    "BINANCE_TESTNET_API_KEY",
    "BINANCE_TESTNET_API_SECRET",
    "PITR_DRILL_COMMAND",
    "PITR_EVIDENCE_JSON",
    "HA_DRILL_COMMAND",
    "HA_EVIDENCE_JSON",
    "WORM_ACCEPTANCE_COMMAND",
    "WORM_EVIDENCE_JSON",
    "RESTART_DRILL_COMMAND",
    "RESTART_EVIDENCE_JSON",
    "PROVENANCE_SIGN_VERIFY_COMMAND",
    "ACCEPTANCE_CHALLENGE_VERIFY_COMMAND",
    "LEDGER_CHECKPOINT_SIGN_COMMAND",
    "ACCEPTANCE_LEDGER_CHECKPOINT_VERIFY_COMMAND"
)

function Write-Stage([string]$Text) {
    Write-Host "`n=== $Text ==="
}

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script from an elevated PowerShell window (Run as administrator)."
    }
}

function Assert-Python312 {
    $resolver = Join-Path $PSScriptRoot "resolve_python312_windows.ps1"
    if (-not (Test-Path -LiteralPath $resolver -PathType Leaf)) {
        throw "Python resolver is missing: $resolver"
    }
    & $resolver | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Windows Python 3.12 validation failed."
    }
}

function Resolve-ExactCandidateSha {
    param([string]$RequestedRef)
    if ($RequestedRef) {
        if ($RequestedRef -notmatch '^[0-9a-fA-F]{40}$') {
            throw "CandidateRef must be an exact 40-hex commit SHA. Moving branch names are not accepted."
        }
        return $RequestedRef.ToLowerInvariant()
    }

    $resolved = (& gh api "repos/$Repository/commits/main" --jq '.sha').Trim()
    if ($LASTEXITCODE -ne 0 -or $resolved -notmatch '^[0-9a-fA-F]{40}$') {
        throw "Could not resolve main to an exact commit SHA."
    }
    return $resolved.ToLowerInvariant()
}

function Ensure-GitHubEnvironment {
    param([string]$ExactSha)
    Write-Stage "GitHub protected environment bootstrap"
    '{}' | gh api --method PUT "repos/$Repository/environments/$EnvironmentName" --input - *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create or verify GitHub Environment '$EnvironmentName'. Repository admin permission is required."
    }

    if ($AcceptanceEnvironmentId) {
        Invoke-Checked gh variable set ACCEPTANCE_ENVIRONMENT_ID --env $EnvironmentName --repo $Repository --body $AcceptanceEnvironmentId
    }

    if ($TopologyDescriptorPath) {
        $resolvedTopology = (Resolve-Path $TopologyDescriptorPath).Path
        $topologyHash = (Get-FileHash -Algorithm SHA256 -Path $resolvedTopology).Hash.ToLowerInvariant()
        if ($topologyHash -notmatch '^[0-9a-f]{64}$') {
            throw "Topology SHA-256 is invalid."
        }
        Invoke-Checked gh variable set ACCEPTANCE_TOPOLOGY_HASH --env $EnvironmentName --repo $Repository --body $topologyHash
        Write-Host "Topology hash configured from local descriptor: $topologyHash"
    }

    Write-Host "Exact acceptance candidate: $ExactSha"
    if (-not $AcceptanceEnvironmentId) {
        Write-Warning "ACCEPTANCE_ENVIRONMENT_ID was not changed because -AcceptanceEnvironmentId was not supplied."
    }
    if (-not $TopologyDescriptorPath) {
        Write-Warning "ACCEPTANCE_TOPOLOGY_HASH was not changed because -TopologyDescriptorPath was not supplied."
    }
}

function Configure-ProtectedSecretsInteractive {
    Write-Stage "Protected production-acceptance secrets"
    Write-Host "Each command below lets GitHub CLI read the value interactively. Values are not written to repository files by this script."
    foreach ($name in $RequiredSecretNames) {
        Write-Host "Configure secret: $name"
        & gh secret set $name --env $EnvironmentName --repo $Repository
        if ($LASTEXITCODE -ne 0) {
            throw "Failed while configuring protected secret: $name"
        }
    }
}

function Get-ExistingRunnerListener {
    $expectedListener = Join-Path $RunnerDirectory "bin\Runner.Listener.exe"
    if (-not (Test-Path -LiteralPath $expectedListener -PathType Leaf)) {
        return $null
    }

    $resolvedExpected = (Resolve-Path -LiteralPath $expectedListener).Path
    foreach ($process in @(Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue)) {
        try {
            if ($process.Path -and ((Resolve-Path -LiteralPath $process.Path).Path -eq $resolvedExpected)) {
                return $process
            }
        } catch {
            continue
        }
    }
    return $null
}

function Install-Runner {
    param([string]$ExactSha)
    Write-Stage "Download and verify GitHub Actions Runner v$RunnerVersion"

    $existingConfig = Join-Path $RunnerDirectory ".runner"
    $reuseExisting = Test-Path -LiteralPath $existingConfig -PathType Leaf

    if ($reuseExisting) {
        Write-Host "Existing runner configuration detected and will be reused: $RunnerDirectory"
        if ($Mode -eq "Service" -and -not (Test-Path -LiteralPath (Join-Path $RunnerDirectory ".service") -PathType Leaf)) {
            throw "Existing runner is not configured as a Windows service. Reconfigure it explicitly before using -Mode Service."
        }
    } else {
        if (-not (Test-Path -LiteralPath $RunnerDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $RunnerDirectory -Force | Out-Null
        }

        $tempArchive = Join-Path ([IO.Path]::GetTempPath()) "$([guid]::NewGuid().ToString('N'))-$RunnerArchive"
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $RunnerUrl -OutFile $tempArchive
            $actualHash = (Get-FileHash -Algorithm SHA256 -Path $tempArchive).Hash.ToLowerInvariant()
            if ($actualHash -ne $RunnerSha256) {
                throw "GitHub Actions Runner checksum mismatch. Expected $RunnerSha256 but got $actualHash."
            }

            Expand-Archive -Path $tempArchive -DestinationPath $RunnerDirectory -Force
        } finally {
            Remove-Item -Force -ErrorAction SilentlyContinue $tempArchive
        }

        Write-Stage "Acquire short-lived runner registration token"
        $registrationToken = (& gh api --method POST "repos/$Repository/actions/runners/registration-token" --jq '.token').Trim()
        if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($registrationToken)) {
            throw "Could not obtain runner registration token. Repository admin permission is required."
        }

        try {
            Push-Location $RunnerDirectory
            try {
                $configArgs = @(
                    "--unattended",
                    "--replace",
                    "--url", "https://github.com/$Repository",
                    "--token", $registrationToken,
                    "--name", $RunnerName,
                    "--labels", "production-acceptance",
                    "--work", "_work"
                )
                if ($Mode -eq "Service") {
                    $configArgs += "--runasservice"
                }

                & .\config.cmd @configArgs
                if ($LASTEXITCODE -ne 0) {
                    throw "GitHub Actions Runner configuration failed with exit code $LASTEXITCODE."
                }
            } finally {
                Pop-Location
            }
        } finally {
            $registrationToken = $null
            [GC]::Collect()
        }
    }

    Write-Stage "Start or verify runner"
    if ($Mode -eq "Service") {
        $serviceFile = Join-Path $RunnerDirectory ".service"
        if (-not (Test-Path -LiteralPath $serviceFile -PathType Leaf)) {
            throw "Runner requested Service mode but .service was not created."
        }
        $serviceName = (Get-Content $serviceFile -Raw).Trim()
        if ([string]::IsNullOrWhiteSpace($serviceName)) {
            throw "Runner service name is empty."
        }
        $service = Get-Service -Name $serviceName
        if ($service.Status -ne "Running") {
            Start-Service -Name $serviceName
            $service = Get-Service -Name $serviceName
        }
        if ($service.Status -ne "Running") {
            throw "Runner service did not enter Running state: $serviceName"
        }
        Write-Host "Runner service is Running: $serviceName"
    } else {
        $existingListener = Get-ExistingRunnerListener
        if ($existingListener) {
            Write-Host "Foreground runner is already running. PID=$($existingListener.Id)"
        } else {
            $runCmd = Join-Path $RunnerDirectory "run.cmd"
            if (-not (Test-Path -LiteralPath $runCmd -PathType Leaf)) {
                throw "Runner executable is missing: $runCmd"
            }
            $process = Start-Process -FilePath $runCmd -WorkingDirectory $RunnerDirectory -PassThru
            Start-Sleep -Seconds 3
            if ($process.HasExited) {
                throw "Foreground runner exited immediately. Inspect $RunnerDirectory\_diag."
            }
            Write-Host "Foreground runner process started. PID=$($process.Id). Keep the Windows session available until acceptance is complete."
        }
    }

    Write-Host "Runner labels expected by GitHub workflow: self-hosted, production-acceptance"
    Write-Host "Candidate SHA for readiness: $ExactSha"
}

Write-Stage "Fail-closed preflight"
Assert-Administrator
Assert-Command gh
Assert-Command git
Assert-Command bash
Assert-Command docker

Invoke-Checked gh auth status
Invoke-Checked git --version
Invoke-Checked bash --version
Invoke-Checked docker --version
Invoke-Checked docker info
Invoke-Checked docker compose version
Assert-Python312

$exactSha = Resolve-ExactCandidateSha -RequestedRef $CandidateRef
Ensure-GitHubEnvironment -ExactSha $exactSha
if ($ConfigureProtectedSecrets) {
    Configure-ProtectedSecretsInteractive
}
Install-Runner -ExactSha $exactSha

Write-Stage "Bootstrap completed"
Write-Host "Repository: $Repository"
Write-Host "Runner: $RunnerName"
Write-Host "Mode: $Mode"
Write-Host "Exact candidate SHA: $exactSha"
Write-Host "Next acceptance boundary: Production Runner Readiness must PASS for this exact SHA before Production Acceptance is attempted."
Write-Host "No production-ready/LIVE claim is made by this bootstrap."
