[CmdletBinding()]
param(
    [string]$CandidateRef,
    [string]$Symbol = "BTCUSDT",
    [Parameter(Mandatory = $true)][string]$PartialPrice,
    [decimal]$MaxNotional = 15,
    [string]$Repository = "erdincbostan1827/Kripto",
    [string]$OutputDirectory = ".phase245-binance-testnet",
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
    param([Parameter(Mandatory = $true)][bool]$Passed, [string]$RunId, [string]$Detail, [string]$Blocker)
    $payload = [ordered]@{
        schema_version = "1.0"
        classification = "PHASE245_BINANCE_TESTNET_ACCEPTANCE_ORCHESTRATION"
        generated_at = [DateTimeOffset]::UtcNow.ToString("o")
        passed = $Passed
        repository = $Repository
        candidate_sha = $CandidateRef
        workflow = "Phase 245 Binance TESTNET Acceptance"
        run_id = $RunId
        symbol = $Symbol
        max_notional = $MaxNotional.ToString([Globalization.CultureInfo]::InvariantCulture)
        partial_price = $PartialPrice
        detail = $Detail
        blocker = $Blocker
        production_ready = $false
        live_enabled = $false
        truth_policy = "Phase 245 PASS closes only the exact-SHA credentialed Binance Spot TESTNET scenario on the intended Windows target identity. It does not authorize real-money LIVE trading or close campaign/signing gates."
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
    if ($CandidateRef -notmatch '^[0-9a-fA-F]{40}$') { throw "CandidateRef must resolve to an exact 40-character commit SHA. Got: '$CandidateRef'" }
    $CandidateRef = $CandidateRef.ToLowerInvariant()
    $Symbol = $Symbol.Trim().ToUpperInvariant()
    if ($Symbol -notmatch '^[A-Z0-9]{5,20}$') { throw "Symbol must match ^[A-Z0-9]{5,20}$." }
    if ($MaxNotional -le 0 -or $MaxNotional -gt 15) { throw "MaxNotional must be >0 and <=15." }
    $culture = [Globalization.CultureInfo]::InvariantCulture
    $style = [Globalization.NumberStyles]::Number
    [decimal]$partialDecimal = 0
    if (-not [decimal]::TryParse($PartialPrice, $style, $culture, [ref]$partialDecimal) -or $partialDecimal -le 0) {
        throw "PartialPrice must be a positive decimal number using '.' as decimal separator."
    }
    $maxNotionalText = $MaxNotional.ToString($culture)
    $partialPriceText = $partialDecimal.ToString($culture)
    $PartialPrice = $partialPriceText
    $expectedRunTitle = "Phase 245 Binance TESTNET Acceptance $CandidateRef"

    $dispatchStarted = [DateTimeOffset]::UtcNow
    Invoke-Gh -Arguments @(
        "workflow", "run", "Phase 245 Binance TESTNET Acceptance",
        "--repo", $Repository,
        "--ref", "main",
        "-f", "candidate_ref=$CandidateRef",
        "-f", "symbol=$Symbol",
        "-f", "max_notional=$maxNotionalText",
        "-f", "partial_price=$partialPriceText"
    ) | Out-Null

    $deadline = [DateTimeOffset]::UtcNow.AddSeconds($DiscoveryTimeoutSeconds)
    do {
        $json = (Invoke-Gh -Arguments @(
            "run", "list", "--repo", $Repository,
            "--workflow", "Phase 245 Binance TESTNET Acceptance",
            "--event", "workflow_dispatch", "--limit", "20",
            "--json", "databaseId,createdAt,status,conclusion,displayTitle"
        )) -join "`n"
        $parsedRuns = $json | ConvertFrom-Json
        $runs = @()
        if ($null -ne $parsedRuns) {
            if ($parsedRuns -is [System.Array]) { $runs = @($parsedRuns | ForEach-Object { $_ }) } else { $runs = @($parsedRuns) }
        }
        $candidateRuns = @($runs | Where-Object {
            $createdAt = Get-RunCreatedAt -Run $_
            $displayTitle = [string](Get-RunProperty -Run $_ -Name "displayTitle")
            ($null -ne $createdAt) -and ($createdAt -ge $dispatchStarted.AddSeconds(-10)) -and ($displayTitle -eq $expectedRunTitle)
        } | Sort-Object { Get-RunCreatedAt -Run $_ } -Descending)
        if ($candidateRuns.Count -gt 0) {
            $runId = [string](Get-RunProperty -Run $candidateRuns[0] -Name "databaseId")
            if ([string]::IsNullOrWhiteSpace($runId)) { throw "Discovered Phase 245 run does not expose databaseId." }
            break
        }
        Start-Sleep -Seconds 2
    } while ([DateTimeOffset]::UtcNow -lt $deadline)
    if ([string]::IsNullOrWhiteSpace($runId)) { throw "Could not discover the dispatched Phase 245 Binance TESTNET Acceptance run for exact candidate '$CandidateRef'." }

    & gh run watch $runId --repo $Repository --exit-status
    $workflowPassed = ($LASTEXITCODE -eq 0)

    $resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
    if (Test-Path -LiteralPath $resolvedOutput) { Remove-Item -LiteralPath $resolvedOutput -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $resolvedOutput | Out-Null
    $artifactName = "phase245-binance-testnet-acceptance-$CandidateRef"
    Invoke-Gh -Arguments @("run", "download", $runId, "--repo", $Repository, "--name", $artifactName, "--dir", $resolvedOutput) | Out-Null

    $workflowResultPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "PHASE245_BINANCE_TESTNET_RESULT.json" | Select-Object -First 1 -ExpandProperty FullName
    $identityPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "BINANCE_TESTNET_TARGET_IDENTITY.json" | Select-Object -First 1 -ExpandProperty FullName
    $runtimePath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "manifest_runtime.json" | Select-Object -First 1 -ExpandProperty FullName
    $testnetPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "manifest_testnet.json" | Select-Object -First 1 -ExpandProperty FullName
    $scenarioPath = Get-ChildItem -LiteralPath $resolvedOutput -Recurse -File -Filter "binance_testnet.log" | Select-Object -First 1 -ExpandProperty FullName
    if (-not $workflowResultPath) { throw "Phase 245 artifact did not contain PHASE245_BINANCE_TESTNET_RESULT.json." }
    if (-not $identityPath) { throw "Phase 245 artifact did not contain BINANCE_TESTNET_TARGET_IDENTITY.json." }
    if (-not $runtimePath) { throw "Phase 245 artifact did not contain manifest_runtime.json." }
    if (-not $testnetPath) { throw "Phase 245 artifact did not contain manifest_testnet.json." }
    if (-not $scenarioPath) { throw "Phase 245 artifact did not contain binance_testnet.log." }

    $workflowResult = Get-Content -LiteralPath $workflowResultPath -Raw | ConvertFrom-Json
    $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    $runtime = Get-Content -LiteralPath $runtimePath -Raw | ConvertFrom-Json
    $testnet = Get-Content -LiteralPath $testnetPath -Raw | ConvertFrom-Json
    $scenario = Get-Content -LiteralPath $scenarioPath -Raw | ConvertFrom-Json

    if ($workflowResult.classification -ne "PHASE245_BINANCE_TESTNET_ACCEPTANCE_WORKFLOW_RESULT") { throw "Unexpected Phase 245 workflow result classification: $($workflowResult.classification)" }
    if ($identity.classification -ne "PHASE245_BINANCE_TESTNET_TARGET_IDENTITY_NOT_ACCEPTANCE_EVIDENCE") { throw "Unexpected Phase 245 target identity classification: $($identity.classification)" }
    if ($identity.candidate_sha -ne $CandidateRef) { throw "Phase 245 target identity is bound to a different git SHA: $($identity.candidate_sha)" }
    if ($identity.runner_os -ne "Windows") { throw "Phase 245 target identity did not run on Windows: $($identity.runner_os)" }
    if ($identity.exchange_endpoint -ne "https://testnet.binance.vision") { throw "Phase 245 target identity is not bound to Binance Spot TESTNET." }
    if ([string]$identity.symbol -ne $Symbol) { throw "Phase 245 target identity symbol mismatch: $($identity.symbol)" }
    if ([decimal]::Parse([string]$identity.max_notional, $culture) -ne $MaxNotional) { throw "Phase 245 target identity max_notional mismatch." }
    if ([decimal]::Parse([string]$identity.partial_price, $culture) -ne $partialDecimal) { throw "Phase 245 target identity partial_price mismatch." }

    foreach ($manifest in @($runtime, $testnet)) {
        if ($manifest.classification -ne "EXTERNAL_ACCEPTANCE_EVIDENCE_BUNDLE") { throw "Unexpected external acceptance classification: $($manifest.classification)" }
        if ($manifest.environment.git_commit_sha -ne $CandidateRef) { throw "Acceptance evidence is bound to a different git SHA: $($manifest.environment.git_commit_sha)" }
        if ($manifest.environment.topology_hash -ne $identity.topology_hash) { throw "Acceptance evidence topology hash does not match the Phase 245 target identity." }
    }
    if ($runtime.profile -ne "runtime") { throw "Unexpected runtime profile: $($runtime.profile)" }
    if ($testnet.profile -ne "testnet") { throw "Unexpected TESTNET profile: $($testnet.profile)" }
    if ($testnet.credentials.binance_testnet -ne "PRESENT_REDACTED") { throw "Phase 245 TESTNET credentials were not verified as present/redacted." }
    if ($workflowResult.candidate_sha -ne $CandidateRef) { throw "Phase 245 workflow result is bound to a different git SHA: $($workflowResult.candidate_sha)" }
    if ($scenario.endpoint -ne "https://testnet.binance.vision") { throw "Scenario endpoint is not Binance Spot TESTNET: $($scenario.endpoint)" }

    if ($null -ne $workflowResult.PSObject.Properties["blocker"]) { $blocker = [string]$workflowResult.blocker }
    if ([string]::IsNullOrWhiteSpace($blocker) -and $null -ne $testnet.PSObject.Properties["blocker"]) { $blocker = [string]$testnet.blocker }
    if ([string]::IsNullOrWhiteSpace($blocker) -and $null -ne $runtime.PSObject.Properties["blocker"]) { $blocker = [string]$runtime.blocker }

    $runtimeStatus = [string]$runtime.groups.runtime
    $testnetStatus = [string]$testnet.groups.testnet
    $passed = (
        $workflowPassed -and
        $workflowResult.passed -eq $true -and
        $workflowResult.production_ready -eq $false -and
        $workflowResult.live_enabled -eq $false -and
        $runtime.real_target_explicitly_confirmed -eq $true -and
        $testnet.real_target_explicitly_confirmed -eq $true -and
        $runtime.challenge.verified -eq $true -and
        $testnet.challenge.verified -eq $true -and
        $runtime.challenge.trust_verified -eq $true -and
        $testnet.challenge.trust_verified -eq $true -and
        $runtime.selected_all_pass -eq $true -and
        $testnet.selected_all_pass -eq $true -and
        $runtimeStatus -eq "PASS" -and
        $testnetStatus -eq "PASS" -and
        $scenario.all_pass -eq $true -and
        $scenario.checks.market_order.pass -eq $true -and
        $scenario.checks.limit_order.pass -eq $true -and
        $scenario.checks.cancel.pass -eq $true -and
        $scenario.checks.partial_fill.pass -eq $true
    )
    if (-not $passed) {
        if ([string]::IsNullOrWhiteSpace($blocker)) {
            if ($scenario.endpoint -ne "https://testnet.binance.vision") { $blocker = "NON_TESTNET_ENDPOINT" }
            elseif ($runtime.challenge.verified -ne $true -or $testnet.challenge.verified -ne $true) { $blocker = "RELEASE_CHALLENGE_NOT_VERIFIED" }
            elseif ($runtime.challenge.trust_verified -ne $true -or $testnet.challenge.trust_verified -ne $true) { $blocker = "RELEASE_CHALLENGE_TRUST_NOT_VERIFIED" }
            elseif ($runtimeStatus -ne "PASS") { $blocker = "RUNTIME_GROUP_$runtimeStatus" }
            elseif ($testnetStatus -ne "PASS") { $blocker = "TESTNET_GROUP_$testnetStatus" }
            elseif ($scenario.checks.partial_fill.pass -ne $true) { $blocker = "TESTNET_PARTIAL_FILL_NOT_PROVEN" }
            elseif (-not $workflowPassed) { $blocker = "WORKFLOW_FAILED" }
            else { $blocker = "BINANCE_TESTNET_ACCEPTANCE_NOT_ALL_PASS" }
        }
        Write-PhaseResult -Passed $false -RunId $runId -Detail "Exact-SHA runtime + credentialed Binance Spot TESTNET acceptance did not PASS." -Blocker $blocker
        Write-Host "PHASE245_BINANCE_TESTNET_ACCEPTANCE=FAIL"
        Write-Host "Candidate SHA: $CandidateRef"
        Write-Host "Workflow run id: $runId"
        Write-Host "Blocker: $blocker"
        throw "Phase 245 Binance TESTNET Acceptance failed closed: $blocker"
    }

    Write-PhaseResult -Passed $true -RunId $runId -Detail "Exact-SHA trusted runtime prerequisite and credentialed Binance Spot TESTNET market/limit/cancel/partial-fill scenario verified on the bound Windows target identity." -Blocker ""
    Write-Host "PHASE245_BINANCE_TESTNET_ACCEPTANCE=PASS"
    Write-Host "Candidate SHA: $CandidateRef"
    Write-Host "Workflow run id: $runId"
    Write-Host "Runtime group: $runtimeStatus"
    Write-Host "TESTNET group: $testnetStatus"
    Write-Host "Endpoint: https://testnet.binance.vision"
    Write-Host "No production-ready/LIVE claim is made by this phase."
}
catch {
    $message = $_.Exception.Message
    if ([string]::IsNullOrWhiteSpace($blocker)) { $blocker = $message }
    try {
        $existing = Join-Path ([System.IO.Path]::GetFullPath($OutputDirectory)) "PHASE245_ORCHESTRATION_RESULT.json"
        if (-not (Test-Path -LiteralPath $existing -PathType Leaf)) { Write-PhaseResult -Passed $false -RunId $runId -Detail $message -Blocker $blocker }
    } catch { Write-Warning "Could not write Phase 245 result JSON: $($_.Exception.Message)" }
    if ($message -notlike "Phase 245 Binance TESTNET Acceptance failed closed:*") { Write-Host "PHASE245_BINANCE_TESTNET_ACCEPTANCE=FAIL" }
    throw
}
