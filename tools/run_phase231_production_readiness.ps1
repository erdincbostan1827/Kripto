[CmdletBinding()]
param(
    [string]$CandidateRef,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase231-readiness",
    [int]$DiscoveryTimeoutSeconds = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is unavailable: $Name"
    }
}

function Invoke-Gh {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $output = & gh @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "gh command failed: gh $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)"
    }
    return @($output)
}

function Get-RunCreatedAt {
    param([Parameter(Mandatory = $false)]$Run)

    if ($null -eq $Run) {
        return $null
    }

    $property = $Run.PSObject.Properties["createdAt"]
    if ($null -eq $property) {
        return $null
    }

    $value = [string]$property.Value
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $null
    }

    try {
        return [DateTimeOffset]$value
    }
    catch {
        return $null
    }
}

function Get-RunDisplayTitle {
    param([Parameter(Mandatory = $false)]$Run)

    if ($null -eq $Run) {
        return $null
    }

    $property = $Run.PSObject.Properties["displayTitle"]
    if ($null -eq $property) {
        return $null
    }

    $value = [string]$property.Value
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $null
    }
    return $value
}

function Write-PhaseResult {
    param(
        [Parameter(Mandatory = $true)][bool]$Passed,
        [string]$RunId,
        [string]$Detail
    )

    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE231_PRODUCTION_RUNNER_READINESS_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Production Runner Readiness"
        run_id = $RunId
        detail = $Detail
        production_ready = $false
        truth_policy = "Readiness PASS proves runner prerequisites only; it does not authorize LIVE trading or production execution."
    }

    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $resultPath = Join-Path $resolvedOutput "PHASE231_RESULT.json"
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runId = ""
try {
    Require-Command -Name "gh"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    if ([string]::IsNullOrWhiteSpace($CandidateRef)) {
        $resolved = Invoke-Gh -Arguments @("api", "repos/$Repository/commits/main", "--jq", ".sha")
        $CandidateRef = ($resolved | Select-Object -First 1).Trim()
    }

    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') {
        throw "CandidateRef must resolve to an exact 40-character commit SHA. Got: '$CandidateRef'"
    }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    $expectedRunTitle = "Production Runner Readiness $CandidateRef"

    $resolverPath = Join-Path $PSScriptRoot "resolve_python312_windows.ps1"
    if (-not (Test-Path -LiteralPath $resolverPath -PathType Leaf)) {
        throw "Pinned Python resolver not found: $resolverPath"
    }
    & $resolverPath | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Pinned Python 3.12.10 resolver failed."
    }

    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "Production Runner Readiness",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "candidate_ref=$CandidateRef"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list",
            "--repo", $Repository,
            "--workflow", "Production Runner Readiness",
            "--event", "workflow_dispatch",
            "--limit", "20",
            "--json", "databaseId,createdAt,status,conclusion,displayTitle"
        )) -join "`n"

        $parsedRuns = $json | ConvertFrom-Json
        $runs = @()
        if ($null -ne $parsedRuns) {
            if ($parsedRuns -is [System.Array]) {
                $runs = @($parsedRuns | ForEach-Object { $_ })
            }
            else {
                $runs = @($parsedRuns)
            }
        }

        $candidateRuns = @(
            $runs | Where-Object {
                $createdAt = Get-RunCreatedAt -Run $_
                $displayTitle = Get-RunDisplayTitle -Run $_
                ($null -ne $createdAt) -and
                    ($createdAt -ge $dispatchStarted.AddSeconds(-10)) -and
                    ($displayTitle -eq $expectedRunTitle)
            } | Sort-Object { Get-RunCreatedAt -Run $_ } -Descending
        )

        if ($candidateRuns.Count -gt 0) {
            $databaseIdProperty = $candidateRuns[0].PSObject.Properties["databaseId"]
            if ($null -eq $databaseIdProperty -or [string]::IsNullOrWhiteSpace([string]$databaseIdProperty.Value)) {
                throw "Discovered readiness run does not expose databaseId."
            }
            $runId = [string]$databaseIdProperty.Value
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)

    if ([string]::IsNullOrWhiteSpace($runId)) {
        throw "Could not discover the dispatched Production Runner Readiness run for exact candidate '$CandidateRef'."
    }

    & gh run watch $runId --repo $Repository --exit-status
    if ($LASTEXITCODE -ne 0) {
        throw "Production Runner Readiness workflow did not PASS. Run id: $runId"
    }

    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $resolvedOutput) {
        Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

    $artifactName = "production-runner-readiness-$CandidateRef"
    Invoke-Gh -Arguments @(
        "run", "download", $runId,
        "--repo", $Repository,
        "--name", $artifactName,
        "--dir", $resolvedOutput
    ) | Out-Null

    $reportPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PRODUCTION_RUNNER_READINESS.json" |
        Select-Object -First 1 -ExpandProperty FullName
    if (-not $reportPath) {
        throw "Readiness artifact did not contain PRODUCTION_RUNNER_READINESS.json."
    }

    $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    if ($report.classification -ne "PRODUCTION_ACCEPTANCE_RUNNER_READINESS") {
        throw "Unexpected readiness evidence classification: $($report.classification)"
    }
    if ($report.verified -ne $true) {
        throw "Readiness evidence is not verified."
    }
    if ($report.checks.GIT_HEAD.detail -ne $CandidateRef) {
        throw "Readiness evidence is bound to a different git SHA: $($report.checks.GIT_HEAD.detail)"
    }
    if ($report.runner_context.os -ne "Windows") {
        throw "Readiness evidence did not run on Windows: $($report.runner_context.os)"
    }

    Write-PhaseResult -Passed $true -RunId $runId -Detail "Exact-SHA self-hosted runner readiness verified."
    Write-Host "PHASE231_READINESS=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "No production-ready/LIVE claim is made by this phase."
}
catch {
    $message = $_.Exception.Message
    try {
        Write-PhaseResult -Passed $false -RunId $runId -Detail $message
    }
    catch {
        Write-Warning "Could not write Phase 231 result JSON: $($_.Exception.Message)"
    }
    Write-Host "PHASE231_READINESS=FAIL"
    throw
}
