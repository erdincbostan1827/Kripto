[CmdletBinding()]
param(
    [switch]$AddToGitHubPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

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
                Write-Verbose "Could not inspect Python registry key $root: $($_.Exception.Message)"
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
$selectedVersion = $null
foreach ($candidate in Get-CandidatePythonExecutables) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        continue
    }
    try {
        $version = (& $candidate -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
        if ($LASTEXITCODE -eq 0 -and $version -match '^3\.12\.\d+$') {
            $selected = (Resolve-Path -LiteralPath $candidate).Path
            $selectedVersion = $version
            break
        }
    } catch {
        Write-Verbose "Python candidate failed: $candidate :: $($_.Exception.Message)"
    }
}

if (-not $selected) {
    throw @"
Python 3.12.x was not found on this Windows production-acceptance runner.
Install CPython 3.12 x64 at machine scope, then rerun the readiness workflow.
Recommended command from an elevated PowerShell window:
  winget install --id Python.Python.3.12 -e --scope machine --accept-source-agreements --accept-package-agreements
No production acceptance can proceed without a validated host Python 3.12.x runtime.
"@
}

& $selected -m pip --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 was found at '$selected' but pip is unavailable."
}

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

Write-Host "Validated Windows Python: $selectedVersion"
Write-Host "Python executable: $selected"
Write-Output $selected
