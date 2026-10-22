@echo off
rem =============================================================================
rem 🚀 FLOWORK OS — RUNTIME LAUNCHER & CANVAS HOST (WINDOWS)
rem Co-authored-by: Flowork OS <agent@floworkos.com>
rem =============================================================================
setlocal enabledelayedexpansion
title Flowork OS - Sovereign Canvas Host

rem 1. Dynamically resolve root script directory (Zero Hardcoded Path)
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

rem 2. Delegate directly to sovereign launcher
if exist "%SCRIPT_DIR%\flowork.bat" (
    call "%SCRIPT_DIR%\flowork.bat" %*
    exit /b !ERRORLEVEL!
)

rem Fallback direct execution if flowork.bat is missing
set "FLOWORK_ENGINE_ROOT=%SCRIPT_DIR%"
set "FLOWORK_PORTABLE_ROOT=%SCRIPT_DIR%\portable-home"
set "FLOWAI_CLI_HOME=%SCRIPT_DIR%\portable-home"
set "PORTABLE_HOME=%SCRIPT_DIR%\portable-home"
set "NO_PROXY=127.0.0.1,localhost"
set "no_proxy=127.0.0.1,localhost"

taskkill /F /IM "flowork-connector.exe" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -a -n -o 2^>nul ^| findstr ":9099 :19890" ^| findstr "LISTENING"') do (
    if not "%%a"=="" if not "%%a"=="0" taskkill /F /PID %%a >nul 2>&1
)

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
    echo [Flowork:ERROR] Cannot find runnable Flowork Windows binary flowork.exe or x-flow.exe
    pause
    exit /b 1
)

"!TARGET_EXE!" %*
exit /b !ERRORLEVEL!
