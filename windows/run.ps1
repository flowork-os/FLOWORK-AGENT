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

# 3. Launch native binary
if (Test-Path ".\x-flow.exe") {
    Start-Process ".\x-flow.exe" -ArgumentList $args
} elseif (Test-Path ".\x-flow") {
    Start-Process ".\x-flow" -ArgumentList $args
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
