<#
.SYNOPSIS
    Flowork OS — Official 1-Line Autonomous Installer (Windows)
.DESCRIPTION
    Installs Flowork OS into C:\flowork (with smart fallback to %USERPROFILE%\flowork),
    extracts official components, registers Desktop & Start Menu shortcuts, and launches the runtime.
.EXAMPLE
    irm https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$Repo = "flowork-os/FLOWORK-AGENT"
$Branch = "main"
$ArchiveUrl = "https://github.com/$Repo/archive/refs/heads/$Branch.zip"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "⚡ Flowork OS Autonomous Installer (Windows)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Dynamic Installation Directory Resolution (Custom / Portable / C:\flowork with non-admin fallback)
if ($env:FLOWORK_INSTALL_DIR) {
    $InstallDir = $env:FLOWORK_INSTALL_DIR
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }
} elseif ($args.Count -gt 0 -and $args[0]) {
    $InstallDir = $args[0]
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }
} else {
    $PrimaryDir = "C:\flowork"
    $FallbackDir = Join-Path $env:USERPROFILE "flowork"
    $InstallDir = $PrimaryDir

    $CanWriteC = $false
    try {
        if (-not (Test-Path $PrimaryDir)) {
            New-Item -ItemType Directory -Path $PrimaryDir -Force -ErrorAction Stop | Out-Null
        }
        $TestFile = Join-Path $PrimaryDir ".perm_test_$PID.tmp"
        [System.IO.File]::WriteAllText($TestFile, "test")
        Remove-Item $TestFile -Force -ErrorAction SilentlyContinue
        $CanWriteC = $true
    } catch {
        $CanWriteC = $false
    }

    if (-not $CanWriteC) {
        Write-Host "[Flowork] ℹ️ Standard user permissions detected; targeting: $FallbackDir" -ForegroundColor Yellow
        $InstallDir = $FallbackDir
        if (-not (Test-Path $InstallDir)) {
            New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        }
    } else {
        Write-Host "[Flowork] ✅ Administrator / System write access verified: $PrimaryDir" -ForegroundColor Green
    }
}

Write-Host "📁 Target Directory: $InstallDir" -ForegroundColor Green
Set-Location $InstallDir

# 2. Download Official Release Zip (Precompiled Standalone Bundle)
$ZipPath = Join-Path $env:TEMP "flowork_release_$PID.zip"
$ReleaseBundleUrl = "https://github.com/$Repo/releases/latest/download/Flowork-Agent-Windows-x64.zip"
Write-Host "📥 Fetching Flowork OS official release bundle from GitHub (Flowork-Agent-Windows-x64.zip)..." -ForegroundColor Cyan

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$DownloadedBundle = $false
try {
    Invoke-WebRequest -Uri $ReleaseBundleUrl -OutFile $ZipPath -UseBasicParsing
    $DownloadedBundle = $true
} catch {
    Write-Host "[Flowork] ⚠️ Release bundle download failed, falling back to repository archive..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $ArchiveUrl -OutFile $ZipPath -UseBasicParsing
}

# 3. Extract Components to Target Directory
Write-Host "📦 Extracting release components..." -ForegroundColor Cyan
$ExtractTemp = Join-Path $env:TEMP "flowork_extract_$PID"
if (Test-Path $ExtractTemp) { Remove-Item $ExtractTemp -Recurse -Force }
Expand-Archive -Path $ZipPath -DestinationPath $ExtractTemp -Force

if ($DownloadedBundle) {
    $SourceWindowsDir = Join-Path $ExtractTemp "flowork"
    if (-not (Test-Path $SourceWindowsDir)) { $SourceWindowsDir = $ExtractTemp }
} else {
    $SourceWindowsDir = Join-Path $ExtractTemp "FLOWORK-AGENT-$Branch\windows"
}

if (Test-Path $SourceWindowsDir) {
    Copy-Item -Path "$SourceWindowsDir\*" -Destination $InstallDir -Recurse -Force
} else {
    Write-Host "❌ Failed to locate windows components in archive." -ForegroundColor Red
    exit 1
}

# Clean temporary archives
Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
Remove-Item $ExtractTemp -Recurse -Force -ErrorAction SilentlyContinue

# 4. Autonomous Portable Runtimes Verification & Provisioning
$RuntimeSetupScript = Join-Path $InstallDir "runtimes\windows\setup_runtimes.ps1"
if (Test-Path $RuntimeSetupScript) {
    Write-Host "[Flowork] ⚡ Initializing Autonomous Portable Runtime Layer..." -ForegroundColor Cyan
    try {
        & $RuntimeSetupScript
    } catch {
        Write-Host "[Flowork] ℹ️ Runtime setup completed with notice: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# 4.5 Autonomous Neural ONNX Model Provisioning (FastEmbed / Semantic Search)
$ModelsDir = Join-Path $InstallDir "portable-home\.flowork\models"
$ModelTarget = Join-Path $ModelsDir "models--Xenova--bge-small-en-v1.5"
$ModelZipUrl = "https://github.com/flowork-os/FLOWORK-AGENT/releases/download/v1.0.0/Flowork-Model-bge-small.zip"
$TmpModelZip = Join-Path $ModelsDir "temp_model.zip"

if (-not (Test-Path (Join-Path $ModelTarget "snapshots\ea104dacec62c0de699686887e3f920caeb4f3e3\onnx\model.onnx"))) {
    Write-Host "[Flowork] 🧠 Fetching official neural embedding model from GitHub Release (155 MB)..." -ForegroundColor Cyan
    if (-not (Test-Path $ModelsDir)) { New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null }
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        (New-Object System.Net.WebClient).DownloadFile($ModelZipUrl, $TmpModelZip)
        $ExpectedHash = "ef427bb0e8d1c0688ccdc3216cf2f41f07ed3167a36ecf9738c5b32d1862bc45"
        $CalcHash = (Get-FileHash -Path $TmpModelZip -Algorithm SHA256).Hash.ToLower()
        if ($CalcHash -eq $ExpectedHash) {
            Write-Host "[Flowork] 📦 Unpacking official ONNX model bundle..." -ForegroundColor Cyan
            Expand-Archive -Path $TmpModelZip -DestinationPath $ModelsDir -Force
            Write-Host "[Flowork] ✅ Neural ONNX embedding model installed successfully (100% offline ready)." -ForegroundColor Green
        } else {
            Write-Host "[Flowork] ⚠️ Model checksum mismatch ($CalcHash vs $ExpectedHash); skipping extraction." -ForegroundColor Yellow
        }
        Remove-Item $TmpModelZip -Force -ErrorAction SilentlyContinue
    } catch {
        Write-Host "[Flowork] ⚠️ Model auto-download notice: $($_.Exception.Message)" -ForegroundColor Yellow
        Remove-Item $TmpModelZip -Force -ErrorAction SilentlyContinue
    }
}

# 5. Add Install Directory & Portable Runtimes to User PATH
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$RuntimePaths = @(
    $InstallDir,
    (Join-Path $InstallDir "runtimes\node"),
    (Join-Path $InstallDir "runtimes\python"),
    (Join-Path $InstallDir "portable-home\bin")
)
$NewPaths = @()
foreach ($p in $RuntimePaths) {
    if ($UserPath -notlike "*$p*") {
        $NewPaths += $p
    }
}
if ($NewPaths.Count -gt 0) {
    $UpdatedUserPath = ($UserPath.TrimEnd(';') + ";" + ($NewPaths -join ";")).TrimStart(';')
    [Environment]::SetEnvironmentVariable("Path", $UpdatedUserPath, "User")
    Write-Host "✅ Registered Flowork & Portable Runtimes to User PATH." -ForegroundColor Green
}

# 6. Create Desktop & Start Menu Shortcuts
$WshShell = New-Object -ComObject WScript.Shell

# Desktop Shortcut
$DesktopPath = [Environment]::GetFolderPath("Desktop")
if (Test-Path $DesktopPath) {
    $ShortcutPath = Join-Path $DesktopPath "Flowork OS.lnk"
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = Join-Path $InstallDir "run.bat"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "Flowork Sovereign Canvas Host"
    $IconPath = Join-Path $InstallDir "favicon.ico"
    if (Test-Path $IconPath) { $Shortcut.IconLocation = "$IconPath,0" }
    $Shortcut.Save()
    Write-Host "✅ Created Desktop Shortcut: $ShortcutPath" -ForegroundColor Green

    # Direct Desktop Batch Launcher (Universal Resilient Fallback)
    $DesktopLauncherBat = Join-Path $DesktopPath "Flowork OS Launcher.bat"
    $BatLauncherCode = "@echo off`r`ncd /d `"$InstallDir`"`r`ncall `"$InstallDir\run.bat`" %*`r`n"
    [System.IO.File]::WriteAllText($DesktopLauncherBat, $BatLauncherCode)
    Write-Host "✅ Created Desktop Batch Launcher: $DesktopLauncherBat" -ForegroundColor Green
}

# Start Menu Shortcut
$StartMenuPath = [Environment]::GetFolderPath("Programs")
if (Test-Path $StartMenuPath) {
    $StartShortcutPath = Join-Path $StartMenuPath "Flowork OS.lnk"
    $StartShortcut = $WshShell.CreateShortcut($StartShortcutPath)
    $StartShortcut.TargetPath = Join-Path $InstallDir "run.bat"
    $StartShortcut.WorkingDirectory = $InstallDir
    $StartShortcut.Description = "Flowork Sovereign Canvas Host"
    $IconPath = Join-Path $InstallDir "favicon.ico"
    if (Test-Path $IconPath) { $StartShortcut.IconLocation = "$IconPath,0" }
    $StartShortcut.Save()
    Write-Host "✅ Created Start Menu Shortcut: $StartShortcutPath" -ForegroundColor Green
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎉 Flowork OS installed successfully!" -ForegroundColor Green
Write-Host "🚀 Launching Flowork Canvas Host..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 7. Launch Flowork
$RunBat = Join-Path $InstallDir "run.bat"
Start-Process -FilePath $RunBat -WorkingDirectory $InstallDir
