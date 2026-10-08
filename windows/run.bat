@echo off
REM X-Flow Desktop Canvas Launcher — Windows Multi-OS Architecture
REM Co-authored-by: Flowork OS <agent@floworkos.com>

cd /d "%~dp0"
set SCRIPT_DIR=%~dp0

REM Flowork Sovereign Cloud-Native Self-Healer (GitHub Upstream Restore)
if not exist "%SCRIPT_DIR%connection" (
    echo [X-Flow] Vital ecosystem component(s) missing. Restoring from GitHub upstream...
    powershell -NoProfile -Command "$zip = Join-Path $env:TEMP 'flowork_agent.zip'; Invoke-WebRequest -Uri 'https://github.com/flowork-os/FLOWORK-AGENT/archive/refs/heads/main.zip' -OutFile $zip; Expand-Archive -Path $zip -DestinationPath (Join-Path $env:TEMP 'flw_ext') -Force; Copy-Item -Path (Join-Path $env:TEMP 'flw_ext\FLOWORK-AGENT-main\WINDOWS\*') -Destination '%SCRIPT_DIR%' -Recurse -Force; Remove-Item -Path (Join-Path $env:TEMP 'flw_ext') -Recurse -Force; Remove-Item -Path $zip -Force" >nul 2>&1
)

echo ========================================================
echo [X-Flow] Starting Sovereign Canvas Host on Windows...
echo ========================================================

REM 1. Set Portable Environment
set "FLOWORK_PORTABLE_ROOT=%SCRIPT_DIR%portable-home"
set "FLOWAI_CLI_HOME=%SCRIPT_DIR%portable-home"

REM Dynamic Portability Shield: purge stale cross-OS or non-existent workspace path
set "WS_CFG=%SCRIPT_DIR%.flowork\config\active_workspace.json"
if exist "%WS_CFG%" (
    findstr /C:"/home/" "%WS_CFG%" >nul 2>&1 && del /F /Q "%WS_CFG%" >nul 2>&1
    findstr /C:"/Users/" "%WS_CFG%" >nul 2>&1 && del /F /Q "%WS_CFG%" >nul 2>&1
)

REM 2. Terminate stale x-flow instances
taskkill /F /IM x-flow.exe >nul 2>&1

REM 2.5 Ensure Sovereign Router Switchboard (:9099) is running
if not exist "%SCRIPT_DIR%.FL_BIN" mkdir "%SCRIPT_DIR%.FL_BIN"
netstat -ano | findstr /C:":9099 " >nul 2>&1
if errorlevel 1 (
    where node >nul 2>&1
    if not errorlevel 1 (
        echo [X-Flow] Launching Sovereign Router Switchboard on port 9099...
        start /B "" node "%SCRIPT_DIR%connection\router.js" >> "%SCRIPT_DIR%.FL_BIN\conector.log" 2>&1
    )
)

REM 3. Check if x-flow.exe exists
if exist "x-flow.exe" (
    echo [X-Flow] Launching native Windows binary (x-flow.exe)...
    start "" "x-flow.exe" %*
) else if exist "flowork\flowork.exe" (
    echo [X-Flow] Copying native Windows binary from flowork\flowork.exe...
    copy /Y "flowork\flowork.exe" "x-flow.exe" >nul 2>&1
    start "" "x-flow.exe" %*
) else (
    echo [X-Flow] Binary not found. Building release binary with Cargo...
    if exist "core\Cargo.toml" (
        cargo build --release --manifest-path core\Cargo.toml
        copy /Y "core\target\release\x-flow.exe" ".\x-flow.exe"
        start "" "x-flow.exe" %*
    ) else if exist "..\core\Cargo.toml" (
        cargo build --release --manifest-path ..\core\Cargo.toml
        copy /Y "..\core\target\release\x-flow.exe" ".\x-flow.exe"
        start "" "x-flow.exe" %*
    ) else (
        echo [ERROR] Neither binary nor core source code found.
        pause
    )
)
