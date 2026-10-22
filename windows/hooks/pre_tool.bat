@echo off
rem Flowork OS Sovereign Pre-Tool Hook (Windows Native Batch)
rem Intercepts destructive commands and git operations
setlocal enabledelayedexpansion

set "PAYLOAD=%~1"
if "%PAYLOAD%"=="" exit /b 0

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

rem 1. Check for destructive disk wipe patterns (format, rd /s /q c:\, etc.)
echo !PAYLOAD! | findstr /i /r /c:"format[ ]*[a-z]:" /c:"rd[ ]*/s[ ]*/q[ ]*[a-z]:\\" /c:"rmdir[ ]*/s[ ]*/q[ ]*[a-z]:\\" >nul 2>&1
if !errorlevel! equ 0 (
    echo BLOCKED by pre_tool hook: Catastrophic disk destruction command detected! 1>&2
    exit /b 2
)

rem 2. Delegate to git guardrail if git command is present
echo !PAYLOAD! | findstr /i "git" >nul 2>&1
if !errorlevel! equ 0 (
    if exist "%SCRIPT_DIR%\block-dangerous-git.bat" (
        call "%SCRIPT_DIR%\block-dangerous-git.bat" "!PAYLOAD!"
        if !errorlevel! neq 0 exit /b !errorlevel!
    )
)

exit /b 0
