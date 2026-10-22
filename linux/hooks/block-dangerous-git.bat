@echo off
rem Flowork OS Sovereign Git Safety Guardrail (Windows Native Batch)
rem Intercepts destructive git operations
setlocal enabledelayedexpansion

set "INPUT=%~1"
if "%INPUT%"=="" exit /b 0

rem Check explicit authorization override
echo !INPUT! | findstr /i /c:"--allow-destructive-git" /c:"--flowork-force-allow" >nul 2>&1
if !errorlevel! equ 0 exit /b 0

rem 1. Force push
echo !INPUT! | findstr /i /r /c:"git[ ]*push.*--force" /c:"git[ ]*push.* -f" /c:"git[ ]*push.*origin[ ]*+" /c:"git[ ]*push.*upstream[ ]*+" >nul 2>&1
if !errorlevel! equ 0 (
    echo BLOCKED: Git force push operation rejected by Flowork OS. Use --allow-destructive-git to override. 1>&2
    exit /b 2
)

rem 2. Hard reset
echo !INPUT! | findstr /i /c:"reset --hard" >nul 2>&1
if !errorlevel! equ 0 (
    echo BLOCKED: Git reset --hard rejected by Flowork OS. Use --allow-destructive-git to override. 1>&2
    exit /b 2
)

rem 3. Clean purge
echo !INPUT! | findstr /i /r /c:"clean[ ]*-f" /c:"clean[ ]*--force" >nul 2>&1
if !errorlevel! equ 0 (
    echo BLOCKED: Git clean -f rejected by Flowork OS. Use --allow-destructive-git to override. 1>&2
    exit /b 2
)

rem 4. Branch force delete
echo !INPUT! | findstr /i /r /c:"branch[ ]*-D" /c:"branch[ ]*--delete[ ]*--force" >nul 2>&1
if !errorlevel! equ 0 (
    echo BLOCKED: Git branch -D rejected by Flowork OS. Use --allow-destructive-git to override. 1>&2
    exit /b 2
)

rem 5. Discard changes
echo !INPUT! | findstr /i /r /c:"checkout[ ]*\." /c:"restore[ ]*\." >nul 2>&1
if !errorlevel! equ 0 (
    echo BLOCKED: Discarding changes ('checkout .' / 'restore .') rejected by Flowork OS. 1>&2
    exit /b 2
)

exit /b 0
