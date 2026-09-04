[CmdletBinding()]
param(
    [string]$CandidateRef,
    [Parameter(Mandatory = $true)][string]$HandoffDirectory,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase252-handoff",
    [int]$DiscoveryTimeoutSeconds = 120
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

function Resolve-RemoteMainSha {
    $lines = Invoke-Gh -Arguments @("api", "repos/$Repository/commits/main", "--jq", ".sha")
    $sha = ([string]($lines | Select-Object -First 1)).Trim().ToLowerInvariant()
    if ($sha -notmatch '^[0-9a-f]{40}$') { throw "Could not resolve remote main to an exact SHA. Got: '$sha'" }
    return $sha
}

function Resolve-LocalHeadSha {
    $sha = (& git rev-parse HEAD 2>&1 | Select-Object -First 1).ToString().Trim().ToLowerInvariant()
    if ($LASTEXITCODE -ne 0 -or $sha -notmatch '^[0-9a-f]{40}$') { throw "Could not resolve local HEAD to an exact SHA. Got: '$sha'" }
    return $sha
}

function Write-PhaseResult {
    param(
        [Parameter(Mandatory = $true)][bool]$Passed,
        [string]$Blocker,
        [string]$RunDirectory,
        [string]$BundlePath,
        [string]$BundleSha256,
        [string]$BuilderReceipt,
        [string]$Phase251Directory
    )
    if ([string]::IsNullOrWhiteSpace($RunDirectory)) { return }
    New-Item -ItemType Directory -Force -Path $RunDirectory | Out-Null
    $resultPath = Join-Path $RunDirectory "PHASE252_ATOMIC_HANDOFF_RESULT.json"
    if (Test-Path -LiteralPath $resultPath) { throw "Refusing to overwrite existing Phase 252 result: $resultPath" }
    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE252_ATOMIC_CAMPAIGN_HANDOFF_RESULT"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        campaign_bundle_path = $BundlePath
        campaign_bundle_sha256 = $BundleSha256
        builder_receipt = $BuilderReceipt
        phase251_evidence_directory = $Phase251Directory
        live_enabled = $false
        default_mode = "PAPER"
        eligible_for_human_approval = $Passed
        blocker = $Blocker
        truth_policy = "Phase 252 PASS means an atomically published exact-SHA campaign bundle remained byte-identical through Phase 251 final automated acceptance. LIVE remains disabled and separate human approval is still required."
    }
    $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Write-Host "Result JSON: $resultPath"
}

$runDirectory = ""
$bundlePath = ""
$bundleSha = ""
$builderReceiptPath = ""
$phase251Directory = ""

try {
    Require-Command -Name "gh"
    Require-Command -Name "git"
    Require-Command -Name "python"
    Invoke-Gh -Arguments @("auth", "status") | Out-Null

    $repoRoot = (& git rev-parse --show-toplevel 2>&1 | Select-Object -First 1).ToString().Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) { throw "Could not resolve repository root." }
    $repoRoot = [IO.Path]::GetFullPath($repoRoot)

    $remoteMain = Resolve-RemoteMainSha
    if ([string]::IsNullOrWhiteSpace($CandidateRef)) { $CandidateRef = $remoteMain }
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') { throw "CandidateRef must be an exact 40-character SHA. Got: '$CandidateRef'" }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    if ($CandidateRef -ne $remoteMain) { throw "FINAL_ACCEPTANCE_REQUIRES_CURRENT_REMOTE_MAIN: candidate=$CandidateRef remote_main=$remoteMain" }

    $localHead = Resolve-LocalHeadSha
    if ($localHead -ne $CandidateRef) { throw "PHASE252_LOCAL_HEAD_NOT_CANDIDATE: local_head=$localHead candidate=$CandidateRef" }

    $environmentId = ([string][Environment]::GetEnvironmentVariable("ACCEPTANCE_ENVIRONMENT_ID")).Trim()
    $topologyHash = ([string][Environment]::GetEnvironmentVariable("ACCEPTANCE_TOPOLOGY_HASH")).Trim().ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($environmentId)) { throw "ACCEPTANCE_ENVIRONMENT_ID is required to bind the campaign bundle." }
    if ($topologyHash -notmatch '^[0-9a-f]{64}$') { throw "ACCEPTANCE_TOPOLOGY_HASH must be an exact SHA-256 digest." }

    $handoffRoot = [IO.Path]::GetFullPath($HandoffDirectory)
    New-Item -ItemType Directory -Force -Path $handoffRoot | Out-Null
    $repoResolved = (Resolve-Path -LiteralPath $repoRoot).Path
    $handoffResolved = (Resolve-Path -LiteralPath $handoffRoot).Path
    if ($handoffResolved.StartsWith($repoResolved + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or $handoffResolved -eq $repoResolved) {
        throw "HANDOFF_DIRECTORY_MUST_BE_OUTSIDE_REPOSITORY"
    }

    $resultRoot = [IO.Path]::GetFullPath($OutputDirectory)
    New-Item -ItemType Directory -Force -Path $resultRoot | Out-Null
    $suffix = "{0}-{1}" -f [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ"), ([Guid]::NewGuid().ToString("N").Substring(0, 12))
    $runDirectory = Join-Path $resultRoot "run-$suffix"
    if (Test-Path -LiteralPath $runDirectory) { throw "Refusing to overwrite existing Phase 252 run directory: $runDirectory" }
    New-Item -ItemType Directory -Path $runDirectory | Out-Null

    $bundlePath = Join-Path $handoffResolved "PHASE252_CAMPAIGN_EVIDENCE-$CandidateRef-$suffix.zip"
    $builderReceiptPath = Join-Path $runDirectory "PHASE252_CAMPAIGN_BUNDLE_BUILD.json"
    $builderScript = Join-Path $repoRoot "scripts/external/build_campaign_evidence_bundle.py"
    if (-not (Test-Path -LiteralPath $builderScript -PathType Leaf)) { throw "Phase 252 builder is missing: $builderScript" }

    & python $builderScript `
        --root $repoRoot `
        --candidate $CandidateRef `
        --acceptance-environment-id $environmentId `
        --topology-hash $topologyHash `
        --output $bundlePath `
        --receipt $builderReceiptPath
    if ($LASTEXITCODE -ne 0) { throw "Phase 252 campaign bundle builder failed closed." }

    if (-not (Test-Path -LiteralPath $builderReceiptPath -PathType Leaf)) { throw "Phase 252 builder receipt is missing." }
    $builder = Get-Content -LiteralPath $builderReceiptPath -Raw | ConvertFrom-Json
    if ($builder.classification -ne "PHASE252_CAMPAIGN_BUNDLE_BUILD_RECEIPT" -or $builder.verified -ne $true -or $builder.atomic_publish -ne $true) {
        throw "Phase 252 builder receipt is not verified/atomic."
    }
    if ([string]$builder.candidate_sha -ne $CandidateRef) { throw "Phase 252 builder candidate SHA mismatch." }
    if ([string]$builder.topology_hash -ne $topologyHash) { throw "Phase 252 builder topology hash mismatch." }
    if ($builder.live_enabled -ne $false -or $builder.production_ready -ne $false) { throw "Phase 252 builder violated the PAPER/LIVE safety boundary." }
    if (-not (Test-Path -LiteralPath $bundlePath -PathType Leaf)) { throw "Atomically published campaign bundle is missing." }

    $bundleSha = (Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleSha -ne ([string]$builder.bundle_sha256).ToLowerInvariant()) { throw "BUILDER_BUNDLE_SHA256_MISMATCH" }

    $remoteBeforeHandoff = Resolve-RemoteMainSha
    if ($remoteBeforeHandoff -ne $CandidateRef) { throw "REMOTE_MAIN_MOVED_BEFORE_HANDOFF: candidate=$CandidateRef remote_main=$remoteBeforeHandoff" }

    $phase251Script = Join-Path $repoRoot "tools/run_phase251_final_production_acceptance.ps1"
    if (-not (Test-Path -LiteralPath $phase251Script -PathType Leaf)) { throw "Phase 251 final acceptance wrapper is missing." }
    $phase251Directory = Join-Path $runDirectory "phase251"
    & $phase251Script `
        -CandidateRef $CandidateRef `
        -CampaignEvidenceBundlePath $bundlePath `
        -Repository $Repository `
        -OutputDirectory $phase251Directory `
        -DiscoveryTimeoutSeconds $DiscoveryTimeoutSeconds

    $bundleShaAfter = (Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($bundleShaAfter -ne $bundleSha) { throw "BUNDLE_CHANGED_DURING_PHASE251: before=$bundleSha after=$bundleShaAfter" }

    $phase251Pass = @(Get-ChildItem -LiteralPath $phase251Directory -File -Filter "PHASE251_FINAL_ORCHESTRATION_RESULT-*.json" | Sort-Object LastWriteTimeUtc -Descending)
    if ($phase251Pass.Count -lt 1) { throw "Phase 251 final orchestration result was not produced." }
    $phase251Result = Get-Content -LiteralPath $phase251Pass[0].FullName -Raw | ConvertFrom-Json
    if ($phase251Result.passed -ne $true -or [string]$phase251Result.candidate_sha -ne $CandidateRef -or [string]$phase251Result.campaign_bundle_sha256 -ne $bundleSha) {
        throw "Phase 251 final production acceptance did not PASS for the exact Phase 252 bundle."
    }
    if ($phase251Result.live_enabled -ne $false -or [string]$phase251Result.default_mode -ne "PAPER") { throw "Phase 251 result violated the PAPER/LIVE safety boundary." }

    $remoteMainAfter = Resolve-RemoteMainSha
    if ($remoteMainAfter -ne $CandidateRef) { throw "REMOTE_MAIN_MOVED_DURING_HANDOFF: candidate=$CandidateRef remote_main_after=$remoteMainAfter" }

    Write-PhaseResult -Passed $true -Blocker "" -RunDirectory $runDirectory -BundlePath $bundlePath -BundleSha256 $bundleSha -BuilderReceipt $builderReceiptPath -Phase251Directory $phase251Directory
    Write-Host "PHASE252_ATOMIC_CAMPAIGN_HANDOFF=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Campaign bundle SHA-256: $bundleSha"
    Write-Host "LIVE remains disabled. Separate human approval is required before any LIVE enablement."
}
catch {
    $message = $_.Exception.Message
    try {
        $existingResult = if ([string]::IsNullOrWhiteSpace($runDirectory)) { "" } else { Join-Path $runDirectory "PHASE252_ATOMIC_HANDOFF_RESULT.json" }
        if (-not [string]::IsNullOrWhiteSpace($runDirectory) -and -not (Test-Path -LiteralPath $existingResult -PathType Leaf)) {
            Write-PhaseResult -Passed $false -Blocker $message -RunDirectory $runDirectory -BundlePath $bundlePath -BundleSha256 $bundleSha -BuilderReceipt $builderReceiptPath -Phase251Directory $phase251Directory
        }
    } catch { Write-Warning "Could not write Phase 252 fail-closed result JSON: $($_.Exception.Message)" }
    Write-Host "PHASE252_ATOMIC_CAMPAIGN_HANDOFF=FAIL"
    Write-Host "Blocker: $message"
    throw
}
