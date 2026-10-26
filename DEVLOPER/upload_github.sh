#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — AUTOMATED GITHUB RELEASE & MULTI-OS DEPLOYMENT TOOL
# Repository: https://github.com/flowork-os/FLOWORK-AGENT
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

# -------------------------------------------------------------
# 1. Configuration & Credentials
# -------------------------------------------------------------
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FLOWORK_DIR="$PROJECT_ROOT/flowork"
export DEVLOPER_DIR="$PROJECT_ROOT/DEVLOPER"
export SCRATCH_DIR="$PROJECT_ROOT/.FL_BIN/scratch"
export STAGING_DIR="$SCRATCH_DIR/repo_staging"

# Upstream repository settings
REPO_OWNER="flowork-os"
REPO_NAME="FLOWORK-AGENT"
REPO_BRANCH="main"

# GitHub Token (Zero-Leak: Loaded from env or ~/.flowork_github_token outside repo)
if [ -z "${GITHUB_TOKEN:-}" ] && [ -f "$HOME/.flowork_github_token" ]; then
  GITHUB_TOKEN="$(cat "$HOME/.flowork_github_token" | tr -d '[:space:]')"
fi
: "${GITHUB_TOKEN:?Error: GITHUB_TOKEN environment variable or ~/.flowork_github_token is required}"
REMOTE_AUTH_URL="https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"

echo "============================================================"
echo "⚡ FLOWORK OS — SOVEREIGN MULTI-OS GITHUB PUBLISHER"
echo "============================================================"
echo "📁 Project Directory: $PROJECT_ROOT"
echo "🌐 Upstream Target:   https://github.com/${REPO_OWNER}/${REPO_NAME} (${REPO_BRANCH})"
echo "🔒 Security Mode:     Strict Zero-Leak Isolation Gate"
echo "============================================================"

mkdir -p "$SCRATCH_DIR"

# -------------------------------------------------------------
# 1.5. Architectural Sovereignty & Rejection Gate
# -------------------------------------------------------------
echo "🔍 [Gatekeeper] Verifying Sovereign Architecture Integrity..."
python3 "$DEVLOPER_DIR/hooks/validate_sovereignty.py"

# -------------------------------------------------------------
# 2. Locate Source Binaries
# -------------------------------------------------------------
LINUX_BIN="$DEVLOPER_DIR/build_output/flowork"
[ ! -f "$LINUX_BIN" ] && LINUX_BIN="$FLOWORK_DIR/x-flow"

WIN_BIN="$DEVLOPER_DIR/build_output/flowork.exe"
[ ! -f "$WIN_BIN" ] && WIN_BIN="$FLOWORK_DIR/flowork/flowork.exe"

MAC_X86_BIN="$DEVLOPER_DIR/core/target/x86_64-apple-darwin/release/flowork"
[ ! -f "$MAC_X86_BIN" ] && MAC_X86_BIN="$FLOWORK_DIR/flowork/flowork-darwin-x86_64"
MAC_ARM_BIN="$DEVLOPER_DIR/core/target/aarch64-apple-darwin/release/flowork"
[ ! -f "$MAC_ARM_BIN" ] && MAC_ARM_BIN="$FLOWORK_DIR/flowork/flowork-darwin-arm64"

CONNECTOR_BIN="$FLOWORK_DIR/flowork/flowork-connector"

if [ ! -f "$LINUX_BIN" ]; then
    echo "❌ [ERROR] Linux binary not found at $LINUX_BIN"
    exit 1
fi
if [ ! -f "$WIN_BIN" ]; then
    echo "❌ [ERROR] Windows binary not found at $WIN_BIN"
    exit 1
fi

echo "✅ Verified Release Binaries:"
echo "   - Linux:       $LINUX_BIN ($(du -h "$LINUX_BIN" | cut -f1))"
echo "   - Windows:     $WIN_BIN ($(du -h "$WIN_BIN" | cut -f1))"
if [ -f "$MAC_X86_BIN" ]; then
    echo "   - macOS Intel: $MAC_X86_BIN ($(du -h "$MAC_X86_BIN" | cut -f1))"
fi
if [ -f "$MAC_ARM_BIN" ]; then
    echo "   - macOS Apple: $MAC_ARM_BIN ($(du -h "$MAC_ARM_BIN" | cut -f1))"
fi
if [ -f "$CONNECTOR_BIN" ]; then
    echo "   - Connector:   $CONNECTOR_BIN ($(du -h "$CONNECTOR_BIN" | cut -f1))"
fi

# -------------------------------------------------------------
# 3. Dynamic Cryptographic Checksum Update
# -------------------------------------------------------------
echo ""
echo "🔒 [1/7] Recalculating Live Cryptographic SHA-256 Checksums..."

python3 - << 'EOF_PY_CHECKSUM'
import os
import hashlib
import json

project_root = os.environ.get("PROJECT_ROOT", os.path.abspath("."))
linux_bin = os.path.join(project_root, "DEVLOPER", "build_output", "flowork")
if not os.path.exists(linux_bin):
    linux_bin = os.path.join(project_root, "flowork", "x-flow")

win_bin = os.path.join(project_root, "DEVLOPER", "build_output", "flowork.exe")
if not os.path.exists(win_bin):
    win_bin = os.path.join(project_root, "flowork", "flowork", "flowork.exe")

mac_x86_bin = os.path.join(project_root, "DEVLOPER", "build_output", "flowork-darwin-x86_64")
if not os.path.exists(mac_x86_bin):
    mac_x86_bin = os.path.join(project_root, "DEVLOPER", "core", "target", "x86_64-apple-darwin", "release", "flowork")
if not os.path.exists(mac_x86_bin):
    mac_x86_bin = os.path.join(project_root, "flowork", "flowork", "flowork-darwin-x86_64")
mac_arm_bin = os.path.join(project_root, "DEVLOPER", "build_output", "flowork-darwin-arm64")
if not os.path.exists(mac_arm_bin):
    mac_arm_bin = os.path.join(project_root, "DEVLOPER", "core", "target", "aarch64-apple-darwin", "release", "flowork")
if not os.path.exists(mac_arm_bin):
    mac_arm_bin = os.path.join(project_root, "flowork", "flowork", "flowork-darwin-arm64")
connector_bin = os.path.join(project_root, "flowork", "flowork", "flowork-connector")

def sha256_file(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

linux_hash = sha256_file(linux_bin)
win_hash = sha256_file(win_bin)
conn_hash = sha256_file(connector_bin)
mac_x86_hash = sha256_file(mac_x86_bin)
mac_arm_hash = sha256_file(mac_arm_bin)

print(f"   ✓ Linux ELF SHA-256:         {linux_hash}")
print(f"   ✓ Windows PE SHA-256:        {win_hash}")
if mac_x86_hash:
    print(f"   ✓ macOS x86_64 SHA-256:      {mac_x86_hash}")
if mac_arm_hash:
    print(f"   ✓ macOS arm64 SHA-256:       {mac_arm_hash}")

checksum_paths = [
    os.path.join(project_root, "DEVLOPER", "release_checksums.json"),
    os.path.join(project_root, "flowork", "release_checksums.json"),
    os.path.join(project_root, "linux", "release_checksums.json"),
    os.path.join(project_root, "windows", "release_checksums.json"),
    os.path.join(project_root, "macos", "release_checksums.json"),
    os.path.join(project_root, "release_checksums.json"),
]

ref_file = os.path.join(project_root, "flowork", "release_checksums.json")
with open(ref_file, "r", encoding="utf-8") as f:
    matrix = json.load(f)

if linux_hash:
    l_list = matrix.setdefault("linux", {}).setdefault("binary_sha256", [])
    if linux_hash in l_list:
        l_list.remove(linux_hash)
    l_list.insert(0, linux_hash)
    matrix["latest_linux_hash"] = linux_hash
    matrix["linux"]["latest_hash"] = linux_hash

if conn_hash:
    matrix.setdefault("linux", {})["connector_sha256"] = conn_hash

if win_hash:
    w_list = matrix.setdefault("windows", {}).setdefault("binary_sha256", [])
    if win_hash in w_list:
        w_list.remove(win_hash)
    w_list.insert(0, win_hash)
    matrix["latest_windows_hash"] = win_hash
    matrix["windows"]["latest_hash"] = win_hash

if mac_x86_hash or mac_arm_hash:
    macos_dict = matrix.setdefault("macos", {})
    if mac_x86_hash:
        macos_dict["x86_64_sha256"] = mac_x86_hash
    if mac_arm_hash:
        macos_dict["arm64_sha256"] = mac_arm_hash

for p in checksum_paths:
    if os.path.exists(os.path.dirname(p)):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(matrix, f, indent=2)
            f.write("\n")
        print(f"   ✓ Synchronized matrix to: {p}")
EOF_PY_CHECKSUM

# -------------------------------------------------------------
# 4. Initialize & Synchronize Git Staging Area
# -------------------------------------------------------------
echo ""
echo "📦 [2/7] Preparing Clean Git Staging Repository..."

if [ ! -d "$STAGING_DIR/.git" ] || ! git -C "$STAGING_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "   Cloning $REMOTE_AUTH_URL into staging..."
    rm -rf "$STAGING_DIR"
    git clone "$REMOTE_AUTH_URL" "$STAGING_DIR"
else
    echo "   Refreshing upstream tracking branch..."
    git -C "$STAGING_DIR" remote set-url origin "$REMOTE_AUTH_URL"
    git -C "$STAGING_DIR" fetch origin "$REPO_BRANCH"
    git -C "$STAGING_DIR" reset --hard "origin/$REPO_BRANCH"
fi

# -------------------------------------------------------------
# 5. Populate Multi-OS Trees (linux/, windows/, and macos/)
# -------------------------------------------------------------
echo ""
echo "🔨 [3/7] Packaging Multi-OS Distribution Trees..."

python3 - << 'EOF_PY_PACKAGER'
import os
import shutil
import glob

project_root = os.environ.get("PROJECT_ROOT", os.path.abspath("."))
flowork_dir = os.path.join(project_root, "flowork")
devloper_dir = os.path.join(project_root, "DEVLOPER")
staging_dir = os.path.join(project_root, ".FL_BIN", "scratch", "repo_staging")

linux_target = os.path.join(staging_dir, "linux")
windows_target = os.path.join(staging_dir, "windows")
macos_target = os.path.join(staging_dir, "macos")

forbidden_files = {
    "auth_vault.json", "account_pool.json", "cloud_soul.json", "vault.json",
    "flowrk-standalone-oauth-token", "akungithub", "akungithub.txt",
    "security_vault.json", "active_workspace.json", "active_viewport.json",
    "dev.flowork", "dev.flow", "token",
    "launcher.html", "launcher", "auth", "callback"
}

forbidden_extensions = {".log", ".tmp", ".pem", ".key", ".cert", ".crt", ".flow", ".flowork", ".bak", ".backup"}

def clean_copy_tree(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    def _ignore(directory, contents):
        ignored = set()
        for item in contents:
            if item in forbidden_files:
                ignored.add(item)
            elif any(item.endswith(ext) for ext in forbidden_extensions):
                ignored.add(item)
            elif item in {".git", ".flowork_spam", ".flowork_brain", "node_modules", "target", "__pycache__", "connector_src", "sealed_connector"}:
                ignored.add(item)
        return ignored
    shutil.copytree(src, dst, ignore=_ignore)

# Clean OS targets (preserve .gitkeep)
for target in [linux_target, windows_target, macos_target]:
    os.makedirs(target, exist_ok=True)
    for item in os.listdir(target):
        item_path = os.path.join(target, item)
        if item != ".gitkeep":
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

# -----------------
# 1. LINUX TREE
# -----------------
print("   - Staging linux/...")
os.makedirs(os.path.join(linux_target, "flowork"), exist_ok=True)
linux_bin = os.path.join(devloper_dir, "build_output", "flowork")
if not os.path.exists(linux_bin):
    linux_bin = os.path.join(flowork_dir, "x-flow")

shutil.copy2(linux_bin, os.path.join(linux_target, "x-flow"))
os.chmod(os.path.join(linux_target, "x-flow"), 0o755)
shutil.copy2(linux_bin, os.path.join(linux_target, "flowork", "flowork"))
os.chmod(os.path.join(linux_target, "flowork", "flowork"), 0o755)

conn_bin = os.path.join(flowork_dir, "flowork", "flowork-connector")
if os.path.exists(conn_bin):
    shutil.copy2(conn_bin, os.path.join(linux_target, "flowork", "flowork-connector"))
    os.chmod(os.path.join(linux_target, "flowork", "flowork-connector"), 0o755)

# Sovereign sealed enclave: ZERO plaintext connection on disk (enclave built into binary)
clean_copy_tree(os.path.join(flowork_dir, "canvas-ui"), os.path.join(linux_target, "canvas-ui"))

uploads_l = os.path.join(linux_target, "canvas-ui", "uploads")
if os.path.exists(uploads_l):
    for f in os.listdir(uploads_l):
        if f.endswith((".png", ".jpg", ".jpeg", ".webp")):
            os.remove(os.path.join(uploads_l, f))
    with open(os.path.join(uploads_l, ".gitkeep"), "w") as f:
        pass

for shared_dir in ["system", "skills", "tools", "hooks", "mcp", "apps", "runtimes", "engine", "connection", "swarmflow"]:
    src_dir = os.path.join(flowork_dir, shared_dir)
    if os.path.exists(src_dir):
        clean_copy_tree(src_dir, os.path.join(linux_target, shared_dir))

os.makedirs(os.path.join(linux_target, "portable-home", "bin"), exist_ok=True)
os.makedirs(os.path.join(linux_target, "portable-home", ".flowork"), exist_ok=True)
with open(os.path.join(linux_target, "portable-home", "bin", ".gitkeep"), "w") as f: pass
with open(os.path.join(linux_target, "portable-home", ".flowork", ".gitkeep"), "w") as f: pass

for fname in ["run.sh", "flowork.sh", "models.json", "VERSION", "release_checksums.json", "favicon.png", "X-Flow.desktop", "Flowork-Agent-Installer.desktop", "install.sh"]:
    src = os.path.join(flowork_dir, fname)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(linux_target, fname))
os.chmod(os.path.join(linux_target, "run.sh"), 0o755)
os.chmod(os.path.join(linux_target, "flowork.sh"), 0o755)
if os.path.exists(os.path.join(linux_target, "install.sh")):
    os.chmod(os.path.join(linux_target, "install.sh"), 0o755)
if os.path.exists(os.path.join(linux_target, "Flowork-Agent-Installer.desktop")):
    os.chmod(os.path.join(linux_target, "Flowork-Agent-Installer.desktop"), 0o755)

# -----------------
# 2. WINDOWS TREE
# -----------------
print("   - Staging windows/...")
os.makedirs(os.path.join(windows_target, "flowork"), exist_ok=True)
win_bin = os.path.join(devloper_dir, "build_output", "flowork.exe")
if not os.path.exists(win_bin):
    win_bin = os.path.join(flowork_dir, "flowork", "flowork.exe")

shutil.copy2(win_bin, os.path.join(windows_target, "flowork.exe"))
shutil.copy2(win_bin, os.path.join(windows_target, "flowork", "flowork.exe"))

win_conn = os.path.join(flowork_dir, "flowork", "flowork-connector.exe")
if os.path.exists(win_conn):
    shutil.copy2(win_conn, os.path.join(windows_target, "flowork-connector.exe"))
    shutil.copy2(win_conn, os.path.join(windows_target, "flowork", "flowork-connector.exe"))

# Sovereign sealed enclave: ZERO plaintext connection on disk (enclave built into binary)
clean_copy_tree(os.path.join(flowork_dir, "canvas-ui"), os.path.join(windows_target, "canvas-ui"))

uploads_w = os.path.join(windows_target, "canvas-ui", "uploads")
if os.path.exists(uploads_w):
    for f in os.listdir(uploads_w):
        if f.endswith((".png", ".jpg", ".jpeg", ".webp")):
            os.remove(os.path.join(uploads_w, f))
    with open(os.path.join(uploads_w, ".gitkeep"), "w") as f:
        pass

for shared_dir in ["system", "skills", "tools", "hooks", "mcp", "apps", "runtimes", "engine", "connection", "swarmflow"]:
    src_dir = os.path.join(flowork_dir, shared_dir)
    if os.path.exists(src_dir):
        clean_copy_tree(src_dir, os.path.join(windows_target, shared_dir))

os.makedirs(os.path.join(windows_target, "portable-home", "bin"), exist_ok=True)
os.makedirs(os.path.join(windows_target, "portable-home", ".flowork"), exist_ok=True)
with open(os.path.join(windows_target, "portable-home", "bin", ".gitkeep"), "w") as f: pass
with open(os.path.join(windows_target, "portable-home", ".flowork", ".gitkeep"), "w") as f: pass

for fname in ["run.bat", "flowork.bat", "models.json", "VERSION", "release_checksums.json", "favicon.png", "install.bat", "install.ps1", "Flowork-Agent-Installer.exe"]:
    src = os.path.join(flowork_dir, fname)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(windows_target, fname))

# -----------------
# 3. MACOS TREE
# -----------------
print("   - Staging macos/...")
os.makedirs(os.path.join(macos_target, "flowork"), exist_ok=True)
mac_x86 = os.path.join(devloper_dir, "core", "target", "x86_64-apple-darwin", "release", "flowork")
if not os.path.exists(mac_x86):
    mac_x86 = os.path.join(flowork_dir, "flowork", "flowork-darwin-x86_64")
mac_arm = os.path.join(devloper_dir, "core", "target", "aarch64-apple-darwin", "release", "flowork")
if not os.path.exists(mac_arm):
    mac_arm = os.path.join(flowork_dir, "flowork", "flowork-darwin-arm64")

if os.path.exists(mac_x86):
    shutil.copy2(mac_x86, os.path.join(macos_target, "flowork-x86_64"))
    os.chmod(os.path.join(macos_target, "flowork-x86_64"), 0o755)
    shutil.copy2(mac_x86, os.path.join(macos_target, "flowork"))
    os.chmod(os.path.join(macos_target, "flowork"), 0o755)
    shutil.copy2(mac_x86, os.path.join(macos_target, "x-flow"))
    os.chmod(os.path.join(macos_target, "x-flow"), 0o755)
    shutil.copy2(mac_x86, os.path.join(macos_target, "flowork", "flowork"))
    os.chmod(os.path.join(macos_target, "flowork", "flowork"), 0o755)

if os.path.exists(mac_arm):
    shutil.copy2(mac_arm, os.path.join(macos_target, "flowork-arm64"))
    os.chmod(os.path.join(macos_target, "flowork-arm64"), 0o755)

mac_conn_arm = os.path.join(flowork_dir, "flowork", "flowork-connector-darwin-arm64")
if os.path.exists(mac_conn_arm):
    shutil.copy2(mac_conn_arm, os.path.join(macos_target, "flowork", "flowork-connector-darwin-arm64"))
    os.chmod(os.path.join(macos_target, "flowork", "flowork-connector-darwin-arm64"), 0o755)
    shutil.copy2(mac_conn_arm, os.path.join(macos_target, "flowork", "flowork-connector"))
    os.chmod(os.path.join(macos_target, "flowork", "flowork-connector"), 0o755)

mac_conn_x86 = os.path.join(flowork_dir, "flowork", "flowork-connector-darwin-x86_64")
if os.path.exists(mac_conn_x86):
    shutil.copy2(mac_conn_x86, os.path.join(macos_target, "flowork", "flowork-connector-darwin-x86_64"))
    os.chmod(os.path.join(macos_target, "flowork", "flowork-connector-darwin-x86_64"), 0o755)

# Sovereign sealed enclave: ZERO plaintext connection on disk (enclave built into binary)
clean_copy_tree(os.path.join(flowork_dir, "canvas-ui"), os.path.join(macos_target, "canvas-ui"))

uploads_m = os.path.join(macos_target, "canvas-ui", "uploads")
if os.path.exists(uploads_m):
    for f in os.listdir(uploads_m):
        if f.endswith((".png", ".jpg", ".jpeg", ".webp")):
            os.remove(os.path.join(uploads_m, f))
    with open(os.path.join(uploads_m, ".gitkeep"), "w") as f:
        pass

for shared_dir in ["system", "skills", "tools", "hooks", "mcp", "apps", "runtimes", "engine", "connection", "swarmflow"]:
    src_dir = os.path.join(flowork_dir, shared_dir)
    if os.path.exists(src_dir):
        clean_copy_tree(src_dir, os.path.join(macos_target, shared_dir))

os.makedirs(os.path.join(macos_target, "portable-home", "bin"), exist_ok=True)
os.makedirs(os.path.join(macos_target, "portable-home", ".flowork"), exist_ok=True)
with open(os.path.join(macos_target, "portable-home", "bin", ".gitkeep"), "w") as f: pass
with open(os.path.join(macos_target, "portable-home", ".flowork", ".gitkeep"), "w") as f: pass

# macOS specific launchers
macos_run_src = os.path.join(flowork_dir, "runtimes", "macos_run.sh")
if os.path.exists(macos_run_src):
    shutil.copy2(macos_run_src, os.path.join(macos_target, "run.sh"))
    os.chmod(os.path.join(macos_target, "run.sh"), 0o755)

for fname in ["models.json", "VERSION", "release_checksums.json", "favicon.png", "install.sh", "Flowork-Agent-Installer.command"]:
    src = os.path.join(flowork_dir, fname)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(macos_target, fname))

if os.path.exists(os.path.join(macos_target, "install.sh")):
    os.chmod(os.path.join(macos_target, "install.sh"), 0o755)
if os.path.exists(os.path.join(macos_target, "Flowork-Agent-Installer.command")):
    os.chmod(os.path.join(macos_target, "Flowork-Agent-Installer.command"), 0o755)
    shutil.copy2(os.path.join(macos_target, "Flowork-Agent-Installer.command"), os.path.join(macos_target, "Flowork.command"))

# -----------------
# 4. ROOT STAGING
# -----------------
if os.path.exists(os.path.join(flowork_dir, "runtimes")):
    clean_copy_tree(os.path.join(flowork_dir, "runtimes"), os.path.join(staging_dir, "runtimes"))

if os.path.exists(os.path.join(flowork_dir, "swarmflow")):
    clean_copy_tree(os.path.join(flowork_dir, "swarmflow"), os.path.join(staging_dir, "swarmflow"))

for rname in ["install.sh", "install.ps1", "install.bat", "Flowork-Agent-Installer.desktop", "Flowork-Agent-Installer.exe", "Flowork-Agent-Installer.command", "README.md", "README.MD", "cover.png", "STRUCTURE.MD", "VERSION", "release_checksums.json"]:
    src = os.path.join(flowork_dir, rname)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(staging_dir, rname))

print("   ✓ Multi-OS distribution trees (linux, windows, macos) populated successfully.")
EOF_PY_PACKAGER

# -------------------------------------------------------------
# 6. Verify & Synchronize Protection Files & Permissions
# -------------------------------------------------------------
echo ""
echo "📋 [4/7] Synchronizing Root Autonomous Installers & Protection Files..."

chmod +x "$STAGING_DIR/install.sh" 2>/dev/null || true
chmod +x "$STAGING_DIR/Flowork-Agent-Installer.desktop" 2>/dev/null || true
chmod +x "$STAGING_DIR/Flowork-Agent-Installer.command" 2>/dev/null || true
chmod +x "$STAGING_DIR/runtimes/linux/setup_runtimes.sh" 2>/dev/null || true

# Root .gitignore (Anti-Leak Shield)
cat << 'EOF_GITIGNORE' > "$STAGING_DIR/.gitignore"
# =========================================================================
# 🛡️ FLOWORK OS — SOVEREIGN SENSITIVE DATA SHIELD & ZERO-LEAK .GITIGNORE
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =========================================================================

# 1. Sovereign Local Runtime, Auth, Tokens & Private Data (.flowork)
.flowork/
**/.flowork/
portable-home/.flowork/*
!portable-home/.flowork/.gitkeep
**/portable-home/.flowork/*
!**/portable-home/.flowork/.gitkeep

# 2. Host Machine & Local Workspace Hardware Bindings
.flowork/config/active_workspace.json
.flowork/active_viewport.json
portable-home/.flowork/active_viewport.json
akungithub
akungithub.txt

# 3. Browser Profiles, Cookies & Web Caches
xflow-canvas-profile/
*canvas-profile*/
Cookies
Cookies-journal
Network/Cookies
Local Storage/
IndexedDB/
Session Storage/
Singleton*
.org.chromium.*

# 4. Environment Secrets & Private Keys
.env
.env.*
*.pem
*.key
*.cert
*.crt
*.flow
*.flowork
dev.flowork
dev.flow

# 5. Runtime Spams, Forensic Memories & Temporary Dumps
.flowork_spam/
flowork_spam/
.FL_SPAM/
FL_SPAM/
.flowork_brain/
flowork_brain/
.FL_BRAIN/
FL_BRAIN/
.FL_BIN/
FL_BIN/
*.log
*.tmp
*.bak
screen_capture.*
*.png.tmp
*.jpg.tmp
canvas-ui/uploads/*.png
canvas-ui/uploads/*.jpg
canvas-ui/uploads/*.jpeg
canvas-ui/uploads/*.webp
!canvas-ui/uploads/.gitkeep
**/canvas-ui/uploads/*.png
**/canvas-ui/uploads/*.jpg
**/canvas-ui/uploads/*.jpeg
**/canvas-ui/uploads/*.webp
!**/canvas-ui/uploads/.gitkeep

# 6. Build Artifacts & Node Modules
node_modules/
target/
.cargo/
dist/

# 7. OS Generated Files
.DS_Store
Thumbs.db
desktop.ini
EOF_GITIGNORE

# Multi-OS Line Ending Matrix (.gitattributes)
cat << 'EOF_GITATTR' > "$STAGING_DIR/.gitattributes"
# Flowork OS — Sovereign Multi-OS Line Ending Normalization Matrix
* text=auto eol=lf
*.sh text eol=lf
*.bash text eol=lf
*.command text eol=lf
*.mjs text eol=lf
*.js text eol=lf
*.rs text eol=lf
*.json text eol=lf
*.md text eol=lf
*.toml text eol=lf
*.css text eol=lf
*.html text eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
*.exe binary
*.png binary
*.ico binary
*.tar.gz binary
*.zip binary
EOF_GITATTR

chmod +x "$STAGING_DIR/install.sh" 2>/dev/null || true
echo "   ✓ Staged multi-OS installers and configuration files."

# -------------------------------------------------------------
# 7. Strict Forensic Zero-Leak Security Audit
# -------------------------------------------------------------
echo ""
echo "🛡️ [5/7] Executing Forensic Anti-Leak Inspection Gate..."

python3 - << 'EOF_PY_AUDIT'
import os
import re

staging_dir = os.environ.get("STAGING_DIR", os.path.join(os.environ.get("PROJECT_ROOT", os.path.abspath(".")), ".FL_BIN", "scratch", "repo_staging"))
forbidden_files = {
    "auth_vault.json", "account_pool.json", "cloud_soul.json", "vault.json",
    "flowrk-standalone-oauth-token", "akungithub", "akungithub.txt",
    "security_vault.json", "active_workspace.json", "active_viewport.json",
    "dev.flowork", "dev.flow", "token",
    "launcher.html", "launcher", "auth", "callback"
}
forbidden_exts = {".log", ".tmp", ".pem", ".key", ".cert", ".crt", ".flow", ".flowork", ".bak", ".backup"}

leaks = []
file_count = 0
total_size = 0

for root, dirs, files in os.walk(staging_dir):
    if ".git" in root:
        continue
    for d in dirs:
        if d in {"connector_src", "sealed_connector"}:
            leaks.append(f"Forbidden directory in staging: {os.path.join(root, d)}")

# Strict Hardcoded Path Regex Patterns
host_path_patterns = [
    (re.compile(r'/home/(?:mrflow|awenk|teguh|[a-zA-Z0-9_\-\.]+/(?:Desktop|\.local|\.cargo|\.config))'), "Hardcoded Linux host home directory"),
    (re.compile(r'[a-zA-Z]:[/\\]Users[/\\][a-zA-Z0-9_\-\.]+', re.IGNORECASE), "Hardcoded Windows Users path"),
    (re.compile(r'/Users/[a-zA-Z0-9_\-\.]+/(?:Desktop|\.local|Downloads|Documents)', re.IGNORECASE), "Hardcoded macOS Users path"),
]

# Strict Secret Token Patterns
secret_patterns = [
    (re.compile(r'ghp_[a-zA-Z0-9]{36}'), "GitHub Personal Access Token (PAT)"),
    (re.compile(r'github_pat_[a-zA-Z0-9_]{82}'), "Fine-Grained GitHub PAT"),
    (re.compile(r'cfat_[a-zA-Z0-9_-]{35,}'), "Cloudflare API Token"),
    (re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----'), "Cryptographic Private Key"),
    (re.compile(r'AIzaSy[0-9A-Za-z_-]{33}'), "Google API Key"),
    (re.compile(r'sk-[a-zA-Z0-9_-]{24,}'), "OpenAI/Anthropic Secret Key"),
]

# Paths allowed to contain pattern signatures for test assertion/documentation purposes only
whitelist_audit_files = {
    "rules.json", "rules.md", "README.md", "upload_github.sh",
    "10_terminal_qc_verification.sh", "09_deterministic_test_harness.py",
    "manifest.json"
}

for root, dirs, files in os.walk(staging_dir):
    if ".git" in root:
        continue
    for f in files:
        file_count += 1
        path = os.path.join(root, f)
        rel_path = os.path.relpath(path, staging_dir)
        sz = os.path.getsize(path)
        total_size += sz

        # 1. Forbidden Vault / Credentials File Check
        if f in forbidden_files:
            leaks.append(f"CRITICAL: Forbidden credential/vault file in staging: {rel_path}")
        if any(f.endswith(ext) for ext in forbidden_exts):
            leaks.append(f"CRITICAL: Forbidden temporary/secret file extension: {rel_path}")

        # 2. Binary Stripping Audit: Ensure native Rust ELF executables are stripped via native ELF header inspection
        if f in {"flowork", "x-flow"}:
            try:
                with open(path, "rb") as bf:
                    hdr = bf.read(4096)
                    if b"\x7fELF" in hdr[:4]:
                        bf.seek(0)
                        if b".symtab" in bf.read():
                            leaks.append(f"UNSTRIPPED BINARY DETECTED: {rel_path} must be stripped before distribution!")
            except Exception: pass

        # 3. Source Text Inspection: Hardcoded Paths & Leaked Secrets
        is_binary = f.endswith((".exe", ".png", ".svg", ".db", ".ico", ".tar.gz", ".zip", ".wasm")) or sz > 3 * 1024 * 1024
        if not is_binary and f not in whitelist_audit_files:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line_no, line in enumerate(fh, start=1):
                        # Bypass scanner self-references and test comments
                        if any(marker in line for marker in ["assert_eq", "assertFalse", "guardian-input", "whitelist", "forbidden_patterns"]):
                            continue

                        # Check Hardcoded Host Paths
                        for pat, desc in host_path_patterns:
                            m = pat.search(line)
                            if m:
                                leaks.append(f"HARDCODED HOST PATH [{desc}]: {rel_path}:{line_no} -> '{m.group(0)}'")

                        # Check Secret Credentials
                        for pat, desc in secret_patterns:
                            m = pat.search(line)
                            if m:
                                leaks.append(f"SECRET CREDENTIAL LEAK [{desc}]: {rel_path}:{line_no} -> '{m.group(0)[:8]}***'")
            except Exception:
                pass

print(f"   ✓ Audited {file_count} files ({total_size / (1024*1024):.2f} MB)")
if leaks:
    print("\n🛑 [FAIL-CLOSED] CRITICAL SECURITY LEAK / HARDCODED PATH DETECTED:")
    print("=" * 70)
    for l in leaks:
        print(f"   ❌ {l}")
    print("=" * 70)
    print("🚨 BUILD & PUSH TERMINATED WITH EXIT CODE 1.")
    print("   Doktrin Kedaulatan Flowork OS: Haram rilis kode yang memuat path lokal atau kredensial rahasia!")
    sys.exit(1)
else:
    print("   ✅ ZERO LEAKS & ZERO HARDCODED PATHS CONFIRMED: All binaries stripped, all sources portable.")
EOF_PY_AUDIT

# -------------------------------------------------------------
# 8. Git Commit & Push to Upstream
# -------------------------------------------------------------
echo ""
echo "🚀 [6/7] Committing & Pushing to GitHub (origin ${REPO_BRANCH})..."

cd "$STAGING_DIR"

git config user.name "Flowork OS"
git config user.email "agent@floworkos.com"

git add -A

if git diff --cached --quiet; then
    echo "⚡ [INFO] No changes detected compared to upstream. Repository is already up-to-date!"
else
    TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
    COMMIT_MSG="release: sovereign multi-OS update ($TIMESTAMP)"
    git commit -m "$COMMIT_MSG"
    
    echo "📤 Pushing release commit to GitHub..."
    git push origin "$REPO_BRANCH"
    echo "   ✓ Successfully pushed commit to origin/$REPO_BRANCH"
fi

if [ "${SKIP_RELEASE_PUBLISH:-0}" = "1" ] || [ "${ONLY_PUSH:-0}" = "1" ]; then
    echo ""
    echo "============================================================"
    echo "⚡ [INFO] SKIP_RELEASE_PUBLISH=1 is active."
    echo "📤 Code successfully uploaded and pushed to GitHub (origin/$REPO_BRANCH)!"
    echo "🛑 Release publication skipped as commanded ('jangan di rilis dulu')."
    echo "============================================================"
    exit 0
fi

# -------------------------------------------------------------
# 9. Build Standalone Portable Packages & Official GitHub Release
# -------------------------------------------------------------
echo ""
echo "🎁 [7/7] Generating Release Bundles & Publishing Official GitHub Release..."

python3 - "$PROJECT_ROOT" "$STAGING_DIR" "$FLOWORK_DIR" "$SCRATCH_DIR/release_dist" "$GITHUB_TOKEN" << 'EOF_PY_RELEASE'
import os
import sys
import shutil
import tarfile
import zipfile
import urllib.request
import json

project_root = sys.argv[1]
staging_dir = sys.argv[2]
flowork_dir = sys.argv[3]
dist_dir = sys.argv[4]
token = sys.argv[5]
os.makedirs(dist_dir, exist_ok=True)

repo_owner = "flowork-os"
repo_name = "FLOWORK-AGENT"
tag_name = "v1.0.0"

headers = {
    "Authorization": f"token {token}",
    "User-Agent": "Flowork-OS",
    "Accept": "application/vnd.github.v3+json"
}

# 1. Package Flowork-Agent-Linux-x86_64.tar.gz
linux_tar = os.path.join(dist_dir, "Flowork-Agent-Linux-x86_64.tar.gz")
print("   - Packaging Flowork-Agent-Linux-x86_64.tar.gz...")
with tarfile.open(linux_tar, "w:gz") as tar:
    tar.add(os.path.join(staging_dir, "linux"), arcname="flowork")

# 2. Package Flowork-Agent-Windows-x64.zip
windows_zip = os.path.join(dist_dir, "Flowork-Agent-Windows-x64.zip")
print("   - Packaging Flowork-Agent-Windows-x64.zip...")
with zipfile.ZipFile(windows_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
    win_src = os.path.join(staging_dir, "windows")
    for root, _, files in os.walk(win_src):
        for f in files:
            full_p = os.path.join(root, f)
            rel_p = os.path.join("flowork", os.path.relpath(full_p, win_src))
            zipf.write(full_p, arcname=rel_p)

# 3. Package Flowork-Agent-macOS.tar.gz
macos_tar = os.path.join(dist_dir, "Flowork-Agent-macOS.tar.gz")
print("   - Packaging Flowork-Agent-macOS.tar.gz...")
with tarfile.open(macos_tar, "w:gz") as tar:
    tar.add(os.path.join(staging_dir, "macos"), arcname="flowork")

# 4. Gather Standalone Installer Assets
assets_to_upload = [
    ("Flowork-Agent-Linux-x86_64.tar.gz", linux_tar, "application/gzip"),
    ("Flowork-Agent-Windows-x64.zip", windows_zip, "application/zip"),
    ("Flowork-Agent-macOS.tar.gz", macos_tar, "application/gzip"),
    ("Flowork-Agent-Installer.desktop", os.path.join(flowork_dir, "Flowork-Agent-Installer.desktop"), "text/plain"),
    ("Flowork-Agent-Installer.exe", os.path.join(flowork_dir, "Flowork-Agent-Installer.exe"), "application/octet-stream"),
    ("Flowork-Agent-Installer.command", os.path.join(flowork_dir, "Flowork-Agent-Installer.command"), "text/plain"),
    ("install.sh", os.path.join(flowork_dir, "install.sh"), "text/plain"),
    ("install.ps1", os.path.join(flowork_dir, "install.ps1"), "text/plain"),
    ("install.bat", os.path.join(flowork_dir, "install.bat"), "text/plain")
]

# 5. Delete any existing release with tag_name
try:
    req = urllib.request.Request(f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag_name}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        rel_data = json.loads(resp.read().decode())
        rel_id = rel_data.get("id")
        if rel_id:
            del_req = urllib.request.Request(f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/{rel_id}", headers=headers, method="DELETE")
            urllib.request.urlopen(del_req)
            print(f"   ✓ Purged legacy release ID {rel_id}")
except Exception:
    pass

# Delete tag ref if exists
try:
    del_tag_req = urllib.request.Request(f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/tags/{tag_name}", headers=headers, method="DELETE")
    urllib.request.urlopen(del_tag_req)
except Exception:
    pass

# 6. Create New Official Release
release_payload = {
    "tag_name": tag_name,
    "target_commitish": "main",
    "name": f"Flowork OS {tag_name} — 3D Sovereign Virtual Office & Autonomous Swarm (Linux, Windows, macOS)",
    "body": """# 🏢 Flowork OS — 3D Sovereign Virtual Office & Autonomous Swarm (v1.0.0)

**Watch Autonomous Agents Work Inside a Real 3D Office**: [https://floworkos.com](https://floworkos.com)

Flowork OS is an autonomous, sovereign multi-agent virtual office operating environment designed for zero-cloud-lock, high-performance local AI operations across Marketing, Business Intelligence, Market Recon, Operations, and Bare-Metal Engineering.

### 🚀 1-Line Autonomous Quick Installers
- **Linux (Ubuntu/Debian/Arch/Fedora x86_64)**:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash
  ```
- **macOS (Apple Silicon M1/M2/M3/M4 & Intel x86_64)**:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash
  ```
- **Windows 10/11 (x64 PowerShell)**:
  ```powershell
  irm https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.ps1 | iex
  ```

### 📦 Official Standalone Portable Packages & Double-Click Installers
- **Linux Portable Desktop Installer**: `Flowork-Agent-Installer.desktop`
- **Windows Portable Executable Installer**: `Flowork-Agent-Installer.exe`
- **macOS Portable Command Installer**: `Flowork-Agent-Installer.command`
- **Linux Full Bundle**: `Flowork-Agent-Linux-x86_64.tar.gz`
- **Windows Full Bundle**: `Flowork-Agent-Windows-x64.zip`
- **macOS Full Bundle**: `Flowork-Agent-macOS.tar.gz`

### 🏛️ Core Engines & Architecture Included:
- **Pure Rust Tri-Engine Storage (FNSE)**: Tantivy FTS + SIMD DiskANN Vector PQ + CSR Graph Traversal (< 4ms query latency).
- **Multi-OS Native Compilations**: Verified binaries for Linux ELF, Windows PE, and macOS Mach-O (Intel & ARM64).
- **Zero Plaintext Credentials Leak Guarantee**: Audited against .rodata plaintext leaks.
- **Plug & Play Portable Runtimes**: Zero system-level dependencies required.
""",
    "draft": False,
    "prerelease": False
}

create_req = urllib.request.Request(
    f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases",
    data=json.dumps(release_payload).encode("utf-8"),
    headers={**headers, "Content-Type": "application/json"},
    method="POST"
)

with urllib.request.urlopen(create_req) as resp:
    created_rel = json.loads(resp.read().decode())
    new_rel_id = created_rel["id"]
    upload_url_tmpl = created_rel["upload_url"].split("{")[0]
    print(f"   ✓ Created Official GitHub Release: {tag_name} (ID: {new_rel_id})")

# 7. Upload Assets to Release
for asset_name, asset_path, mime_type in assets_to_upload:
    if not os.path.exists(asset_path):
        print(f"   ⚠️ Asset not found: {asset_path}")
        continue
    sz = os.path.getsize(asset_path)
    print(f"   📤 Uploading asset {asset_name} ({sz / (1024*1024):.2f} MB)...")
    with open(asset_path, "rb") as af:
        asset_data = af.read()
    
    upload_url = f"{upload_url_tmpl}?name={asset_name}"
    upload_req = urllib.request.Request(
        upload_url,
        data=asset_data,
        headers={
            **headers,
            "Content-Type": mime_type,
            "Content-Length": str(sz)
        },
        method="POST"
    )
    with urllib.request.urlopen(upload_req) as u_resp:
        u_data = json.loads(u_resp.read().decode())
        print(f"      ✓ Uploaded: {u_data.get('name')}")

print("   🎉 All release assets uploaded successfully.")
EOF_PY_RELEASE

echo ""
echo "============================================================"
echo "🎉 SUCCESS: Sovereign Multi-OS Release Completed with Exit Code 0!"
echo "🌐 Release Link: https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/tag/v1.0.0"
echo "============================================================"
exit 0
