<#
[FL_INDEX: setup_runtimes, windows_portable, node_embed, python_embed, zero_dependency | purpose="Autonomous zero-installer provisioner for Flowork OS portable runtimes on Windows"]
#>
param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimesRoot = Split-Path -Parent $ScriptDir
$NodeDir = Join-Path $RuntimesRoot "node"
$PythonDir = Join-Path $RuntimesRoot "python"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "⚡ Flowork OS — Autonomous Runtime Provisioner (Windows)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

# -------------------------------------------------------------
# 1. Node.js Portable Runtime Provisioning
# -------------------------------------------------------------
$NodeTargetExe = Join-Path $NodeDir "node.exe"
$SystemNode = Get-Command node -ErrorAction SilentlyContinue

if (-not $Force -and (Test-Path $NodeTargetExe)) {
    Write-Host "[Runtime:Node] ✅ Portable Node.js already present: $NodeTargetExe" -ForegroundColor Green
} elseif (-not $Force -and $SystemNode) {
    Write-Host "[Runtime:Node] ✅ System Node.js detected: $($SystemNode.Source)" -ForegroundColor Green
} else {
    Write-Host "[Runtime:Node] 📥 Fetching official portable Node.js binary (v20.18.0)..." -ForegroundColor Yellow
    if (-not (Test-Path $NodeDir)) { New-Item -ItemType Directory -Path $NodeDir -Force | Out-Null }
    
    $NodeUrl = "https://nodejs.org/dist/v20.18.0/win-x64/node.exe"
    try {
        Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeTargetExe -UseBasicParsing
        Write-Host "[Runtime:Node] ✅ Portable Node.js installed to $NodeTargetExe" -ForegroundColor Green
    } catch {
        Write-Host "[Runtime:Node] ⚠️ Could not download portable node.exe: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# -------------------------------------------------------------
# 2. Python 3 Portable Runtime Provisioning (Anti-Windows Store Alias)
# -------------------------------------------------------------
$PythonTargetExe = Join-Path $PythonDir "python.exe"

# Detect if system python is a Microsoft Store fake alias
$IsRealPython = $false
$SystemPython = Get-Command python -ErrorAction SilentlyContinue
if ($SystemPython) {
    if ($SystemPython.Source -like "*WindowsApps*") {
        Write-Host "[Runtime:Python] ⚠️ Detected Windows Store stub alias; bypassing Microsoft Store trap." -ForegroundColor Yellow
        $IsRealPython = $false
    } else {
        try {
            $PyVer = & $SystemPython.Source --version 2>&1
            if ($PyVer -like "*Python 3*") {
                $IsRealPython = $true
                Write-Host "[Runtime:Python] ✅ System Python 3 detected: $($SystemPython.Source)" -ForegroundColor Green
            }
        } catch {
            $IsRealPython = $false
        }
    }
}

if (-not $Force -and (Test-Path $PythonTargetExe)) {
    Write-Host "[Runtime:Python] ✅ Portable Python 3 already present: $PythonTargetExe" -ForegroundColor Green
} elseif (-not $Force -and $IsRealPython) {
    Write-Host "[Runtime:Python] ✅ Host environment already satisfied." -ForegroundColor Green
} else {
    Write-Host "[Runtime:Python] 📥 Fetching official Windows embeddable Python package..." -ForegroundColor Yellow
    if (-not (Test-Path $PythonDir)) { New-Item -ItemType Directory -Path $PythonDir -Force | Out-Null }
    
    $PyZipUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
    $TempZip = Join-Path $env:TEMP "python_embed_$PID.zip"
    try {
        Invoke-WebRequest -Uri $PyZipUrl -OutFile $TempZip -UseBasicParsing
        Expand-Archive -Path $TempZip -DestinationPath $PythonDir -Force
        Remove-Item $TempZip -Force -ErrorAction SilentlyContinue

        # Un-restrict site-packages in embeddable python
        $PthFile = Get-ChildItem -Path $PythonDir -Filter "*._pth" | Select-Object -First 1
        if ($PthFile) {
            $Content = Get-Content $PthFile.FullName
            $Updated = $Content -replace "^#import site", "import site"
            Set-Content -Path $PthFile.FullName -Value $Updated
        }
        Write-Host "[Runtime:Python] ✅ Portable Python installed to $PythonTargetExe" -ForegroundColor Green
    } catch {
        Write-Host "[Runtime:Python] ⚠️ Could not download embeddable Python: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Runtime check complete. Zero-dependency environment ready." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
