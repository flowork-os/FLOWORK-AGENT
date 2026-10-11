@echo off
REM =============================================================================
REM 🚀 FLOWORK OS — ZERO-API SMART AUTONOMOUS LAUNCHER & SELF-UPDATER (WINDOWS)
REM Target Directory: C:\flowork
REM Co-authored-by: Flowork OS <agent@floworkos.com>
REM =============================================================================
setlocal enabledelayedexpansion

set "TARGET_DIR=C:\flowork"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
cd /d "%TARGET_DIR%"

REM 1. Ensure Node.js runtime is ready
set "NODE_BIN=node"
where node >nul 2>&1
if errorlevel 1 goto :FIND_NODE
if exist "%TARGET_DIR%\node\node.exe" set "NODE_BIN=%TARGET_DIR%\node\node.exe"
goto :CHECK_UPDATE

:FIND_NODE
if exist "%TARGET_DIR%\node\node.exe" (
    set "NODE_BIN=%TARGET_DIR%\node\node.exe"
    goto :CHECK_UPDATE
)
if exist "C:\Program Files\nodejs\node.exe" (
    set "NODE_BIN=C:\Program Files\nodejs\node.exe"
    goto :CHECK_UPDATE
)
echo [Flowork] ⚡ Node.js not detected. Auto-installing standalone runtime into %TARGET_DIR%\node...
if not exist "%TARGET_DIR%\node" mkdir "%TARGET_DIR%\node"
powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://nodejs.org/dist/v20.18.0/win-x64/node.exe', '%TARGET_DIR%\node\node.exe'); Write-Host '[Flowork] ✅ Standalone Node.js runtime ready.' -ForegroundColor Green } catch {}"
if exist "%TARGET_DIR%\node\node.exe" set "NODE_BIN=%TARGET_DIR%\node\node.exe"

:CHECK_UPDATE
set "UPSTREAM_REPO=flowork-os/FLOWORK-WINDOWS"
set "RAW_VERSION_URL=https://raw.githubusercontent.com/%UPSTREAM_REPO%/main/VERSION"
set "ARCHIVE_URL=https://codeload.github.com/%UPSTREAM_REPO%/zip/refs/heads/main"
set "LOCAL_VER_FILE=%TARGET_DIR%\VERSION"

set "LOCAL_VER="
if exist "%LOCAL_VER_FILE%" (
    set /p LOCAL_VER=<"%LOCAL_VER_FILE%"
)

REM 2. Fast Sentinel Update Check via PowerShell (Max 2s timeout, Zero-API)
set "REMOTE_VER="
for /f "usebackq delims=" %%v in (`powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri '%RAW_VERSION_URL%' -TimeoutSec 2 -UseBasicParsing).Content.Trim() } catch {}"`) do (
    set "REMOTE_VER=%%v"
)

set "NEEDS_UPDATE=0"
if not exist "%TARGET_DIR%\run.bat" set "NEEDS_UPDATE=1"
if not exist "%TARGET_DIR%\connection\router.js" set "NEEDS_UPDATE=1"
if not exist "%TARGET_DIR%\Persona" set "NEEDS_UPDATE=1"
if not exist "%TARGET_DIR%\x-flow.exe" set "NEEDS_UPDATE=1"
if "%LOCAL_VER%"=="" set "NEEDS_UPDATE=1"
if defined REMOTE_VER (
    if not "%REMOTE_VER%"=="%LOCAL_VER%" set "NEEDS_UPDATE=1"
)

if "%NEEDS_UPDATE%"=="0" goto :RUN_ENGINE

echo [Flowork] ⚡ Synchronizing Flowork OS from upstream into %TARGET_DIR%...
powershell -NoProfile -Command "$zip = Join-Path $env:TEMP 'flowork_update.zip'; $ext = Join-Path $env:TEMP 'flowork_ext'; try { Invoke-WebRequest -Uri '%ARCHIVE_URL%' -OutFile $zip -UseBasicParsing; Expand-Archive -Path $zip -DestinationPath $ext -Force; $src = if (Test-Path (Join-Path $ext 'FLOWORK-WINDOWS-main')) { Join-Path $ext 'FLOWORK-WINDOWS-main' } else { Join-Path $ext 'FLOWORK-AGENT-main\windows' }; if (Test-Path $src) { Get-ChildItem -Path $src -Recurse | Where-Object { $_.FullName -notmatch 'portable-home\\\.flowork' } | ForEach-Object { $rel = $_.FullName.Substring($src.Length).TrimStart('\'); $dest = Join-Path '%TARGET_DIR%' $rel; if ($_.PSIsContainer) { [System.IO.Directory]::CreateDirectory($dest) | Out-Null } else { Copy-Item -Path $_.FullName -Destination $dest -Force } } }; Remove-Item -Path $ext -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -Path $zip -Force -ErrorAction SilentlyContinue; Write-Host '[Flowork] ✅ Successfully synchronized.' -ForegroundColor Green; } catch { Write-Warning '[Flowork] ⚠️ Update notice or offline mode.' }"
if defined REMOTE_VER (
    echo %REMOTE_VER%> "%LOCAL_VER_FILE%"
)

:RUN_ENGINE
if exist "%TARGET_DIR%\run.bat" (
    call "%TARGET_DIR%\run.bat" %*
) else if exist "%TARGET_DIR%\x-flow.exe" (
    "%TARGET_DIR%\x-flow.exe" %*
) else (
    echo [Flowork:ERROR] Cannot find runnable Flowork engine in %TARGET_DIR%
    pause
)
