# Flowork OS Sovereign Git Safety Guardrail (Windows PowerShell)
param([string]$InputText = "")

if ([string]::IsNullOrWhiteSpace($InputText)) {
    exit 0
}

# Check explicit authorization override
if ($InputText -match '(?i)(--allow-destructive-git|--flowork-force-allow)') {
    exit 0
}

# 1. Force push
if ($InputText -match '(?i)git\s+push.*(--force|\s+-f(\s+|=|$)|origin\s+\+|upstream\s+\+)') {
    [Console]::Error.WriteLine("BLOCKED: Git force push operation rejected by Flowork OS. Use --allow-destructive-git to override.")
    exit 2
}

# 2. Hard reset
if ($InputText -match '(?i)git\s+reset.*--hard') {
    [Console]::Error.WriteLine("BLOCKED: Git reset --hard rejected by Flowork OS. Use --allow-destructive-git to override.")
    exit 2
}

# 3. Clean purge
if ($InputText -match '(?i)git\s+clean.*(-[a-zA-Z]*f|--force)') {
    [Console]::Error.WriteLine("BLOCKED: Git clean -f rejected by Flowork OS. Use --allow-destructive-git to override.")
    exit 2
}

# 4. Branch force delete
if ($InputText -match '(?i)git\s+branch.*(-D|--delete\s+--force)') {
    [Console]::Error.WriteLine("BLOCKED: Git branch -D rejected by Flowork OS. Use --allow-destructive-git to override.")
    exit 2
}

# 5. Discard changes
if ($InputText -match '(?i)git\s+(checkout|restore)\s+\.') {
    [Console]::Error.WriteLine("BLOCKED: Discarding changes ('checkout .' / 'restore .') rejected by Flowork OS.")
    exit 2
}

exit 0
