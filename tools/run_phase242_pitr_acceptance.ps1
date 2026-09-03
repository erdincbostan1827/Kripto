[CmdletBinding()]
param(
    [string]$CandidateRef,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase242-pitr",
    [int]$DiscoveryTimeoutSeconds = 90
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

function Get-RunProperty {
    param(
        [Parameter(Mandatory = $false)]$Run,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if ($null -eq $Run) { return $null }
    $property = $Run.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-RunCreatedAt {
    param([Parameter(Mandatory = $false)]$Run)
    $value = [string](Get-RunProperty -Run $Run -Name "createdAt")
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    try { return [DateTimeOffset]$value } catch { return $null }
}

function Write-PhaseResult {
    param(
        [Parameter(Mandatory = $true)][bool]$Passed,
        [string]$RunId,
        [string]$Detail,
        [string]$Blocker
    )
    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE242_PITR_ACCEPTANCE_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Phase 242 PITR Acceptance"
        run_id = $RunId
        detail = $Detail
        blocker = $Blocker
        production_ready = $false
        truth_policy = "Phase 242 PASS closes only the exact-SHA runtime prerequisite and PITR acceptance on the intended Windows target identity. It does not authorize LIVE trading or close TESTNET/HA/WORM/signing/campaign gates."
    }
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $resultPath = Join-Path $resolvedOutput "PHASE242_ORCHESTRATION_RESULT.json"
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runId = ""
$blocker = ""
try {
    Require-Command -Name "gh"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    if ([string]::IsNullOrWhiteSpace($CandidateRef)) {
        $resolved = Invoke-Gh -Arguments @("api", "repos/$Repository/commits/main", "--jq", ".sha")
        $CandidateRef = ([string]($resolved | Select-Object -First 1)).Trim()
    }
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') {
        throw "CandidateRef must resolve to an exact 40-character commit SHA. Got: '$CandidateRef'"
    }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    $expectedRunTitle = "Phase 242 PITR Acceptance $CandidateRef"

    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "Phase 242 PITR Acceptance",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "candidate_ref=$CandidateRef"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list",
            "--repo", $Repository,
            "--workflow", "Phase 242 PITR Acceptance",
            "--event", "workflow_dispatch",
            "--limit", "20",
            "--json", "databaseId,createdAt,status,conclusion,displayTitle"
        )) -join "`n"
        $parsedRuns = $json | ConvertFrom-Json
        $runs = @()
        if ($null -ne $parsedRuns) {
            if ($parsedRuns -is [System.Array]) { $runs = @($parsedRuns | ForEach-Object { $_ }) }
            else { $runs = @($parsedRuns) }
        }
        $candidateRuns = @(
            $runs | Where-Object {
                $createdAt = Get-RunCreatedAt -Run $_
                $displayTitle = [string](Get-RunProperty -Run $_ -Name "displayTitle")
                ($null -ne $createdAt) -and
                    ($createdAt -ge $dispatchStarted.AddSeconds(-10)) -and
                    ($displayTitle -eq $expectedRunTitle)
            } | Sort-Object { Get-RunCreatedAt -Run $_ } -Descending
        )
        if ($candidateRuns.Count -gt 0) {
            $runId = [string](Get-RunProperty -Run $candidateRuns[0] -Name "databaseId")
            if ([string]::IsNullOrWhiteSpace($runId)) {
                throw "Discovered Phase 242 run does not expose databaseId."
            }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)

    if ([string]::IsNullOrWhiteSpace($runId)) {
        throw "Could not discover the dispatched Phase 242 PITR Acceptance run for exact candidate '$CandidateRef'."
    }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $resolvedOutput) {
        Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

    $artifactName = "phase242-pitr-acceptance-$CandidateRef"
    Invoke-Gh -Arguments @(
        "run", "download", $runId,
        "--repo", $Repository,
        "--name", $artifactName,
        "--dir", $resolvedOutput
    ) | Out-Null

    $workflowResultPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PHASE242_PITR_RESULT.json" |
        Select-Object -First 1 -ExpandProperty FullName
    $identityPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PITR_TARGET_IDENTITY.json" |
        Select-Object -First 1 -ExpandProperty FullName
    $runtimePath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "manifest_runtime.json" |
        Select-Object -First 1 -ExpandProperty FullName
    $pitrPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "manifest_pitr.json" |
        Select-Object -First 1 -ExpandProperty FullName

    if (-not $workflowResultPath) { throw "Phase 242 artifact did not contain PHASE242_PITR_RESULT.json." }
    if (-not $identityPath) { throw "Phase 242 artifact did not contain PITR_TARGET_IDENTITY.json." }
    if (-not $runtimePath) { throw "Phase 242 artifact did not contain manifest_runtime.json." }
    if (-not $pitrPath) { throw "Phase 242 artifact did not contain manifest_pitr.json." }

    $workflowResult = Get-Content -LiteralPath $workflowResultPath -Raw | ConvertFrom-Json
    $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    $runtime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
    $pitr = Get-Content -LiteralPath $pitrPath -Raw | ConvertFrom-Json

    if ($workflowResult.classification -ne "PHASE242_PITR_ACCEPTANCE_WORKFLOW_RESULT") {
        throw "Unexpected Phase 242 workflow result classification: $($workflowResult.classification)"
    }
    if ($identity.classification -ne "PHASE242_PITR_TARGET_IDENTITY_NOT_ACCEPTANCE_EVIDENCE") {
        throw "Unexpected Phase 242 target identity classification: $($identity.classification)"
    }
    if ($identity.candidate_sha -ne $CandidateRef) {
        throw "Phase 242 target identity is bound to a different git SHA: $($identity.candidate_sha)"
    }
    if ($identity.runner_os -ne "Windows") {
        throw "Phase 242 target identity did not run on Windows: $($identity.runner_os)"
    }

    foreach ($manifest in @($runtime, $pitr)) {
        if ($manifest.classification -ne "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE") {
            throw "Unexpected external acceptance classification: $($manifest.classification)"
        }
        if ($manifest.environment.git_commit_sha -ne $CandidateRef) {
            throw "Acceptance evidence is bound to a different git SHA: $($manifest.environment.git_commit_sha)"
        }
        if ($manifest.environment.topology_hash -ne $identity.topology_hash) {
            throw "Acceptance evidence topology hash does not match the Phase 242 target identity."
        }
    }
    if ($runtime.profile -ne "runtime") { throw "Unexpected runtime profile: $($runtime.profile)" }
    if ($pitr.profile -ne "pitr") { throw "Unexpected PITR profile: $($pitr.profile)" }
    if ($workflowResult.candidate_sha -ne $CandidateRef) {
        throw "Phase 242 workflow result is bound to a different git SHA: $($workflowResult.candidate_sha)"
    }

    if ($null -ne $workflowResult.PSObject.Properties["blocker"]) { $blocker = [string]$workflowResult.blocker }
    if ([string]::IsNullOrWhiteSpace($blocker) -and $null -ne $pitr.PSObject.Properties["blocker"]) {
        $blocker = [string]$pitr.blocker
    }
    if ([string]::IsNullOrWhiteSpace($blocker) -and $null -ne $runtime.PSObject.Properties["blocker"]) {
        $blocker = [string]$runtime.blocker
    }

    $runtimeStatus = [string]$runtime.groups.runtime
    $pitrStatus = [string]$pitr.groups.pitr
    $passed = (
        $workflowPassed -and
        $workflowResult.passed -eq $true -and
        $runtime.real_target_explicitly_confirmed -eq $true -and
        $pitr.real_target_explicitly_confirmed -eq $true -and
        $runtime.challenge.verified -eq $true -and
        $pitr.challenge.verified -eq $true -and
        $runtime.challenge.trust_verified -eq $true -and
        $pitr.challenge.trust_verified -eq $true -and
        $runtime.selected_all_pass -eq $true -and
        $pitr.selected_all_pass -eq $true -and
        $runtimeStatus -eq "PASS" -and
        $pitrStatus -eq "PASS"
    )

    if (-not $passed) {
        if ([string]::IsNullOrWhiteSpace($blocker)) {
            if ($runtime.challenge.verified -ne $true -or $pitr.challenge.verified -ne $true) { $blocker = "RELEASE_CHALLENGE_NOT_VERIFIED" }
            elseif ($runtime.challenge.trust_verified -ne $true -or $pitr.challenge.trust_verified -ne $true) { $blocker = "RELEASE_CHALLENGE_TRUST_NOT_VERIFIED" }
            elseif ($runtimeStatus -ne "PASS") { $blocker = "RUNTIME_GROUP_$runtimeStatus" }
            elseif ($pitrStatus -ne "PASS") { $blocker = "PITR_GROUP_$pitrStatus" }
            elseif (-not $workflowPassed) { $blocker = "WORKFLOW_FAILED" }
            else { $blocker = "PITR_ACCEPTANCE_NOT_ALL_PASS" }
        }
        Write-PhaseResult -Passed $false -RunId $runId -Detail "Exact-SHA runtime + PITR acceptance did not PASS." -Blocker $blocker
        Write-Host "PHASE242_PITR_ACCEPTANCE=FAIL"
        Write-Host "Candidate SHA: $CandidateRef"
        Write-Host "Workflow run id: $runId"
        Write-Host "Blocker: $blocker"
        throw "Phase 242 PITR Acceptance failed closed: $blocker"
    }

    Write-PhaseResult -Passed $true -RunId $runId -Detail "Exact-SHA trusted runtime prerequisite and PITR acceptance verified on the bound Windows target identity." -Blocker ""
    Write-Host "PHASE242_PITR_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "Runtime group: $runtimeStatus"
    Write-Host "PITR group: $pitrStatus"
    Write-Host "No production-ready/LIVE claim is made by this phase."
}
catch {
    $message = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = $message }
    try {
        $existing = Join-Path ([System.IO.Path]::GetFullPath($OutputDirectory)) "PHASE242_ORCHESTRATION_RESULT.json"
        if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) {
            Write-PhaseResult -Passed $false -RunId $runId -Detail $message -Blocker $blocker
        }
    }
    catch {
        Write-Warning "Could not write Phase 242 result JSON: $($_.Exception.Message)"
    }
    if ($message -notlike "Phase 242 PITR Acceptance failed closed:*") {
        Write-Host "PHASE242_PITR_ACCEPTANCE=FAIL"
    }
    throw
}
