# Flowork OS Sovereign Git Safety Guardrail (Windows PowerShell Edition)
# 100% Parity with x-flow Kernel check_git_safety in core/src/tools.rs

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$CommandArg = ""
)

if (-not [string]::IsNullOrWhiteSpace($CommandArg)) {
    $InputData = $CommandArg
} else {
    $InputData = [Console]::In.ReadToEnd()
}
if ([string]::IsNullOrWhiteSpace($InputData)) { exit 0 }

$Command = ""
if ($InputData.Trim().StartsWith("{")) {
    try {
        $json = $InputData | ConvertFrom-Json
        $Command = if ($json.tool_input.command) { $json.tool_input.command }
                   elseif ($json.CommandLine) { $json.CommandLine }
                   elseif ($json.command) { $json.command }
                   elseif ($json.cmd) { $json.cmd }
                   else { "" }
    } catch {
        $Command = $InputData
    }
} else {
    $Command = $InputData
}

$Command = $Command.Trim()
if ([string]::IsNullOrWhiteSpace($Command)) { exit 0 }

# Override check
if ($Command -match "(--allow-destructive-git|--flowork-force-allow)") { exit 0 }

$cmdLower = $Command.ToLower()

# 1. Force push
if (($cmdLower -match "(^|[;&|\s])push(\s|$)") -and ($cmdLower -match "(--force|\s-f(\s|=|$)|origin\s+\+|upstream\s+\+)")) {
    [Console]::Error.WriteLine("BLOCKED: Perintah '$Command' memuat operasi force push git. Doktrin Kedaulatan Flowork OS melarang force push.")
    exit 2
}

# 2. Hard reset
if (($cmdLower -match "(^|[;&|\s])reset(\s|$)") -and ($cmdLower -match "--hard")) {
    [Console]::Error.WriteLine("BLOCKED: Perintah '$Command' memuat 'reset --hard'. Doktrin Kedaulatan Flowork OS melarang hard reset.")
    exit 2
}

# 3. Clean purge
if (($cmdLower -match "(^|[;&|\s])clean(\s|$)") -and ($cmdLower -match "(-[a-zA-Z]*f|--force)")) {
    [Console]::Error.WriteLine("BLOCKED: Perintah '$Command' memuat 'git clean -f' (pemusnahan untracked files).")
    exit 2
}

# 4. Branch force delete
if (($Command -match "branch\s+-D") -or (($cmdLower -match "(^|[;&|\s])branch(\s|$)") -and ($cmdLower -match "--delete") -and ($cmdLower -match "--force"))) {
    [Console]::Error.WriteLine("BLOCKED: Perintah '$Command' memuat penghapusan paksa cabang git (-D).")
    exit 2
}

# 5. Discard changes
if (($cmdLower -match "(checkout|restore)") -and ($cmdLower -match "\s\.(\s|$)")) {
    [Console]::Error.WriteLine("BLOCKED: Perintah '$Command' memuat pembatalan seluruh perubahan kerja ('checkout .' / 'restore .').")
    exit 2
}

exit 0
