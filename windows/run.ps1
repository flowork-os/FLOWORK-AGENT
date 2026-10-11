# =============================================================================
# 🚀 FLOWORK OS — NATIVE CANVAS LAUNCHER & POLYGLOT ENGINE (POWERSHELL)
# Target: C:\flowork
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================

$TargetDir = "C:\flowork"
if (-not (Test-Path $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
Set-Location $TargetDir

# 1. Resolve Node.js runtime
$NodeBin = "node"
if (Test-Path (Join-Path $TargetDir "node\node.exe")) {
    $NodeBin = Join-Path $TargetDir "node\node.exe"
} elseif (Get-Command "node" -ErrorAction SilentlyContinue) {
    $NodeBin = "node"
} elseif (Test-Path "C:\Program Files\nodejs\node.exe") {
    $NodeBin = "C:\Program Files\nodejs\node.exe"
} else {
    Write-Host "[X-Flow] ⚡ Fetching standalone Node.js runtime into $TargetDir\node..." -ForegroundColor Yellow
    $nodeDir = Join-Path $TargetDir "node"
    if (-not (Test-Path $nodeDir)) { New-Item -ItemType Directory -Path $nodeDir -Force | Out-Null }
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile("https://nodejs.org/dist/v20.18.0/win-x64/node.exe", (Join-Path $nodeDir "node.exe"))
        $NodeBin = Join-Path $nodeDir "node.exe"
        Write-Host "[X-Flow] ✅ Node.js runtime ready." -ForegroundColor Green
    } catch {
        Write-Warning "[X-Flow] Could not download standalone Node.js: $_"
    }
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[X-Flow] Starting Sovereign Canvas Host (PowerShell)..." -ForegroundColor Cyan
Write-Host "[X-Flow] Root Path: $TargetDir" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 2. Set Portable Environment
$env:FLOWORK_PORTABLE_ROOT = Join-Path $TargetDir "portable-home"
$env:FLOWAI_CLI_HOME = Join-Path $TargetDir "portable-home"

# Dynamic Portability Shield: purge stale cross-OS or non-existent workspace path
$WsCfg = Join-Path $TargetDir ".flowork\config\active_workspace.json"
if (Test-Path $WsCfg) {
    try {
        $cfg = Get-Content $WsCfg -Raw | ConvertFrom-Json
        if ($cfg.path -and (-not (Test-Path $cfg.path) -or $cfg.path.StartsWith("/"))) {
            Remove-Item $WsCfg -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

# 3. Kill previous stale instances if running
Get-Process -Name "x-flow" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 4. Ensure Sovereign Router Switchboard (:9099) is running
$flBin = Join-Path $TargetDir ".FL_BIN"
if (-not (Test-Path $flBin)) { New-Item -ItemType Directory -Path $flBin -Force | Out-Null }
$routerPortListening = $false
try {
    $conns = Get-NetTCPConnection -LocalPort 9099 -ErrorAction SilentlyContinue
    if ($conns) { $routerPortListening = $true }
} catch {}
if (-not $routerPortListening) {
    Write-Host "[X-Flow] Launching Sovereign Router Switchboard on port 9099..." -ForegroundColor Cyan
    Start-Process -FilePath $NodeBin -ArgumentList @((Join-Path $TargetDir "connection\router.js")) -WorkingDirectory $TargetDir -WindowStyle Hidden
    Start-Sleep -Milliseconds 800
}

# 5. Native binary x-flow will launch Canvas UI in standalone App Mode
Write-Host "[X-Flow] Sovereign Canvas Host ready on http://127.0.0.1:19890" -ForegroundColor Green

# 6. Launch native binary
if (Test-Path (Join-Path $TargetDir "x-flow.exe")) {
    Start-Process (Join-Path $TargetDir "x-flow.exe") -ArgumentList $args
} elseif (Test-Path (Join-Path $TargetDir "flowork\flowork.exe")) {
    Copy-Item (Join-Path $TargetDir "flowork\flowork.exe") (Join-Path $TargetDir "x-flow.exe") -Force
    Start-Process (Join-Path $TargetDir "x-flow.exe") -ArgumentList $args
} else {
    Write-Error "[ERROR] Native x-flow.exe binary not found."
}
