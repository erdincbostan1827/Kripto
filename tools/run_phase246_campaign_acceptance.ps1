[CmdletBinding()]
param(
    [string]$CandidateRef,
    [Parameter(Mandatory = $true)][string]$EvidenceBundlePath,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase246-campaign",
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
    param([Parameter(Mandatory = $true)][bool]$Passed, [string]$RunId, [string]$Detail, [string]$Blocker, [string]$BundleSha256)
    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE246_CAMPAIGN_ACCEPTANCE_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Phase 246 Campaign Acceptance"
        run_id = $RunId
        campaign_bundle_sha256 = $BundleSha256
        detail = $Detail
        blocker = $Blocker
        live_enabled = $false
        production_ready = $false
        truth_policy = "Phase 246 PASS closes only exact-SHA release-bound private-stream/PAPER/live-shadow/profitability evidence. Live-shadow must prove zero real order submissions. This phase never authorizes LIVE trading."
    }
    $resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $resultPath = Join-Path $resolvedOutput "PHASE246_ORCHESTRATION_RESULT.json"
    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runId = ""
$blocker = ""
$bundleSha = ""
try {
    Require-Command -Name "gh"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    $bundleFullPath = [IO.Path]::GetFullPath($EvidenceBundlePath)
    if (-not (Test-Path -LiteralPath $bundleFullPath -PathType Leaf)) { throw "Evidence bundle is not a file: $bundleFullPath" }
    $bundleSha = (Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleSha -notmatch '^[0-9a-f]{64}$') { throw "Could not derive a valid bundle SHA-256." }

    if ([string]::IsNullOrWhiteSpace($CandidateRef)) {
        $resolved = Invoke-Gh -Arguments @("api", "repos/$Repository/commits/main", "--jq", ".sha")
        $CandidateRef = ([string]($resolved | Select-Object -First 1)).Trim()
    }
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') { throw "CandidateRef must resolve to an exact 40-character commit SHA. Got: '$CandidateRef'" }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    $expectedRunTitle = "Phase 246 Campaign Acceptance $CandidateRef"

    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "Phase 246 Campaign Acceptance",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "candidate_ref=$CandidateRef",
        "-f", "bundle_path=$bundleFullPath",
        "-f", "bundle_sha256=$bundleSha"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list", "--repo", $Repository,
            "--workflow", "Phase 246 Campaign Acceptance",
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
            if ([string]::IsNullOrWhiteSpace($runId)) { throw "Discovered Phase 246 run does not expose databaseId." }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    if ([string]::IsNullOrWhiteSpace($runId)) { throw "Could not discover the dispatched Phase 246 Campaign Acceptance run for exact candidate '$CandidateRef'." }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $bundleShaAfter = (Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleShaAfter -ne $bundleSha) { throw "Campaign evidence bundle changed during acceptance execution." }

    $resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $resolvedOutput) { Remove-Item -LiteralPath $resolvedOutput -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $artifactName = "phase246-campaign-acceptance-$CandidateRef"
    Invoke-Gh -Arguments @("run", "download", $runId, "--repo", $Repository, "--name", $artifactName, "--dir", $resolvedOutput) | Out-Null

    $workflowResultPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PHASE246_CAMPAIGN_RESULT.json" | Select-Object -First 1 -ExpandProperty FullName
    $identityPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "CAMPAIGN_TARGET_IDENTITY.json" | Select-Object -First 1 -ExpandProperty FullName
    $transferPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "CAMPAIGN_BUNDLE_TRANSFER_VERIFICATION.json" | Select-Object -First 1 -ExpandProperty FullName
    $manifestPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "manifest_campaigns.json" | Select-Object -First 1 -ExpandProperty FullName
    $privatePath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "private_stream.json" | Select-Object -First 1 -ExpandProperty FullName
    $paperPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "paper_campaign.json" | Select-Object -First 1 -ExpandProperty FullName
    $shadowPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "live_shadow.json" | Select-Object -First 1 -ExpandProperty FullName
    $profitPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "profitability.json" | Select-Object -First 1 -ExpandProperty FullName
    foreach ($path in @($workflowResultPath,$identityPath,$transferPath,$manifestPath,$privatePath,$paperPath,$shadowPath,$profitPath)) {
        if ([string]::IsNullOrWhiteSpace([string]$path)) { throw "Phase 246 artifact is incomplete." }
    }

    $workflowResult = Get-Content -LiteralPath $workflowResultPath -Raw | ConvertFrom-Json
    $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    $transfer = Get-Content -LiteralPath $transferPath -Raw | ConvertFrom-Json
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $private = Get-Content -LiteralPath $privatePath -Raw | ConvertFrom-Json
    $paper = Get-Content -LiteralPath $paperPath -Raw | ConvertFrom-Json
    $shadow = Get-Content -LiteralPath $shadowPath -Raw | ConvertFrom-Json
    $profit = Get-Content -LiteralPath $profitPath -Raw | ConvertFrom-Json

    if ($workflowResult.classification -ne "PHASE246_CAMPAIGN_ACCEPTANCE_WORKFLOW_RESULT") { throw "Unexpected Phase 246 workflow result classification." }
    if ($identity.classification -ne "PHASE246_CAMPAIGN_TARGET_IDENTITY_NOT_ACCEPTANCE_EVIDENCE") { throw "Unexpected Phase 246 target identity classification." }
    if ($transfer.classification -ne "PHASE246_CAMPAIGN_BUNDLE_TRANSFER_VERIFICATION" -or $transfer.verified -ne $true) { throw "Campaign bundle transfer was not verified." }
    if ($identity.candidate_sha -ne $CandidateRef -or $workflowResult.candidate_sha -ne $CandidateRef -or $transfer.candidate_sha -ne $CandidateRef) { throw "Phase 246 evidence is bound to a different candidate SHA." }
    if ($identity.runner_os -ne "Windows") { throw "Phase 246 validation did not run on Windows: $($identity.runner_os)" }
    if ([string]$identity.bundle_sha256 -ne $bundleSha -or [string]$transfer.bundle_sha256 -ne $bundleSha) { throw "Campaign bundle SHA-256 binding mismatch." }
    if ([string]$identity.campaign_environment_id_sha256 -ne [string]$transfer.acceptance_environment_id_sha256) { throw "Campaign environment identity binding mismatch." }
    if ([string]$identity.topology_hash -ne [string]$transfer.topology_hash) { throw "Campaign topology binding mismatch." }
    if ($identity.live_enabled -ne $false -or $identity.production_ready -ne $false) { throw "Phase 246 identity must remain non-LIVE/non-production-ready." }

    if ($manifest.classification -ne "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE" -or $manifest.profile -ne "campaigns") { throw "Unexpected external campaign acceptance manifest." }
    if ($manifest.environment.git_commit_sha -ne $CandidateRef) { throw "Campaign manifest is bound to a different git SHA." }
    if ($manifest.environment.acceptance_environment_id_hash -ne $transfer.acceptance_environment_id_sha256) { throw "Campaign manifest environment identity mismatch." }
    if ($manifest.environment.topology_hash -ne $transfer.topology_hash) { throw "Campaign manifest topology mismatch." }

    foreach ($receipt in @($private,$paper,$shadow,$profit)) {
        if ($receipt.git_commit_sha -ne $CandidateRef -or $receipt.real_system -ne $true -or $receipt.executed -ne $true) {
            throw "A campaign evidence receipt is not exact-SHA real/executed evidence."
        }
    }
    if ([int64]$shadow.metrics.real_orders_submitted -ne 0 -or [int64]$shadow.metrics.exchange_submit_calls -ne 0) {
        throw "Live-shadow evidence contains real order submissions."
    }

    if ($null -ne $workflowResult.PSObject.Properties["blocker"]) { $blocker = [string]$workflowResult.blocker }
    if ([string]::IsNullOrWhiteSpace($blocker) -and $null -ne $manifest.PSObject.Properties["blocker"]) { $blocker = [string]$manifest.blocker }
    $privateStatus = [string]$manifest.groups.private_stream
    $paperStatus = [string]$manifest.groups.paper_campaign
    $shadowStatus = [string]$manifest.groups.live_shadow
    $profitStatus = [string]$manifest.groups.profitability
    $passed = (
        $workflowPassed -and
        $workflowResult.passed -eq $true -and
        $workflowResult.live_enabled -eq $false -and
        $workflowResult.production_ready -eq $false -and
        $manifest.real_target_explicitly_confirmed -eq $true -and
        $manifest.challenge.verified -eq $true -and
        $manifest.challenge.trust_verified -eq $true -and
        $manifest.selected_all_pass -eq $true -and
        $privateStatus -eq "PASS" -and $paperStatus -eq "PASS" -and $shadowStatus -eq "PASS" -and $profitStatus -eq "PASS"
    )
    if (-not $passed) {
        if ([string]::IsNullOrWhiteSpace($blocker)) {
            if ($manifest.challenge.verified -ne $true) { $blocker = "RELEASE_CHALLENGE_NOT_VERIFIED" }
            elseif ($manifest.challenge.trust_verified -ne $true) { $blocker = "RELEASE_CHALLENGE_TRUST_NOT_VERIFIED" }
            elseif ($privateStatus -ne "PASS") { $blocker = "PRIVATE_STREAM_GROUP_$privateStatus" }
            elseif ($paperStatus -ne "PASS") { $blocker = "PAPER_CAMPAIGN_GROUP_$paperStatus" }
            elseif ($shadowStatus -ne "PASS") { $blocker = "LIVE_SHADOW_GROUP_$shadowStatus" }
            elseif ($profitStatus -ne "PASS") { $blocker = "PROFITABILITY_GROUP_$profitStatus" }
            elseif (-not $workflowPassed) { $blocker = "WORKFLOW_FAILED" }
            else { $blocker = "CAMPAIGN_ACCEPTANCE_NOT_ALL_PASS" }
        }
        Write-PhaseResult -Passed $false -RunId $runId -Detail "Exact-SHA campaign acceptance did not PASS." -Blocker $blocker -BundleSha256 $bundleSha
        Write-Host "PHASE246_CAMPAIGN_ACCEPTANCE=FAIL"
        Write-Host "Candidate SHA: $CandidateRef"
        Write-Host "Workflow run id: $runId"
        Write-Host "Blocker: $blocker"
        throw "Phase 246 Campaign Acceptance failed closed: $blocker"
    }

    Write-PhaseResult -Passed $true -RunId $runId -Detail "Exact-SHA release-bound private-stream, PAPER, live-shadow and profitability evidence passed canonical strict validation." -Blocker "" -BundleSha256 $bundleSha
    Write-Host "PHASE246_CAMPAIGN_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "Campaign groups: private-stream=$privateStatus paper=$paperStatus live-shadow=$shadowStatus profitability=$profitStatus"
    Write-Host "No production-ready/LIVE claim is made by this phase."
}
catch {
    $message = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = $message }
    try {
        $existing = Join-Path ([IO.Path]::GetFullPath($OutputDirectory)) "PHASE246_ORCHESTRATION_RESULT.json"
        if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) {
            Write-PhaseResult -Passed $false -RunId $runId -Detail $message -Blocker $blocker -BundleSha256 $bundleSha
        }
    } catch { Write-Warning "Could not write Phase 246 result JSON: $($_.Exception.Message)" }
    if ($message -notlike "Phase 246 Campaign Acceptance failed closed:*") { Write-Host "PHASE246_CAMPAIGN_ACCEPTANCE=FAIL" }
    throw
}
