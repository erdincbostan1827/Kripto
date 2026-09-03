[CmdletBinding()]
param(
    [string]$CandidateRef,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase250-final",
    [int]$DiscoveryTimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RequiredProfiles = @(
    "locks", "runtime", "restart-drills", "supply-chain", "pitr",
    "ha", "worm", "testnet", "provenance", "campaigns"
)

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

function Get-PropertyValue {
    param(
        [Parameter(Mandatory = $false)]$Object,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-RunCreatedAt {
    param([Parameter(Mandatory = $false)]$Run)
    $value = [string](Get-PropertyValue -Object $Run -Name "createdAt")
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    try { return [DateTimeOffset]$value } catch { return $null }
}

function Resolve-RemoteMainSha {
    $lines = Invoke-Gh -Arguments @("api", "repos/$Repository/commits/main", "--jq", ".sha")
    $sha = ([string]($lines | Select-Object -First 1)).Trim().ToLowerInvariant()
    if ($sha -notmatch '^[0-9a-f]{40}$') {
        throw "Could not resolve remote main to an exact 40-character SHA. Got: '$sha'"
    }
    return $sha
}

function Find-RequiredFile {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $matches = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $Name)
    if ($matches.Count -ne 1) {
        throw "Expected exactly one '$Name' in downloaded evidence; found $($matches.Count)."
    }
    return $matches[0].FullName
}

function Write-PhaseResult {
    param(
        [Parameter(Mandatory = $true)][bool]$Passed,
        [string]$RunId,
        [string]$WorkflowConclusion,
        [string]$Blocker,
        [bool]$ProductionReady,
        [bool]$EligibleForHumanApproval,
        [string]$EvidenceDirectory
    )

    $root = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    $suffix = if ([string]::IsNullOrWhiteSpace($RunId)) {
        [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
    } else {
        $RunId
    }
    $resultPath = Join-Path $root "PHASE250_FINAL_ORCHESTRATION_RESULT-$suffix.json"
    if (Test-Path -LiteralPath $resultPath) {
        throw "Refusing to overwrite existing Phase 250 result: $resultPath"
    }

    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE250_FINAL_PRODUCTION_ACCEPTANCE_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Production Acceptance"
        run_id = $RunId
        workflow_conclusion = $WorkflowConclusion
        production_ready = $ProductionReady
        eligible_for_human_approval = $EligibleForHumanApproval
        live_enabled = $false
        default_mode = "PAPER"
        evidence_directory = $EvidenceDirectory
        blocker = $Blocker
        truth_policy = "PASS means the exact current main candidate passed the automated real-target production acceptance and final release gate and is eligible for separate human LIVE approval. PASS never enables LIVE automatically."
    }
    $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runId = ""
$workflowConclusion = ""
$blocker = ""
$runOutput = ""
$productionReady = $false
$eligibleForHumanApproval = $false

try {
    Require-Command -Name "gh"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    $remoteMain = Resolve-RemoteMainSha
    if ([string]::IsNullOrWhiteSpace($CandidateRef)) {
        $CandidateRef = $remoteMain
    }
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') {
        throw "CandidateRef must be an exact 40-character commit SHA. Got: '$CandidateRef'"
    }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    if ($CandidateRef -ne $remoteMain) {
        throw "FINAL_ACCEPTANCE_REQUIRES_CURRENT_REMOTE_MAIN: candidate=$CandidateRef remote_main=$remoteMain"
    }

    $expectedTitle = "Production Acceptance $CandidateRef"
    $dispatchStarted = [DateTimeOffset]::UtcNow

    Invoke-Gh -Arguments @(
        "workflow", "run", "production-acceptance.yml",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "acceptance_ref=$CandidateRef"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds([Math]::Max(10, $DiscoveryTimeoutSeconds))
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list", "--repo", $Repository,
            "--workflow", "production-acceptance.yml",
            "--event", "workflow_dispatch", "--limit", "30",
            "--json", "databaseId,createdAt,status,conclusion,displayTitle,headSha,url"
        )) -join "`n"
        $parsed = $json | ConvertFrom-Json
        $runs = if ($null -eq $parsed) { @() } elseif ($parsed -is [Array]) { @($parsed) } else { @($parsed) }
        $candidates = @($runs | Where-Object {
            $createdAt = Get-RunCreatedAt -Run $_
            $title = [string](Get-PropertyValue -Object $_ -Name "displayTitle")
            $headSha = ([string](Get-PropertyValue -Object $_ -Name "headSha")).ToLowerInvariant()
            ($null -ne $createdAt) -and
            ($createdAt -ge $dispatchStarted.AddSeconds(-10)) -and
            ($title -eq $expectedTitle) -and
            ($headSha -eq $CandidateRef)
        } | Sort-Object { Get-RunCreatedAt -Run $_ } -Descending)

        if ($candidates.Count -gt 0) {
            $runId = [string](Get-PropertyValue -Object $candidates[0] -Name "databaseId")
            if ([string]::IsNullOrWhiteSpace($runId)) {
                throw "Discovered Production Acceptance run does not expose databaseId."
            }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)

    if ([string]::IsNullOrWhiteSpace($runId)) {
        throw "Could not discover Production Acceptance run for exact candidate '$CandidateRef'."
    }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $viewJson = (Invoke-Gh -Arguments @(
        "run", "view", $runId, "--repo", $Repository,
        "--json", "databaseId,displayTitle,headSha,status,conclusion,url"
    )) -join "`n"
    $runView = $viewJson | ConvertFrom-Json
    $runTitle = [string](Get-PropertyValue -Object $runView -Name "displayTitle")
    $runHead = ([string](Get-PropertyValue -Object $runView -Name "headSha")).ToLowerInvariant()
    $runStatus = [string](Get-PropertyValue -Object $runView -Name "status")
    $workflowConclusion = [string](Get-PropertyValue -Object $runView -Name "conclusion")
    if ($runTitle -ne $expectedTitle -or $runHead -ne $CandidateRef) {
        throw "WORKFLOW_IDENTITY_MISMATCH: title='$runTitle' head='$runHead'"
    }
    if ($runStatus -ne "completed") {
        throw "WORKFLOW_NOT_COMPLETED: status=$runStatus"
    }

    $rootOutput = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $rootOutput | Out-Null
    $runOutput = Join-Path $rootOutput "run-$runId"
    if (Test-Path -LiteralPath $runOutput) {
        throw "Refusing to overwrite existing Phase 250 evidence directory: $runOutput"
    }
    New-Item -ItemType Directory -Path $runOutput | Out-Null

    $artifactName = "real-target-evidence-$CandidateRef"
    Invoke-Gh -Arguments @(
        "run", "download", $runId,
        "--repo", $Repository,
        "--name", $artifactName,
        "--dir", $runOutput
    ) | Out-Null

    $preflightPath = Find-RequiredFile -Root $runOutput -Name "PRODUCTION_ACCEPTANCE_PREFLIGHT.json"
    $orchestrationPath = Find-RequiredFile -Root $runOutput -Name "PRODUCTION_ACCEPTANCE_ORCHESTRATION.json"
    $releaseGatePath = Find-RequiredFile -Root $runOutput -Name "CI_RELEASE_GATE.txt"
    $releaseManifestPath = Find-RequiredFile -Root $runOutput -Name "RELEASE_MANIFEST.json"
    $artifactIdentityPath = Find-RequiredFile -Root $runOutput -Name "CI_BUILD_ARTIFACT_IDENTITY.json"

    $preflight = Get-Content -LiteralPath $preflightPath -Raw | ConvertFrom-Json
    $orchestration = Get-Content -LiteralPath $orchestrationPath -Raw | ConvertFrom-Json
    $releaseManifest = Get-Content -LiteralPath $releaseManifestPath -Raw | ConvertFrom-Json
    $artifactIdentity = Get-Content -LiteralPath $artifactIdentityPath -Raw | ConvertFrom-Json
    $releaseGateText = Get-Content -LiteralPath $releaseGatePath -Raw

    if ($preflight.classification -ne "PRODUCTION_ACCEPTANCE_REAL_TARGET_PREFLIGHT") { throw "Unexpected production acceptance preflight classification." }
    if ($preflight.verified -ne $true) { throw "Production acceptance real-target preflight is not verified." }
    if (([string]$preflight.git_commit_sha).ToLowerInvariant() -ne $CandidateRef) { throw "Preflight git SHA mismatch." }
    if (([string]$preflight.acceptance_expected_git_sha).ToLowerInvariant() -ne $CandidateRef) { throw "Preflight expected SHA mismatch." }

    if ($artifactIdentity.classification -ne "GITHUB_ACTIONS_BUILD_ARTIFACT_IDENTITY_BINDING") { throw "Unexpected CI build artifact identity classification." }
    if ($artifactIdentity.verified -ne $true) { throw "CI build artifact identity is not verified." }
    if (([string]$artifactIdentity.git_commit_sha).ToLowerInvariant() -ne $CandidateRef) { throw "CI build artifact identity git SHA mismatch." }

    if ($orchestration.classification -ne "PRODUCTION_ACCEPTANCE_ORCHESTRATION_RESULT") { throw "Unexpected production acceptance orchestration classification." }
    if ($orchestration.executed -ne $true -or $orchestration.real_target_explicitly_confirmed -ne $true) { throw "Production acceptance was not executed against an explicitly confirmed real target." }
    if ($orchestration.production_ready -ne $true) { throw "Production acceptance orchestration did not reach production_ready=true." }
    if (([string]$orchestration.challenge.git_commit_sha).ToLowerInvariant() -ne $CandidateRef) { throw "Release challenge git SHA mismatch." }
    if ($orchestration.challenge_verification.verified -ne $true -or $orchestration.challenge_verification.trust_verified -ne $true) { throw "Release challenge external trust is not verified." }
    if ($orchestration.merge.selected_all_pass -ne $true) { throw "Merged external acceptance is not all PASS." }
    if ($orchestration.verification.verified -ne $true -or $orchestration.verification.selected_all_pass -ne $true) { throw "Merged external acceptance verification is not all PASS." }
    if ([int]$orchestration.release_manifest.exit_code -ne 0 -or [int]$orchestration.release_gate.exit_code -ne 0) { throw "Release manifest or release gate command failed inside orchestration." }
    if ([int]$orchestration.ledger_checkpoint.exit_code -ne 0) { throw "Final production acceptance ledger checkpoint signing/verification did not PASS." }

    foreach ($profile in $RequiredProfiles) {
        $profileProperty = $orchestration.profiles.PSObject.Properties[$profile]
        if ($null -eq $profileProperty) { throw "Required production acceptance profile is missing: $profile" }
        if ($profileProperty.Value.selected_all_pass -ne $true) { throw "Required production acceptance profile is not all PASS: $profile" }
    }

    if ($releaseGateText -notmatch 'PROD_LIVE_RELEASE=ELIGIBLE_FOR_HUMAN_APPROVAL') {
        throw "Final release gate did not report eligibility for human approval."
    }
    if ($releaseManifest.live_enabled -ne $false) { throw "RELEASE_MANIFEST live_enabled must remain false." }
    if ([string]$releaseManifest.default_mode -ne "PAPER") { throw "RELEASE_MANIFEST default_mode must remain PAPER." }
    if ([string]$releaseManifest.prod_live_status -notin @("ELIGIBLE_FOR_HUMAN_APPROVAL", "APPROVED")) {
        throw "RELEASE_MANIFEST prod_live_status is not eligible/approved."
    }

    $remoteMainAfter = Resolve-RemoteMainSha
    if ($remoteMainAfter -ne $CandidateRef) {
        throw "REMOTE_MAIN_MOVED_DURING_ACCEPTANCE: candidate=$CandidateRef remote_main_after=$remoteMainAfter"
    }

    $productionReady = $true
    $eligibleForHumanApproval = $true
    if (-not $workflowPassed -or $workflowConclusion -ne "success") {
        throw "Workflow did not conclude success despite downloaded evidence. conclusion=$workflowConclusion"
    }

    Write-PhaseResult -Passed $true -RunId $runId -WorkflowConclusion $workflowConclusion -Blocker "" -ProductionReady $true -EligibleForHumanApproval $true -EvidenceDirectory $runOutput
    Write-Host "PHASE250_FINAL_PRODUCTION_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "LIVE remains disabled. Separate human approval is required before any LIVE enablement."
}
catch {
    $message = $_.Exception.Message
    $blocker = $message
    try {
        Write-PhaseResult -Passed $false -RunId $runId -WorkflowConclusion $workflowConclusion -Blocker $blocker -ProductionReady $productionReady -EligibleForHumanApproval $eligibleForHumanApproval -EvidenceDirectory $runOutput
    } catch {
        Write-Warning "Could not write Phase 250 fail-closed result JSON: $($_.Exception.Message)"
    }
    Write-Host "PHASE250_FINAL_PRODUCTION_ACCEPTANCE=FAIL"
    throw
}
