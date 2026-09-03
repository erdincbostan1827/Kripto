[CmdletBinding()]
param(
    [string]$CandidateRef,
    [Parameter(Mandatory = $true)][string]$ReturnBundlePath,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase248-ledger",
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
    if ($LASTEXITCODE -ne 0) { throw "gh command failed: gh $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)" }
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
        [string]$Blocker,
        [string]$BundleSha256
    )
    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE248_LEDGER_CHECKPOINT_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Phase 248 Ledger Checkpoint Acceptance"
        run_id = $RunId
        return_bundle_sha256 = $BundleSha256
        detail = $Detail
        blocker = $Blocker
        production_ready = $false
        live_enabled = $false
        truth_policy = "Phase 248 PASS closes only the signed evidence-ledger checkpoint for the exact candidate and return bundle. Final merged acceptance and LIVE authorization remain separate gates."
    }
    $resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $resultPath = Join-Path $resolvedOutput "PHASE248_ORCHESTRATION_RESULT.json"
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runId = ""
$blocker = ""
$bundleSha = ""
try {
    Require-Command -Name "gh"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    $bundleFullPath = [IO.Path]::GetFullPath($ReturnBundlePath)
    if (-not (Test-Path -LiteralPath $bundleFullPath -PathType Leaf)) { throw "Return bundle is not a file: $bundleFullPath" }
    $bundleSha = (Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleSha -notmatch '^[0-9a-f]{64}$') { throw "Could not derive a valid return bundle SHA-256." }

    if ([string]::IsNullOrWhiteSpace($CandidateRef)) {
        $resolved = Invoke-Gh -Arguments @("api", "repos/$Repository/commits/main", "--jq", ".sha")
        $CandidateRef = ([string]($resolved | Select-Object -First 1)).Trim()
    }
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') { throw "CandidateRef must resolve to an exact 40-character commit SHA. Got: '$CandidateRef'" }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    $expectedRunTitle = "Phase 248 Ledger Checkpoint Acceptance $CandidateRef"

    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "Phase 248 Ledger Checkpoint Acceptance",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "candidate_ref=$CandidateRef",
        "-f", "return_bundle_path=$bundleFullPath",
        "-f", "return_bundle_sha256=$bundleSha"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list", "--repo", $Repository,
            "--workflow", "Phase 248 Ledger Checkpoint Acceptance",
            "--event", "workflow_dispatch", "--limit", "20",
            "--json", "databaseId,createdAt,status,conclusion,displayTitle"
        )) -join "`n"
        $parsedRuns = $json | ConvertFrom-Json
        $runs = @()
        if ($null -ne $parsedRuns) {
            if ($parsedRuns -is [Array]) { $runs = @($parsedRuns | ForEach-Object { $_ }) } else { $runs = @($parsedRuns) }
        }
        $candidateRuns = @($runs | Where-Object {
            $createdAt = Get-RunCreatedAt -Run $_
            $displayTitle = [string](Get-RunProperty -Run $_ -Name "displayTitle")
            ($null -ne $createdAt) -and ($createdAt -ge $dispatchStarted.AddSeconds(-10)) -and ($displayTitle -eq $expectedRunTitle)
        } | Sort-Object { Get-RunCreatedAt -Run $_ } -Descending)
        if ($candidateRuns.Count -gt 0) {
            $runId = [string](Get-RunProperty -Run $candidateRuns[0] -Name "databaseId")
            if ([string]::IsNullOrWhiteSpace($runId)) { throw "Discovered Phase 248 run does not expose databaseId." }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    if ([string]::IsNullOrWhiteSpace($runId)) { throw "Could not discover Phase 248 run for exact candidate '$CandidateRef'." }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $bundleShaAfter = (Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleShaAfter -ne $bundleSha) { throw "Return bundle changed during Phase 248 execution." }

    $resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $resolvedOutput) { Remove-Item -LiteralPath $resolvedOutput -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $artifactName = "phase248-ledger-checkpoint-$CandidateRef"
    Invoke-Gh -Arguments @("run", "download", $runId, "--repo", $Repository, "--name", $artifactName, "--dir", $resolvedOutput) | Out-Null

    $workflowResultPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PHASE248_LEDGER_RESULT.json" | Select-Object -First 1 -ExpandProperty FullName
    $identityPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "LEDGER_TARGET_IDENTITY.json" | Select-Object -First 1 -ExpandProperty FullName
    $transportPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "RETURN_BUNDLE_IDENTITY.json" | Select-Object -First 1 -ExpandProperty FullName
    $promotionPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "RETURN_PROMOTION_RESULT.json" | Select-Object -First 1 -ExpandProperty FullName
    $verificationPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "LEDGER_CHECKPOINT_VERIFICATION.json" | Select-Object -First 1 -ExpandProperty FullName
    $checkpointPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "evidence_ledger_checkpoint.json" | Select-Object -First 1 -ExpandProperty FullName
    $ledgerPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "evidence_ledger.json" | Select-Object -First 1 -ExpandProperty FullName
    $signatureCopyPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "LEDGER_CHECKPOINT_SIGNATURE.bin" | Select-Object -First 1 -ExpandProperty FullName
    foreach ($path in @($workflowResultPath,$identityPath,$transportPath,$promotionPath,$verificationPath,$checkpointPath,$ledgerPath,$signatureCopyPath)) {
        if ([string]::IsNullOrWhiteSpace([string]$path)) { throw "Phase 248 artifact is incomplete." }
    }

    $workflowResult = Get-Content -LiteralPath $workflowResultPath -Raw | ConvertFrom-Json
    $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    $transport = Get-Content -LiteralPath $transportPath -Raw | ConvertFrom-Json
    $promotion = Get-Content -LiteralPath $promotionPath -Raw | ConvertFrom-Json
    $verification = Get-Content -LiteralPath $verificationPath -Raw | ConvertFrom-Json
    $checkpoint = Get-Content -LiteralPath $checkpointPath -Raw | ConvertFrom-Json

    if ($workflowResult.classification -ne "PHASE248_LEDGER_CHECKPOINT_WORKFLOW_RESULT") { throw "Unexpected Phase 248 workflow result classification." }
    if ($identity.classification -ne "PHASE248_LEDGER_TARGET_IDENTITY_NOT_ACCEPTANCE_EVIDENCE") { throw "Unexpected Phase 248 target identity classification." }
    if ($transport.classification -ne "PHASE248_RETURN_BUNDLE_IDENTITY_NOT_ACCEPTANCE_EVIDENCE") { throw "Unexpected Phase 248 return bundle identity classification." }
    if ($workflowResult.candidate_sha -ne $CandidateRef -or $identity.candidate_sha -ne $CandidateRef -or $transport.candidate_sha -ne $CandidateRef -or $checkpoint.git_commit_sha -ne $CandidateRef) { throw "Phase 248 evidence is bound to a different candidate SHA." }
    if ($identity.runner_os -ne "Windows") { throw "Phase 248 did not run on Windows: $($identity.runner_os)" }
    if ([string]$workflowResult.return_bundle_sha256 -ne $bundleSha -or [string]$identity.return_bundle_sha256 -ne $bundleSha -or [string]$transport.bundle_sha256 -ne $bundleSha) { throw "Phase 248 return bundle SHA-256 binding mismatch." }
    if ($identity.production_ready -ne $false -or $identity.live_enabled -ne $false -or $workflowResult.production_ready -ne $false -or $workflowResult.live_enabled -ne $false) { throw "Phase 248 must remain non-LIVE/non-production-ready." }
    if ($promotion.verified -ne $true -or $promotion.promoted -ne $true -or $promotion.rolled_back -eq $true) { throw "Returned evidence promotion was not atomically committed." }
    if ($checkpoint.real_system -ne $true -or $checkpoint.executed -ne $true -or $checkpoint.signature_verified -ne $true) { throw "Ledger checkpoint is not real executed signature-verified evidence." }
    if ($checkpoint.environment.acceptance_environment_id_hash -ne $identity.acceptance_environment_id_hash -or $checkpoint.environment.topology_hash -ne $identity.topology_hash) { throw "Ledger checkpoint target identity mismatch." }
    if ($verification.verified -ne $true -or $verification.trust_verified -ne $true) { throw "Ledger checkpoint external trust is not verified." }
    if ($verification.ledger_head_hash -ne $checkpoint.ledger_head_hash -or [int64]$verification.ledger_entries -ne [int64]$checkpoint.ledger_entries) { throw "Ledger checkpoint head/count binding mismatch." }
    $signatureCopyHash = (Get-FileHash -LiteralPath $signatureCopyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($signatureCopyHash -ne ([string]$checkpoint.signature_sha256).ToLowerInvariant()) { throw "Downloaded checkpoint signature hash mismatch." }

    $passed = ($workflowPassed -and $workflowResult.passed -eq $true)
    if (-not $passed) {
        $blocker = [string]$workflowResult.blocker
        if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = "LEDGER_CHECKPOINT_ACCEPTANCE_NOT_ALL_PASS" }
        Write-PhaseResult -Passed $false -RunId $runId -Detail "Exact-SHA ledger checkpoint acceptance did not PASS." -Blocker $blocker -BundleSha256 $bundleSha
        Write-Host "PHASE248_LEDGER_CHECKPOINT_ACCEPTANCE=FAIL"
        throw "Phase 248 Ledger Checkpoint Acceptance failed closed: $blocker"
    }

    Write-PhaseResult -Passed $true -RunId $runId -Detail "Exact-SHA returned external evidence was semantically promoted and its evidence ledger was externally signed and verified." -Blocker "" -BundleSha256 $bundleSha
    Write-Host "PHASE248_LEDGER_CHECKPOINT_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "No production-ready/LIVE claim is made by this phase."
}
catch {
    $message = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = $message }
    try {
        $existing = Join-Path ([IO.Path]::GetFullPath($OutputDirectory)) "PHASE248_ORCHESTRATION_RESULT.json"
        if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) {
            Write-PhaseResult -Passed $false -RunId $runId -Detail $message -Blocker $blocker -BundleSha256 $bundleSha
        }
    } catch { Write-Warning "Could not write Phase 248 result JSON: $($_.Exception.Message)" }
    if ($message -notlike "Phase 248 Ledger Checkpoint Acceptance failed closed:*") { Write-Host "PHASE248_LEDGER_CHECKPOINT_ACCEPTANCE=FAIL" }
    throw
}
