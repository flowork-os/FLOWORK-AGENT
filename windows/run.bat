@echo off
REM =============================================================================
REM 🚀 FLOWORK OS — NATIVE CANVAS LAUNCHER & POLYGLOT ENGINE (WINDOWS)
REM Target: C:\flowork
REM Co-authored-by: Flowork OS <agent@floworkos.com>
REM =============================================================================

set "SCRIPT_DIR=C:\flowork"
cd /d "%SCRIPT_DIR%"

REM 1. Detect or Fallback Node.js Runtime
set "NODE_BIN=node"
where node >nul 2>&1
if errorlevel 1 goto :FIND_NODE
if exist "%SCRIPT_DIR%\node\node.exe" set "NODE_BIN=%SCRIPT_DIR%\node\node.exe"
goto :NODE_DONE

:FIND_NODE
if exist "%SCRIPT_DIR%\node\node.exe" (
    set "NODE_BIN=%SCRIPT_DIR%\node\node.exe"
    goto :NODE_DONE
)
if exist "C:\Program Files\nodejs\node.exe" (
    set "NODE_BIN=C:\Program Files\nodejs\node.exe"
    goto :NODE_DONE
)
echo [X-Flow] Node.js runtime not found. Fetching standalone runtime into %SCRIPT_DIR%\node...
if not exist "%SCRIPT_DIR%\node" mkdir "%SCRIPT_DIR%\node"
powershell -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://nodejs.org/dist/v20.18.0/win-x64/node.exe', '%SCRIPT_DIR%\node\node.exe') } catch {}"
if exist "%SCRIPT_DIR%\node\node.exe" set "NODE_BIN=%SCRIPT_DIR%\node\node.exe"

:NODE_DONE
echo ========================================================
echo [X-Flow] Starting Sovereign Canvas Host on Windows...
echo [X-Flow] Target Directory: %SCRIPT_DIR%
echo ========================================================

REM 2. Set Portable Environment
set "FLOWORK_PORTABLE_ROOT=%SCRIPT_DIR%\portable-home"
set "FLOWAI_CLI_HOME=%SCRIPT_DIR%\portable-home"

REM Dynamic Portability Shield: purge stale cross-OS or non-existent workspace path
set "WS_CFG=%SCRIPT_DIR%\.flowork\config\active_workspace.json"
if exist "%WS_CFG%" (
    findstr /C:"/home/" "%WS_CFG%" >nul 2>&1 && del /F /Q "%WS_CFG%" >nul 2>&1
    findstr /C:"/Users/" "%WS_CFG%" >nul 2>&1 && del /F /Q "%WS_CFG%" >nul 2>&1
)

REM 3. Terminate stale x-flow instances
taskkill /F /IM x-flow.exe >nul 2>&1 || (call )

REM 4. Ensure Sovereign Router Switchboard (:9099) is running
if not exist "%SCRIPT_DIR%\.FL_BIN" mkdir "%SCRIPT_DIR%\.FL_BIN"
netstat -ano | findstr /C:":9099 " >nul 2>&1
if not errorlevel 1 goto :ROUTER_OK

echo [X-Flow] Launching Sovereign Router Switchboard on port 9099...
start /MIN "Flowork Router (:9099)" "%NODE_BIN%" "%SCRIPT_DIR%\connection\router.js"
timeout /t 2 /nobreak >nul 2>&1

:ROUTER_OK
REM 5. Native binary x-flow will launch Canvas UI in standalone App Mode
echo [X-Flow] Sovereign Canvas Host ready on http://127.0.0.1:19890

REM 6. Launch native x-flow binary in foreground
if exist "%SCRIPT_DIR%\x-flow.exe" goto :RUN_XFLOW
if exist "%SCRIPT_DIR%\flowork\flowork.exe" goto :COPY_XFLOW

echo [ERROR] Neither x-flow.exe nor core binary found in %SCRIPT_DIR%.
pause
exit /b 1

:COPY_XFLOW
echo [X-Flow] Copying native Windows binary from flowork\flowork.exe...
copy /Y "%SCRIPT_DIR%\flowork\flowork.exe" "%SCRIPT_DIR%\x-flow.exe" >nul 2>&1

:RUN_XFLOW
echo [X-Flow] Launching native Windows binary: x-flow.exe
"%SCRIPT_DIR%\x-flow.exe" %*
