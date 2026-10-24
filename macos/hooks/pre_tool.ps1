# Flowork OS Sovereign Pre-Tool Hook (Windows PowerShell)
param([string]$Payload = "")

if ([string]::IsNullOrWhiteSpace($Payload)) {
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Catastrophic disk destruction prevention
$DestructivePatterns = @(
    'format\s+[a-zA-Z]:',
    'rd\s+/s\s+/q\s+[a-zA-Z]:\\',
    'rmdir\s+/s\s+/q\s+[a-zA-Z]:\\',
    'Remove-Item\s+-Recurse\s+-Force\s+[a-zA-Z]:\\',
    'rm\s+-[a-zA-Z]*rf\s+/[^\s]*'
)

foreach ($pattern in $DestructivePatterns) {
    if ($Payload -match $pattern) {
        [Console]::Error.WriteLine("BLOCKED by pre_tool hook: Catastrophic disk destruction command detected!")
        exit 2
    }
}

# 2. Delegate to git guardrail if git command is present
if ($Payload -match '(?i)git') {
    $GitHook = Join-Path $ScriptDir "block-dangerous-git.ps1"
    if (Test-Path $GitHook) {
        & $GitHook $Payload
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
}

exit 0
