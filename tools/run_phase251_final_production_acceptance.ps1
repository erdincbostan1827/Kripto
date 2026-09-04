[CmdletBinding()]
param(
    [string]$CandidateRef,
    [Parameter(Mandatory = $true)][string]$CampaignEvidenceBundlePath,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase251-final",
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
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) { throw "Required command is unavailable: $Name" }
}

function Invoke-Gh {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $output = & gh @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "gh command failed: gh $($Arguments -join ' ')`n$($output -join [Environment]::NewLine)" }
    return @($output)
}

function Get-PropertyValue {
    param([Parameter(Mandatory = $false)]$Object, [Parameter(Mandatory = $true)][string]$Name)
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
    if ($sha -notmatch '^[0-9a-f]{40}$') { throw "Could not resolve remote main to an exact SHA. Got: '$sha'" }
    return $sha
}

function Find-RequiredFile {
    param([Parameter(Mandatory = $true)][string]$Root, [Parameter(Mandatory = $true)][string]$Name)
    $matches = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $Name)
    if ($matches.Count -ne 1) { throw "Expected exactly one '$Name' in downloaded evidence; found $($matches.Count)." }
    return $matches[0].FullName
}

function Write-PhaseResult {
    param(
        [Parameter(Mandatory = $true)][bool]$Passed,
        [string]$RunId,
        [string]$WorkflowConclusion,
        [string]$Blocker,
        [string]$BundleSha256,
        [string]$EvidenceDirectory
    )
    $root = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $root | Out-Null
    $suffix = if ([string]::IsNullOrWhiteSpace($RunId)) { [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ") } else { $RunId }
    $resultPath = Join-Path $root "PHASE251_FINAL_ORCHESTRATION_RESULT-$suffix.json"
    if (Test-Path -LiteralPath $resultPath) { throw "Refusing to overwrite existing Phase 251 result: $resultPath" }
    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE251_FINAL_CAMPAIGN_BOUND_PRODUCTION_ACCEPTANCE_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        campaign_bundle_sha256 = $BundleSha256
        workflow = "Production Acceptance"
        run_id = $RunId
        workflow_conclusion = $WorkflowConclusion
        live_enabled = $false
        default_mode = "PAPER"
        eligible_for_human_approval = $Passed
        evidence_directory = $EvidenceDirectory
        blocker = $Blocker
        truth_policy = "PASS means the exact current main SHA and exact campaign bundle passed automated real-target production acceptance. LIVE remains disabled and separate human approval is still required."
    }
    $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runId = ""
$workflowConclusion = ""
$runOutput = ""
$bundleSha = ""

try {
    Require-Command -Name "gh"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    $bundleFullPath = [IO.Path]::GetFullPath($CampaignEvidenceBundlePath)
    if (-not (Test-Path -LiteralPath $bundleFullPath -PathType Leaf)) { throw "Campaign evidence bundle is not a file: $bundleFullPath" }
    $bundleSha = (Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleSha -notmatch '^[0-9a-f]{64}$') { throw "Could not derive campaign bundle SHA-256." }

    $remoteMain = Resolve-RemoteMainSha
    if ([string]::IsNullOrWhiteSpace($CandidateRef)) { $CandidateRef = $remoteMain }
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') { throw "CandidateRef must be an exact 40-character SHA. Got: '$CandidateRef'" }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    if ($CandidateRef -ne $remoteMain) { throw "FINAL_ACCEPTANCE_REQUIRES_CURRENT_REMOTE_MAIN: candidate=$CandidateRef remote_main=$remoteMain" }

    $expectedTitle = "Production Acceptance $CandidateRef"
    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "production-acceptance.yml",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "acceptance_ref=$CandidateRef",
        "-f", "campaign_bundle_path=$bundleFullPath",
        "-f", "campaign_bundle_sha256=$bundleSha"
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
        $matches = @($runs | Where-Object {
            $created = Get-RunCreatedAt -Run $_
            $title = [string](Get-PropertyValue -Object $_ -Name "displayTitle")
            $head = ([string](Get-PropertyValue -Object $_ -Name "headSha")).ToLowerInvariant()
            ($null -ne $created) -and ($created -ge $dispatchStarted.AddSeconds(-10)) -and ($title -eq $expectedTitle) -and ($head -eq $CandidateRef)
        } | Sort-Object { Get-RunCreatedAt -Run $_ } -Descending)
        if ($matches.Count -gt 0) {
            $runId = [string](Get-PropertyValue -Object $matches[0] -Name "databaseId")
            if ([string]::IsNullOrWhiteSpace($runId)) { throw "Discovered Production Acceptance run does not expose databaseId." }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    if ([string]::IsNullOrWhiteSpace($runId)) { throw "Could not discover exact-SHA Production Acceptance run." }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $bundleShaAfter = (Get-FileHash -LiteralPath $bundleFullPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleShaAfter -ne $bundleSha) { throw "Campaign evidence bundle changed during final acceptance." }

    $viewJson = (Invoke-Gh -Arguments @("run", "view", $runId, "--repo", $Repository, "--json", "databaseId,displayTitle,headSha,status,conclusion,url")) -join "`n"
    $runView = $viewJson | ConvertFrom-Json
    if ([string](Get-PropertyValue -Object $runView -Name "displayTitle") -ne $expectedTitle) { throw "WORKFLOW_TITLE_MISMATCH" }
    if (([string](Get-PropertyValue -Object $runView -Name "headSha")).ToLowerInvariant() -ne $CandidateRef) { throw "WORKFLOW_HEAD_SHA_MISMATCH" }
    if ([string](Get-PropertyValue -Object $runView -Name "status") -ne "completed") { throw "WORKFLOW_NOT_COMPLETED" }
    $workflowConclusion = [string](Get-PropertyValue -Object $runView -Name "conclusion")

    $rootOutput = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $rootOutput | Out-Null
    $runOutput = Join-Path $rootOutput "run-$runId"
    if (Test-Path -LiteralPath $runOutput) { throw "Refusing to overwrite existing Phase 251 evidence directory: $runOutput" }
    New-Item -ItemType Directory -Path $runOutput | Out-Null

    $artifactName = "real-target-evidence-$CandidateRef"
    Invoke-Gh -Arguments @("run", "download", $runId, "--repo", $Repository, "--name", $artifactName, "--dir", $runOutput) | Out-Null

    $handoffPath = Find-RequiredFile -Root $runOutput -Name "FINAL_CAMPAIGN_HANDOFF_VERIFICATION.json"
    $preflightPath = Find-RequiredFile -Root $runOutput -Name "PRODUCTION_ACCEPTANCE_PREFLIGHT.json"
    $orchestrationPath = Find-RequiredFile -Root $runOutput -Name "PRODUCTION_ACCEPTANCE_ORCHESTRATION.json"
    $releaseGatePath = Find-RequiredFile -Root $runOutput -Name "CI_RELEASE_GATE.txt"
    $releaseManifestPath = Find-RequiredFile -Root $runOutput -Name "RELEASE_MANIFEST.json"
    $artifactIdentityPath = Find-RequiredFile -Root $runOutput -Name "CI_BUILD_ARTIFACT_IDENTITY.json"

    $handoff = Get-Content -LiteralPath $handoffPath -Raw | ConvertFrom-Json
    $preflight = Get-Content -LiteralPath $preflightPath -Raw | ConvertFrom-Json
    $orchestration = Get-Content -LiteralPath $orchestrationPath -Raw | ConvertFrom-Json
    $releaseManifest = Get-Content -LiteralPath $releaseManifestPath -Raw | ConvertFrom-Json
    $artifactIdentity = Get-Content -LiteralPath $artifactIdentityPath -Raw | ConvertFrom-Json
    $releaseGateText = Get-Content -LiteralPath $releaseGatePath -Raw

    if ($handoff.classification -ne "PHASE251_FINAL_CAMPAIGN_HANDOFF_VERIFICATION" -or $handoff.verified -ne $true) { throw "Final campaign handoff is not verified." }
    if ([string]$handoff.candidate_sha -ne $CandidateRef -or [string]$handoff.bundle_sha256 -ne $bundleSha) { throw "Final campaign handoff identity mismatch." }
    if ($handoff.challenge.trust_verified -ne $true) { throw "Final campaign handoff challenge trust is not verified." }
    foreach ($name in @("private-stream", "paper", "live-shadow", "profitability")) {
        $property = $handoff.campaigns.PSObject.Properties[$name]
        if ($null -eq $property -or $property.Value.verified -ne $true) { throw "Final campaign handoff campaign is not verified: $name" }
    }

    if ($preflight.classification -ne "PRODUCTION_ACCEPTANCE_REAL_TARGET_PREFLIGHT" -or $preflight.verified -ne $true) { throw "Production acceptance preflight is not verified." }
    if (([string]$preflight.git_commit_sha).ToLowerInvariant() -ne $CandidateRef) { throw "Preflight git SHA mismatch." }
    if ($artifactIdentity.classification -ne "GITHUB_ACTIONS_BUILD_ARTIFACT_IDENTITY_BINDING" -or $artifactIdentity.verified -ne $true) { throw "CI artifact identity is not verified." }
    if (([string]$artifactIdentity.git_commit_sha).ToLowerInvariant() -ne $CandidateRef) { throw "CI artifact identity SHA mismatch." }

    if ($orchestration.classification -ne "PRODUCTION_ACCEPTANCE_ORCHESTRATION_RESULT") { throw "Unexpected orchestration classification." }
    if ($orchestration.executed -ne $true -or $orchestration.real_target_explicitly_confirmed -ne $true) { throw "Real-target orchestration was not executed." }
    if ($orchestration.reuse_current_challenge -ne $true -or $orchestration.challenge.reused -ne $true) { throw "Final orchestration did not reuse the verified campaign challenge." }
    if ($orchestration.challenge_verification.verified -ne $true -or $orchestration.challenge_verification.trust_verified -ne $true) { throw "Orchestration challenge trust is not verified." }
    if ($orchestration.production_ready -ne $true) { throw "Production acceptance did not reach production_ready=true." }
    if ($orchestration.merge.selected_all_pass -ne $true -or $orchestration.verification.verified -ne $true -or $orchestration.verification.selected_all_pass -ne $true) { throw "Merged acceptance is not all PASS." }

    foreach ($profile in $RequiredProfiles) {
        $property = $orchestration.profiles.PSObject.Properties[$profile]
        if ($null -eq $property -or $property.Value.selected_all_pass -ne $true) { throw "Required production acceptance profile is not all PASS: $profile" }
    }

    foreach ($name in @("release_manifest", "release_gate", "ledger_checkpoint")) {
        $section = Get-PropertyValue -Object $orchestration -Name $name
        $exitCode = Get-PropertyValue -Object $section -Name "exit_code"
        if ($null -eq $exitCode -or [int]$exitCode -ne 0) { throw "Missing successful orchestration exit code: $name" }
    }

    if ($releaseGateText -notmatch 'PROD_LIVE_RELEASE=ELIGIBLE_FOR_HUMAN_APPROVAL') { throw "Final release gate did not report human-approval eligibility." }
    if ($releaseManifest.live_enabled -ne $false -or [string]$releaseManifest.default_mode -ne "PAPER") { throw "Release manifest violated PAPER/LIVE safety boundary." }
    if ([string]$releaseManifest.prod_live_status -notin @("ELIGIBLE_FOR_HUMAN_APPROVAL", "APPROVED")) { throw "Release manifest is not eligible/approved." }

    $remoteMainAfter = Resolve-RemoteMainSha
    if ($remoteMainAfter -ne $CandidateRef) { throw "REMOTE_MAIN_MOVED_DURING_ACCEPTANCE: candidate=$CandidateRef remote_main_after=$remoteMainAfter" }
    if (-not $workflowPassed -or $workflowConclusion -ne "success") { throw "Workflow did not conclude success. conclusion=$workflowConclusion" }

    Write-PhaseResult -Passed $true -RunId $runId -WorkflowConclusion $workflowConclusion -Blocker "" -BundleSha256 $bundleSha -EvidenceDirectory $runOutput
    Write-Host "PHASE251_FINAL_PRODUCTION_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Campaign bundle SHA-256: $bundleSha"
    Write-Host "Workflow run id: $runId"
    Write-Host "LIVE remains disabled. Separate human approval is required before any LIVE enablement."
}
catch {
    $message = $_.Exception.Message
    try { Write-PhaseResult -Passed $false -RunId $runId -WorkflowConclusion $workflowConclusion -Blocker $message -BundleSha256 $bundleSha -EvidenceDirectory $runOutput } catch { Write-Warning "Could not write Phase 251 fail-closed result JSON: $($_.Exception.Message)" }
    Write-Host "PHASE251_FINAL_PRODUCTION_ACCEPTANCE=FAIL"
    Write-Host "Blocker: $message"
    throw
}
