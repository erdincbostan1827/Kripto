[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('StrategyCycle','StrategyLoop','PrivateReconnectDrill','Status')][string]$Action,
    [string]$CandidateRef,
    [Parameter(Mandatory = $true)][string]$StateDirectory,
    [string]$EnvironmentId = $env:ACCEPTANCE_ENVIRONMENT_ID,
    [string]$TopologyHash = $env:ACCEPTANCE_TOPOLOGY_HASH,
    [string]$Symbol = 'BTCUSDT',
    [ValidateSet('1m','3m','5m','15m','30m','1h','4h','1d')][string]$Timeframe = '1h',
    [decimal]$PaperNotional = 10,
    [int]$LatencyMs = 50,
    [double]$TimeoutSeconds = 10,
    [double]$IntervalSeconds = 300,
    [int]$MaxCycles = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is unavailable: $Name"
    }
}

function Resolve-ExactHeadSha {
    $rawValue = & git rev-parse HEAD 2>&1
    $gitSucceeded = $?
    $value = ($rawValue | Select-Object -First 1).ToString().Trim().ToLowerInvariant()
    if (-not $gitSucceeded -or $value -notmatch '^[0-9a-f]{40}$') {
        throw "Could not resolve exact git HEAD. Got '$value'."
    }
    return $value
}

Require-Command -Name 'git'

$rawRepoRoot = & git rev-parse --show-toplevel 2>&1
$repoRootResolved = $?
$repoRoot = ($rawRepoRoot | Select-Object -First 1).ToString().Trim()
if (-not $repoRootResolved -or [string]::IsNullOrWhiteSpace($repoRoot)) {
    throw 'Could not resolve repository root.'
}
Set-Location -LiteralPath $repoRoot

$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    throw "Locked Phase266 runtime interpreter is missing: $venvPython"
}

$headSha = Resolve-ExactHeadSha
if ([string]::IsNullOrWhiteSpace($CandidateRef)) {
    $CandidateRef = $headSha
}
$CandidateRef = $CandidateRef.Trim().ToLowerInvariant()
if ($CandidateRef -notmatch '^[0-9a-f]{40}$') {
    throw "CandidateRef must be an exact 40-character SHA. Got '$CandidateRef'."
}
if ($CandidateRef -ne $headSha) {
    throw "PHASE266_LOCAL_HEAD_NOT_CANDIDATE: local_head=$headSha candidate=$CandidateRef"
}

if ([string]$env:GITHUB_ACTIONS -eq 'true') {
    $runnerName = ([string]$env:RUNNER_NAME).Trim()
    $runnerOs = ([string]$env:RUNNER_OS).Trim()
    $runnerArch = ([string]$env:RUNNER_ARCH).Trim()
    if ([string]::IsNullOrWhiteSpace($runnerName) -or
        [string]::IsNullOrWhiteSpace($runnerOs) -or
        [string]::IsNullOrWhiteSpace($runnerArch)) {
        throw 'Protected GitHub runner identity components are incomplete.'
    }
    $EnvironmentId = 'github-actions:{0}:{1}:{2}:phase266-protected-campaign' -f $runnerName, $runnerOs, $runnerArch
    $env:ACCEPTANCE_ENVIRONMENT_ID = $EnvironmentId
    if (-not [string]::IsNullOrWhiteSpace([string]$env:GITHUB_ENV)) {
        "ACCEPTANCE_ENVIRONMENT_ID=$EnvironmentId" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
    }
}
if ([string]::IsNullOrWhiteSpace($EnvironmentId)) {
    throw 'ACCEPTANCE_ENVIRONMENT_ID/EnvironmentId is required.'
}
if ([string]::IsNullOrWhiteSpace($TopologyHash) -or $TopologyHash -notmatch '^[0-9a-fA-F]{64}$') {
    throw 'ACCEPTANCE_TOPOLOGY_HASH/TopologyHash must be an exact SHA-256 digest.'
}
if ([string]::IsNullOrWhiteSpace($env:PHASE265_TELEMETRY_HMAC_KEY) -or [Text.Encoding]::UTF8.GetByteCount($env:PHASE265_TELEMETRY_HMAC_KEY) -lt 32) {
    throw 'PHASE265_TELEMETRY_HMAC_KEY must contain at least 32 UTF-8 bytes.'
}
if (-not [IO.Path]::IsPathRooted($StateDirectory)) {
    throw 'StateDirectory must be an absolute path outside the repository.'
}
$stateFull = [IO.Path]::GetFullPath($StateDirectory)
$repoFull = [IO.Path]::GetFullPath($repoRoot)
if ($stateFull -eq $repoFull -or $stateFull.StartsWith($repoFull + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'StateDirectory must be outside the repository.'
}
New-Item -ItemType Directory -Force -Path $stateFull | Out-Null

if ($Action -eq 'PrivateReconnectDrill') {
    if ([string]::IsNullOrWhiteSpace($env:BINANCE_TESTNET_API_KEY) -or [string]::IsNullOrWhiteSpace($env:BINANCE_TESTNET_API_SECRET)) {
        throw 'BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET are required for PrivateReconnectDrill.'
    }
}

$common = @(
    'scripts/external/phase266_campaign_runtime.py',
    '--candidate', $CandidateRef,
    '--state-dir', $stateFull,
    '--environment-id', $EnvironmentId,
    '--topology-hash', $TopologyHash.ToLowerInvariant()
)

switch ($Action) {
    'StrategyCycle' {
        $arguments = $common + @(
            'strategy-cycle',
            '--symbol', $Symbol,
            '--timeframe', $Timeframe,
            '--paper-notional', ([string]$PaperNotional),
            '--latency-ms', ([string]$LatencyMs),
            '--timeout-seconds', ([string]$TimeoutSeconds)
        )
    }
    'StrategyLoop' {
        $arguments = $common + @(
            'strategy-loop',
            '--symbol', $Symbol,
            '--timeframe', $Timeframe,
            '--paper-notional', ([string]$PaperNotional),
            '--latency-ms', ([string]$LatencyMs),
            '--timeout-seconds', ([string]$TimeoutSeconds),
            '--interval-seconds', ([string]$IntervalSeconds),
            '--max-cycles', ([string]$MaxCycles)
        )
    }
    'PrivateReconnectDrill' {
        $arguments = $common + @('private-reconnect-drill', '--timeout-seconds', ([string]$TimeoutSeconds))
    }
    'Status' {
        $arguments = $common + @('status')
    }
    default {
        throw "Unsupported Phase266 action: $Action"
    }
}

Write-Host "Phase266 protected campaign runtime"
Write-Host "Candidate SHA: $CandidateRef"
Write-Host "Action: $Action"
Write-Host "State directory: $stateFull"
Write-Host 'LIVE remains disabled; this wrapper exposes no real-order command.'

& $venvPython @arguments
$runtimeSucceeded = $?
if (-not $runtimeSucceeded) {
    throw 'PHASE266_PROTECTED_CAMPAIGN_RUNTIME=FAIL'
}
Write-Host 'PHASE266_PROTECTED_CAMPAIGN_RUNTIME=PASS'
Write-Host 'PASS means only that the requested protected runtime action completed. Campaign acceptance still depends on the Phase265 blockers reaching zero.'
