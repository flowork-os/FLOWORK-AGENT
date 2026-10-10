@echo off
REM =============================================================================
REM 🚀 FLOWORK OS — ZERO-API SMART AUTONOMOUS LAUNCHER & SELF-UPDATER (WINDOWS)
REM Co-authored-by: Flowork OS <agent@floworkos.com>
REM =============================================================================
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "UPSTREAM_REPO=flowork-os/FLOWORK-AGENT"
set "RAW_VERSION_URL=https://raw.githubusercontent.com/%UPSTREAM_REPO%/main/WINDOWS/VERSION"
set "ARCHIVE_URL=https://github.com/%UPSTREAM_REPO%/archive/refs/heads/main.zip"
set "LOCAL_VER_FILE=%SCRIPT_DIR%VERSION"

set "LOCAL_VER="
if exist "%LOCAL_VER_FILE%" (
    set /p LOCAL_VER=<"%LOCAL_VER_FILE%"
)

REM 1. Fast Sentinel Update Check via PowerShell (Max 2s timeout, Zero-API)
set "REMOTE_VER="
for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri '%RAW_VERSION_URL%' -TimeoutSec 2 -UseBasicParsing).Content.Trim() } catch {}"`) do (
    set "REMOTE_VER=%%v"
)

set "NEEDS_UPDATE=0"
if not exist "%SCRIPT_DIR%run.bat" set "NEEDS_UPDATE=1"
if not exist "%SCRIPT_DIR%connection" set "NEEDS_UPDATE=1"
if not exist "%SCRIPT_DIR%Persona" set "NEEDS_UPDATE=1"
if "%LOCAL_VER%"=="" set "NEEDS_UPDATE=1"
if defined REMOTE_VER (
    if not "%REMOTE_VER%"=="%LOCAL_VER%" set "NEEDS_UPDATE=1"
)

REM 2. Safe Download & Update (Never touches portable-home/.flowork)
if "%NEEDS_UPDATE%"=="1" (
    echo [Flowork] ⚡ Synchronizing Flowork OS from upstream...
    powershell -NoProfile -Command ^
        "$zip = Join-Path $env:TEMP 'flowork_update.zip'; ^
        $ext = Join-Path $env:TEMP 'flowork_ext'; ^
        try { ^
            Invoke-WebRequest -Uri '%ARCHIVE_URL%' -OutFile $zip -UseBasicParsing; ^
            Expand-Archive -Path $zip -DestinationPath $ext -Force; ^
            $src = Join-Path $ext 'FLOWORK-AGENT-main\WINDOWS'; ^
            if (Test-Path $src) { ^
                Get-ChildItem -Path $src -Recurse | Where-Object { $_.FullName -notmatch 'portable-home\\\.flowork' } | ForEach-Object { ^
                    $rel = $_.FullName.Substring($src.Length).TrimStart('\'); ^
                    $dest = Join-Path '%SCRIPT_DIR%' $rel; ^
                    if ($_.PSIsContainer) { [System.IO.Directory]::CreateDirectory($dest) | Out-Null } ^
                    else { Copy-Item -Path $_.FullName -Destination $dest -Force } ^
                }; ^
            }; ^
            Remove-Item -Path $ext -Recurse -Force -ErrorAction SilentlyContinue; ^
            Remove-Item -Path $zip -Force -ErrorAction SilentlyContinue; ^
            Write-Host '[Flowork] ✅ Successfully synchronized.' -ForegroundColor Green; ^
        } catch { Write-Warning '[Flowork] ⚠️ Update notice or offline mode.' }"
    if defined REMOTE_VER (
        echo %REMOTE_VER%> "%LOCAL_VER_FILE%"
    )
)

REM 3. Launch Native Engine
if exist "%SCRIPT_DIR%run.bat" (
    call "%SCRIPT_DIR%run.bat" %*
) else if exist "%SCRIPT_DIR%x-flow.exe" (
    start "" "%SCRIPT_DIR%x-flow.exe" %*
) else (
    echo [Flowork:ERROR] Cannot find runnable Flowork engine in %SCRIPT_DIR%
    pause
)
