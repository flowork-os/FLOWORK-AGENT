@echo off
rem =============================================================================
rem 🚀 FLOWORK OS — OFFICIAL WINDOWS DOUBLE-CLICK INSTALLER BOOTSTRAPPER
rem Co-authored-by: Flowork OS <agent@floworkos.com>
rem =============================================================================
title Flowork OS Installer
cd /d "%~dp0"

echo ============================================================
echo ⚡ Flowork OS Autonomous Installer (Windows)
echo ============================================================
echo.
echo Launching PowerShell autonomous installer...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.ps1 | iex"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Installation failed or was interrupted.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
