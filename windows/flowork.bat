@echo off
rem =============================================================================
rem 🚀 FLOWORK OS — ZERO-API SMART AUTONOMOUS LAUNCHER (WINDOWS)
rem Co-authored-by: Flowork OS <agent@floworkos.com>
rem =============================================================================
setlocal enabledelayedexpansion
title Flowork OS - Sovereign Canvas Host

rem 1. Dynamically resolve root script directory (Zero Hardcoded Path)
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

rem 2. Export Sovereign Environment Roots
set "FLOWORK_ENGINE_ROOT=%SCRIPT_DIR%"
set "FLOWORK_PORTABLE_ROOT=%SCRIPT_DIR%\portable-home"
set "FLOWAI_CLI_HOME=%SCRIPT_DIR%\portable-home"
set "PORTABLE_HOME=%SCRIPT_DIR%\portable-home"
set "NO_PROXY=127.0.0.1,localhost"
set "no_proxy=127.0.0.1,localhost"
set "PYTHONNOUSERSITE=1"

rem 2.5 Developer Circuit Breaker (dev.flowork / dev.flow with authenticated hash)
set "DEV_MODE_HASH=755edcc90dadcf187a487a608ad0d1140bd9313ddc3763c334e52518fddf15b4"
set "DEV_LOCKED=0"
for %%F in ("%SCRIPT_DIR%\dev.flowork" "%SCRIPT_DIR%\dev.flow" "%SCRIPT_DIR%\portable-home\dev.flowork" "%SCRIPT_DIR%\portable-home\.flowork\dev.flowork") do (
    if exist "%%~F" call :sub_check_dev "%%~F"
)
if "!DEV_LOCKED!"=="1" (
    echo [Flowork] 🛡️ Developer Mode Active [dev.flowork authenticated]. Auto-update is permanently disabled.
)

rem 3. Ensure Vital Directories Exist
if not exist "%SCRIPT_DIR%\portable-home\.flowork\logs" mkdir "%SCRIPT_DIR%\portable-home\.flowork\logs" 2>nul
if not exist "%SCRIPT_DIR%\portable-home\.flowork\chat_sessions" mkdir "%SCRIPT_DIR%\portable-home\.flowork\chat_sessions" 2>nul
if not exist "%SCRIPT_DIR%\.FL_BIN" mkdir "%SCRIPT_DIR%\.FL_BIN" 2>nul
if not exist "%SCRIPT_DIR%\.FL_BIN\scratch" mkdir "%SCRIPT_DIR%\.FL_BIN\scratch" 2>nul
if not exist "%SCRIPT_DIR%\swarmflow" mkdir "%SCRIPT_DIR%\swarmflow" 2>nul
if not exist "%SCRIPT_DIR%\swarmflow\active.json" echo {"activePresetId": "default"} > "%SCRIPT_DIR%\swarmflow\active.json"

rem 3.5 Purge Local Launcher to Enforce Cloudflare Edge Architecture
if exist "%SCRIPT_DIR%\canvas-ui\launcher.html" del /f /q "%SCRIPT_DIR%\canvas-ui\launcher.html" 2>nul
if exist "%SCRIPT_DIR%\canvas-ui\launcher" rmdir /s /q "%SCRIPT_DIR%\canvas-ui\launcher" 2>nul

rem 3.6 Inject Portable Runtimes into PATH (Zero-Dependency Plug and Play)
if exist "%SCRIPT_DIR%\runtimes\node" set "PATH=%SCRIPT_DIR%\runtimes\node;!PATH!"
if exist "%SCRIPT_DIR%\runtimes\windows" set "PATH=%SCRIPT_DIR%\runtimes\windows;!PATH!"
if exist "%SCRIPT_DIR%\runtimes\python" set "PATH=%SCRIPT_DIR%\runtimes\python;!PATH!"
if exist "%SCRIPT_DIR%\portable-home\bin" set "PATH=%SCRIPT_DIR%\portable-home\bin;!PATH!"

rem 3.6.0 Autonomous Neural ONNX Model Provisioning (FastEmbed / Semantic Search)
set "MODELS_DIR=%SCRIPT_DIR%\portable-home\.flowork\models"
set "MODEL_TARGET=%MODELS_DIR%\models--Xenova--bge-small-en-v1.5"
set "MODEL_ZIP_URL=https://github.com/flowork-os/FLOWORK-AGENT/releases/download/v1.0.0/Flowork-Model-bge-small.zip"
set "TMP_MODEL_ZIP=%MODELS_DIR%\temp_model.zip"

if not exist "%MODEL_TARGET%\snapshots\ea104dacec62c0de699686887e3f920caeb4f3e3\onnx\model.onnx" (
    echo [Flowork] 🧠 Neural embedding model not found. Fetching official ONNX package from GitHub Release...
    if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%" 2>nul
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%MODEL_ZIP_URL%', '%TMP_MODEL_ZIP%'); $h = (Get-FileHash -Path '%TMP_MODEL_ZIP%' -Algorithm SHA256).Hash.ToLower(); if ($h -eq '06424e1e78f22a4436c6df3f00e87238ee57f8e90a8230067b7a7b31e4e4b796') { Expand-Archive -Path '%TMP_MODEL_ZIP%' -DestinationPath '%MODELS_DIR%' -Force; echo '[Flowork] ✅ Neural ONNX embedding model installed successfully (100%% offline ready).' } else { echo '[Flowork] ⚠️ Model hash mismatch; skipping unpack.' }; Remove-Item '%TMP_MODEL_ZIP%' -Force -ErrorAction SilentlyContinue"
)

rem 3.6.1 Locate or Auto-Provision Node.js Runtime for Universal Switchboard Router
set "NODE_BIN="
if exist "%SCRIPT_DIR%\runtimes\node\node.exe" (
    set "NODE_BIN=%SCRIPT_DIR%\runtimes\node\node.exe"
) else if exist "%SCRIPT_DIR%\runtimes\windows\node.exe" (
    set "NODE_BIN=%SCRIPT_DIR%\runtimes\windows\node.exe"
) else (
    where node.exe >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%p in ('where node.exe 2^>nul') do (
            if "!NODE_BIN!"=="" set "NODE_BIN=%%p"
        )
    )
)

if "!NODE_BIN!"=="" (
    echo [Flowork] 📥 Auto-fetching portable Node.js runtime for Windows...
    if not exist "%SCRIPT_DIR%\runtimes\windows" mkdir "%SCRIPT_DIR%\runtimes\windows" 2>nul
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.18.0/win-x64/node.exe' -OutFile '%SCRIPT_DIR%\runtimes\windows\node.exe' -UseBasicParsing" >nul 2>&1
    if exist "%SCRIPT_DIR%\runtimes\windows\node.exe" (
        set "NODE_BIN=%SCRIPT_DIR%\runtimes\windows\node.exe"
    )
)

rem 3.7 Sovereign Port Guardian (Auto-Purge Zombie Processes on Sacred Ports 9099 and 19890)
taskkill /F /IM "flowork-connector.exe" >nul 2>&1

rem Scan and terminate zombie processes listening on sacred port 9099
for /f "tokens=5" %%a in ('netstat -a -n -o 2^>nul ^| findstr ":9099 " ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" taskkill /F /PID %%a >nul 2>&1
)

rem Scan and terminate zombie processes listening on sacred port 19890
for /f "tokens=5" %%a in ('netstat -a -n -o 2^>nul ^| findstr ":19890 " ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" taskkill /F /PID %%a >nul 2>&1
)

rem Clean stale browser singleton locks safely
if exist "%SCRIPT_DIR%\portable-home\.flowork\browser-profile\Singleton*" (
    del /f /q "%SCRIPT_DIR%\portable-home\.flowork\browser-profile\Singleton*" >nul 2>&1
)

rem 3.8 Auto-Start Universal Router Switchboard on Sacred Port 9099
set "ROUTER_BIN="
if exist "%SCRIPT_DIR%\flowork\flowork-connector.exe" (
    set "ROUTER_BIN=%SCRIPT_DIR%\flowork\flowork-connector.exe"
) else if exist "%SCRIPT_DIR%\flowork-connector.exe" (
    set "ROUTER_BIN=%SCRIPT_DIR%\flowork-connector.exe"
)

set "ROUTER_JS="
if exist "%SCRIPT_DIR%\connection\router.js" (
    set "ROUTER_JS=%SCRIPT_DIR%\connection\router.js"
) else if exist "%SCRIPT_DIR%\connector\router.js" (
    set "ROUTER_JS=%SCRIPT_DIR%\connector\router.js"
)

set "LOG_OUT=%SCRIPT_DIR%\portable-home\.flowork\logs\connector.log"
set "LOG_ERR=%SCRIPT_DIR%\portable-home\.flowork\logs\connector_err.log"

if not "!ROUTER_BIN!"=="" (
    echo [Flowork] ⚡ Starting Native Router Connector on port 9099...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '!ROUTER_BIN!' -WindowStyle Hidden -RedirectStandardOutput '%LOG_OUT%' -RedirectStandardError '%LOG_ERR%'" >nul 2>&1
    if errorlevel 1 (
        start "" /B cmd /c ""!ROUTER_BIN!" >> "%LOG_OUT%" 2>&1"
    )
) else if not "!NODE_BIN!"=="" if not "!ROUTER_JS!"=="" (
    echo [Flowork] 🚀 Starting Universal Router Switchboard on port 9099 (Node.js fallback)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%NODE_BIN%' -ArgumentList '"%ROUTER_JS%"' -WindowStyle Hidden -RedirectStandardOutput '%LOG_OUT%' -RedirectStandardError '%LOG_ERR%'" >nul 2>&1
    if errorlevel 1 (
        start "" /B cmd /c ""%NODE_BIN%" "%ROUTER_JS%" >> "%LOG_OUT%" 2>&1"
    )
)

    rem Verify port 9099 is listening
    set "ROUTER_ACTIVE=0"
    for /L %%w in (1,1,6) do (
        if "!ROUTER_ACTIVE!"=="0" (
            netstat -a -n -o 2^>nul | findstr ":9099 " | findstr "LISTENING" >nul 2>&1
            if not errorlevel 1 (
                set "ROUTER_ACTIVE=1"
            ) else (
                ping -n 2 127.0.0.1 >nul 2>&1
            )
        )
    )
    if "!ROUTER_ACTIVE!"=="1" (
        echo [Flowork] ✅ Sovereign Router Switchboard active on port 9099.
    ) else (
        echo [Flowork] ℹ️ Notice: Router Switchboard initializing in background.
    )
) else (
    echo [Flowork] ⚠️ Warning: Node.js runtime or router.js not found. Router switchboard bypassed.
)

rem 4. Auto-detect GitHub Token if akungithub exists
if exist "%SCRIPT_DIR%\akungithub" (
    set /p GITHUB_TOKEN=<"%SCRIPT_DIR%\akungithub"
    set "GITHUB_TOKEN=!GITHUB_TOKEN: =!"
)

rem 5. Locate Flowork Executable Binary
set "TARGET_EXE="
if exist "%SCRIPT_DIR%\flowork\flowork.exe" (
    set "TARGET_EXE=%SCRIPT_DIR%\flowork\flowork.exe"
) else if exist "%SCRIPT_DIR%\flowork.exe" (
    set "TARGET_EXE=%SCRIPT_DIR%\flowork.exe"
) else if exist "%SCRIPT_DIR%\flowork\x-flow.exe" (
    set "TARGET_EXE=%SCRIPT_DIR%\flowork\x-flow.exe"
) else if exist "%SCRIPT_DIR%\x-flow.exe" (
    set "TARGET_EXE=%SCRIPT_DIR%\x-flow.exe"
)

if "!TARGET_EXE!"=="" (
    echo [Flowork:ERROR] Cannot find runnable Flowork Windows binary flowork.exe or x-flow.exe in:
    echo   - %SCRIPT_DIR%\flowork\flowork.exe
    echo   - %SCRIPT_DIR%\flowork.exe
    echo.
    echo Please ensure the release package contains flowork.exe.
    pause
    exit /b 1
)

echo [Flowork OS] 🚀 Starting Sovereign Canvas Host on Windows...
echo [Flowork OS] 📁 Root Directory: %SCRIPT_DIR%
echo [Flowork OS] ⚡ Binary Target: !TARGET_EXE!
echo.

rem 6. Launch Flowork Core Engine
"!TARGET_EXE!" %*
set "EXIT_CODE=!ERRORLEVEL!"

if not "!EXIT_CODE!"=="0" (
    echo.
    echo [Flowork OS] Process terminated with code !EXIT_CODE!.
)
exit /b !EXIT_CODE!

rem =============================================================================
rem SUBROUTINES
rem =============================================================================
:sub_check_dev
set "DF_PATH=%~1"
set "DF_VAL="
set /p DF_VAL=<"%DF_PATH%"
if "%DF_VAL%"=="Aola-#1987" (
    set "DEV_LOCKED=1"
    goto :eof
)
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "$t = (Get-Content -LiteralPath '%DF_PATH%' -Raw).Trim(); $b = [System.Text.Encoding]::UTF8.GetBytes($t); $s = [System.Security.Cryptography.SHA256]::Create(); [System.BitConverter]::ToString($s.ComputeHash($b)).Replace('-','').ToLower()" 2^>nul`) do (
    if "%%H"=="%DEV_MODE_HASH%" set "DEV_LOCKED=1"
)
goto :eof
