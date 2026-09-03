[CmdletBinding()]
param(
    [switch]$AddToGitHubPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RequiredPythonVersion = '3.12.10'
$RequiredPointerBits = 64

function Get-CandidatePythonExecutables {
    $candidates = New-Object System.Collections.Generic.List[string]

    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command -and $command.Source) {
        $candidates.Add($command.Source)
    }

    $registryRoots = @(
        'HKLM:\SOFTWARE\Python\PythonCore\3.12\InstallPath',
        'HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore\3.12\InstallPath',
        'HKCU:\SOFTWARE\Python\PythonCore\3.12\InstallPath'
    )
    foreach ($root in $registryRoots) {
        if (Test-Path $root) {
            try {
                $props = Get-ItemProperty -Path $root
                if ($props.ExecutablePath) {
                    $candidates.Add([string]$props.ExecutablePath)
                }
                $defaultValue = (Get-Item -Path $root).GetValue('')
                if ($defaultValue) {
                    $candidates.Add((Join-Path ([string]$defaultValue) 'python.exe'))
                }
            } catch {
                Write-Verbose "Could not inspect Python registry key ${root}: $($_.Exception.Message)"
            }
        }
    }

    $commonPaths = @(
        'C:\Program Files\Python312\python.exe',
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )
    foreach ($path in $commonPaths) {
        if ($path) {
            $candidates.Add($path)
        }
    }

    return $candidates | Where-Object { $_ } | Select-Object -Unique
}

$selected = $null
$selectedPipOutput = $null
$matchingRuntimeWithoutPip = $false
foreach ($candidate in Get-CandidatePythonExecutables) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        continue
    }
    try {
        $identityOutput = & $candidate -c "import struct,sys; print('.'.join(map(str, sys.version_info[:3])) + '|' + str(struct.calcsize('P') * 8))"
        if ($LASTEXITCODE -ne 0 -or -not $identityOutput) {
            continue
        }
        $parts = ([string]$identityOutput).Trim().Split('|')
        if ($parts.Count -ne 2) {
            continue
        }
        $version = $parts[0]
        $pointerBits = 0
        if (-not [int]::TryParse($parts[1], [ref]$pointerBits)) {
            continue
        }
        if ($version -ne $RequiredPythonVersion -or $pointerBits -ne $RequiredPointerBits) {
            continue
        }

        $pipOutput = & $candidate -m pip --version 2>&1
        if ($LASTEXITCODE -ne 0 -or -not $pipOutput) {
            $matchingRuntimeWithoutPip = $true
            Write-Verbose "CPython $RequiredPythonVersion x64 candidate '$candidate' was skipped because pip is unavailable."
            continue
        }

        $selected = (Resolve-Path -LiteralPath $candidate).Path
        $selectedPipOutput = ([string]$pipOutput).Trim()
        break
    } catch {
        Write-Verbose "Python candidate failed: $candidate :: $($_.Exception.Message)"
    }
}

if (-not $selected) {
    $pipDetail = if ($matchingRuntimeWithoutPip) {
        "At least one exact CPython $RequiredPythonVersion x64 runtime was found, but pip is unavailable on every matching candidate."
    } else {
        "No exact CPython $RequiredPythonVersion x64 runtime was found."
    }
    throw @"
$pipDetail
Install the exact PSF WinGet package from an elevated PowerShell window, then rerun the bootstrap:
  winget install --id Python.Python.3.12 --exact --version $RequiredPythonVersion --scope machine --accept-source-agreements --accept-package-agreements
No production acceptance can proceed without a healthy pinned Windows Python runtime with pip.
"@
}

Write-Host $selectedPipOutput

if ($AddToGitHubPath) {
    if ([string]::IsNullOrWhiteSpace($env:GITHUB_PATH)) {
        throw 'GITHUB_PATH is not available; refusing to claim workflow PATH provisioning.'
    }
    $pythonDir = Split-Path -Parent $selected
    $scriptsDir = Join-Path $pythonDir 'Scripts'
    Add-Content -LiteralPath $env:GITHUB_PATH -Value $pythonDir
    if (Test-Path -LiteralPath $scriptsDir -PathType Container) {
        Add-Content -LiteralPath $env:GITHUB_PATH -Value $scriptsDir
    }
}

Write-Host "Validated Windows Python: $RequiredPythonVersion x64"
Write-Host "Python executable: $selected"
Write-Output $selected
