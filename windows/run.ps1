# X-Flow Desktop Canvas Launcher — Windows PowerShell Multi-OS Architecture
# Co-authored-by: Flowork OS <agent@floworkos.com>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Flowork Sovereign Cloud-Native Self-Healer (GitHub Upstream Restore)
$ConectionDir = Join-Path $ScriptDir "connection"
$CanvasDir = Join-Path $ScriptDir "canvas-ui"
if ((-not (Test-Path $ConectionDir)) -or (-not (Test-Path $CanvasDir))) {
    Write-Host "[X-Flow] 🌐 Vital ecosystem component(s) missing. Restoring from GitHub upstream..." -ForegroundColor Cyan
    $zipPath = Join-Path $env:TEMP "flowork_agent.zip"
    $extPath = Join-Path $env:TEMP "flw_ext"
    try {
        Invoke-WebRequest -Uri "https://github.com/flowork-os/FLOWORK-AGENT/archive/refs/heads/main.zip" -OutFile $zipPath
        Expand-Archive -Path $zipPath -DestinationPath $extPath -Force
        Copy-Item -Path (Join-Path $extPath "FLOWORK-AGENT-main\WINDOWS\*") -Destination $ScriptDir -Recurse -Force
        Remove-Item -Path $extPath -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
        Write-Host "[X-Flow] ✅ Ecosystem components restored successfully." -ForegroundColor Green
    } catch {
        Write-Warning "[X-Flow] Cloud self-healing notice: $_"
    }
}

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "[X-Flow] Starting Sovereign Canvas Host (PowerShell)..." -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Set Portable Environment
$env:FLOWORK_PORTABLE_ROOT = Join-Path $ScriptDir "portable-home"
$env:FLOWAI_CLI_HOME = Join-Path $ScriptDir "portable-home"

# Dynamic Portability Shield: purge stale cross-OS or non-existent workspace path
$WsCfg = Join-Path $ScriptDir ".flowork\config\active_workspace.json"
if (Test-Path $WsCfg) {
    try {
        $cfg = Get-Content $WsCfg -Raw | ConvertFrom-Json
        if ($cfg.path -and (-not (Test-Path $cfg.path) -or $cfg.path.StartsWith("/"))) {
            Remove-Item $WsCfg -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

# 2. Kill previous stale instances if running
Get-Process -Name "x-flow" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# 2.5 Ensure Sovereign Router Switchboard (:9099) is running
$flBin = Join-Path $ScriptDir ".FL_BIN"
if (-not (Test-Path $flBin)) { New-Item -ItemType Directory -Path $flBin -Force | Out-Null }

$NodeDir = Join-Path $ScriptDir "node"
if (Test-Path (Join-Path $NodeDir "node.exe")) {
    $env:PATH = "$NodeDir;" + $env:PATH
} elseif (Test-Path "C:\flowork\node\node.exe") {
    $env:PATH = "C:\flowork\node;" + $env:PATH
} else {
    if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
        Write-Host "[X-Flow] ⚡ Node.js not found in PATH. Auto-installing portable Node.js LTS..." -ForegroundColor Yellow
        $nodeZip = Join-Path $env:TEMP "node_temp.zip"
        $nodeExt = Join-Path $env:TEMP "node_temp_ext"
        try {
            Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip" -OutFile $nodeZip -UseBasicParsing
            Expand-Archive -Path $nodeZip -DestinationPath $nodeExt -Force
            $srcFolder = Get-ChildItem -Path $nodeExt -Directory | Select-Object -First 1
            Move-Item -Path $srcFolder.FullName -Destination $NodeDir -Force
            Remove-Item -Path $nodeExt -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $nodeZip -Force -ErrorAction SilentlyContinue
            $env:PATH = "$NodeDir;" + $env:PATH
            Write-Host "[X-Flow] ✅ Portable Node.js installed successfully." -ForegroundColor Green
        } catch {
            Write-Warning "[X-Flow] Could not auto-download Node.js: $_"
        }
    }
}

$routerPortListening = $false
try {
    $conns = Get-NetTCPConnection -LocalPort 9099 -ErrorAction SilentlyContinue
    if ($conns) { $routerPortListening = $true }
} catch {}
if (-not $routerPortListening) {
    if (Get-Command "node" -ErrorAction SilentlyContinue) {
        Write-Host "[X-Flow] Launching Sovereign Router Switchboard on port 9099..." -ForegroundColor Cyan
        Start-Process "node" -ArgumentList @((Join-Path $ScriptDir "connection\router.js")) -WorkingDirectory $ScriptDir -WindowStyle Hidden
    }
}

# 3. Launch native binary
if (Test-Path ".\x-flow.exe") {
    Start-Process ".\x-flow.exe" -ArgumentList $args
} elseif (Test-Path "flowork\flowork.exe") {
    Write-Host "[X-Flow] Copying native Windows binary from flowork\flowork.exe..." -ForegroundColor Cyan
    Copy-Item "flowork\flowork.exe" ".\x-flow.exe" -Force
    Start-Process ".\x-flow.exe" -ArgumentList $args
} else {
    Write-Host "[X-Flow] Binary not found. Building release binary with Cargo..." -ForegroundColor Yellow
    if (Test-Path "core\Cargo.toml") {
        cargo build --release --manifest-path core\Cargo.toml
        Copy-Item "core\target\release\x-flow.exe" ".\x-flow.exe" -Force
        Start-Process ".\x-flow.exe" -ArgumentList $args
    } elseif (Test-Path "..\core\Cargo.toml") {
        cargo build --release --manifest-path ..\core\Cargo.toml
        Copy-Item "..\core\target\release\x-flow.exe" ".\x-flow.exe" -Force
        Start-Process ".\x-flow.exe" -ArgumentList $args
    } else {
        Write-Error "[ERROR] Neither binary nor core source code found."
    }
}
