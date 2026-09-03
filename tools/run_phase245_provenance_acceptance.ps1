[CmdletBinding()]
param(
    [string]$CandidateRef,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase245-provenance",
    [int]$DiscoveryTimeoutSeconds = 90
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "Required command is unavailable: $Name" }
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
    param([Parameter(Mandatory = $false)]$Run, [Parameter(Mandatory = $true)][string]$Name)
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
        classification = "PHASE245_PROVENANCE_ACCEPTANCE_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Phase 245 Provenance Acceptance"
        run_id = $RunId
        detail = $Detail
        blocker = $Blocker
        production_ready = $false
        truth_policy = "Phase 245 PASS closes only exact-SHA transferred hosted provenance plus strict external provenance/signature verification. It does not close ledger checkpoint, TESTNET/campaign gates or authorize LIVE trading."
    }
    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $resultPath = Join-Path $resolvedOutput "PHASE245_ORCHESTRATION_RESULT.json"
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
    $expectedRunTitle = "Phase 245 Provenance Acceptance $CandidateRef"

    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "Phase 245 Provenance Acceptance",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "candidate_ref=$CandidateRef"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list",
            "--repo", $Repository,
            "--workflow", "Phase 245 Provenance Acceptance",
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
            if ([string]::IsNullOrWhiteSpace($runId)) { throw "Discovered Phase 245 run does not expose databaseId." }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)

    if ([string]::IsNullOrWhiteSpace($runId)) {
        throw "Could not discover the dispatched Phase 245 Provenance Acceptance run for exact candidate '$CandidateRef'."
    }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $resolvedOutput) { Remove-Item -LiteralPath $resolvedOutput -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null

    $artifactName = "phase245-provenance-acceptance-$CandidateRef"
    Invoke-Gh -Arguments @(
        "run", "download", $runId,
        "--repo", $Repository,
        "--name", $artifactName,
        "--dir", $resolvedOutput
    ) | Out-Null

    $workflowResultPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PHASE245_PROVENANCE_RESULT.json" | Select-Object -First 1 -ExpandProperty FullName
    $identityPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PROVENANCE_TARGET_IDENTITY.json" | Select-Object -First 1 -ExpandProperty FullName
    $transferPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PHASE225_TRANSFER_VERIFICATION.json" | Select-Object -First 1 -ExpandProperty FullName
    $manifestPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "manifest_provenance.json" | Select-Object -First 1 -ExpandProperty FullName

    if (-not $workflowResultPath) { throw "Phase 245 artifact did not contain PHASE245_PROVENANCE_RESULT.json." }
    if (-not $identityPath) { throw "Phase 245 artifact did not contain PROVENANCE_TARGET_IDENTITY.json." }
    if (-not $transferPath) { throw "Phase 245 artifact did not contain PHASE225_TRANSFER_VERIFICATION.json." }
    if (-not $manifestPath) { throw "Phase 245 artifact did not contain manifest_provenance.json." }

    $workflowResult = Get-Content -LiteralPath $workflowResultPath -Raw | ConvertFrom-Json
    $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    $transfer = Get-Content -LiteralPath $transferPath -Raw | ConvertFrom-Json
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

    if ($workflowResult.classification -ne "PHASE245_PROVENANCE_ACCEPTANCE_WORKFLOW_RESULT") {
        throw "Unexpected Phase 245 workflow result classification: $($workflowResult.classification)"
    }
    if ($identity.classification -ne "PHASE245_PROVENANCE_TARGET_IDENTITY_NOT_ACCEPTANCE_EVIDENCE") {
        throw "Unexpected Phase 245 target identity classification: $($identity.classification)"
    }
    if ($transfer.classification -ne "PHASE225_TRANSFER_VERIFICATION") {
        throw "Unexpected Phase 225 transfer classification: $($transfer.classification)"
    }
    if ($identity.candidate_sha -ne $CandidateRef -or $workflowResult.candidate_sha -ne $CandidateRef) {
        throw "Phase 245 result/identity is bound to a different git SHA."
    }
    if ($identity.runner_os -ne "Windows") { throw "Phase 245 target identity did not run on Windows: $($identity.runner_os)" }
    if ($transfer.verified -ne $true -or $transfer.expected_git_commit_sha -ne $CandidateRef -or $transfer.checked_out_git_commit_sha -ne $CandidateRef) {
        throw "Transferred Phase 225 provenance was not verified for the exact candidate."
    }
    if ([string]::IsNullOrWhiteSpace([string]$identity.phase225_run_id) -or [string]$workflowResult.phase225_run_id -ne [string]$identity.phase225_run_id) {
        throw "Phase 245 result is not bound to the same Phase 225 source run as the target identity."
    }
    if ($identity.acceptance_image_digest -ne $transfer.acceptance_image_digest) {
        throw "Phase 245 immutable image digest does not match the verified Phase 225 transfer."
    }
    if ($manifest.classification -ne "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE") { throw "Unexpected external acceptance classification: $($manifest.classification)" }
    if ($manifest.profile -ne "provenance") { throw "Unexpected provenance profile: $($manifest.profile)" }
    if ($manifest.environment.git_commit_sha -ne $CandidateRef) { throw "Provenance evidence is bound to a different git SHA: $($manifest.environment.git_commit_sha)" }
    if ($manifest.environment.topology_hash -ne $identity.topology_hash) { throw "Provenance evidence topology hash does not match Phase 245 target identity." }

    if ($null -ne $workflowResult.PSObject.Properties["blocker"]) { $blocker = [string]$workflowResult.blocker }
    if ([string]::IsNullOrWhiteSpace($blocker) -and $null -ne $manifest.PSObject.Properties["blocker"]) { $blocker = [string]$manifest.blocker }

    $provenanceStatus = [string]$manifest.groups.provenance
    $passed = (
        $workflowPassed -and
        $workflowResult.passed -eq $true -and
        $workflowResult.phase225_transfer_verified -eq $true -and
        $manifest.real_target_explicitly_confirmed -eq $true -and
        $manifest.challenge.verified -eq $true -and
        $manifest.challenge.trust_verified -eq $true -and
        $manifest.selected_all_pass -eq $true -and
        $provenanceStatus -eq "PASS"
    )

    if (-not $passed) {
        if ([string]::IsNullOrWhiteSpace($blocker)) {
            if ($transfer.verified -ne $true) { $blocker = "PHASE225_TRANSFER_NOT_VERIFIED" }
            elseif ($manifest.challenge.verified -ne $true) { $blocker = "RELEASE_CHALLENGE_NOT_VERIFIED" }
            elseif ($manifest.challenge.trust_verified -ne $true) { $blocker = "RELEASE_CHALLENGE_TRUST_NOT_VERIFIED" }
            elseif ($provenanceStatus -ne "PASS") { $blocker = "PROVENANCE_GROUP_$provenanceStatus" }
            elseif (-not $workflowPassed) { $blocker = "WORKFLOW_FAILED" }
            else { $blocker = "PROVENANCE_ACCEPTANCE_NOT_ALL_PASS" }
        }
        Write-PhaseResult -Passed $false -RunId $runId -Detail "Exact-SHA provenance/signature acceptance did not PASS." -Blocker $blocker
        Write-Host "PHASE245_PROVENANCE_ACCEPTANCE=FAIL"
        Write-Host "Candidate SHA: $CandidateRef"
        Write-Host "Workflow run id: $runId"
        Write-Host "Blocker: $blocker"
        throw "Phase 245 Provenance Acceptance failed closed: $blocker"
    }

    Write-PhaseResult -Passed $true -RunId $runId -Detail "Exact-SHA transferred hosted provenance and strict external provenance/signature verification passed on the bound Windows target identity." -Blocker ""
    Write-Host "PHASE245_PROVENANCE_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "Phase 225 source run id: $($identity.phase225_run_id)"
    Write-Host "Provenance group: $provenanceStatus"
    Write-Host "No production-ready/LIVE claim is made by this phase."
}
catch {
    $message = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = $message }
    try {
        $existing = Join-Path ([System.IO.Path]::GetFullPath($OutputDirectory)) "PHASE245_ORCHESTRATION_RESULT.json"
        if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) {
            Write-PhaseResult -Passed $false -RunId $runId -Detail $message -Blocker $blocker
        }
    }
    catch { Write-Warning "Could not write Phase 245 result JSON: $($_.Exception.Message)" }
    if ($message -notlike "Phase 245 Provenance Acceptance failed closed:*") { Write-Host "PHASE245_PROVENANCE_ACCEPTANCE=FAIL" }
    throw
}
