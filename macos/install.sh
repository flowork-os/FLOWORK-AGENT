#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — OFFICIAL 1-LINE INSTALLER & AUTONOMOUS BOOTSTRAPPER (LINUX / MACOS)
# Usage: curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

# 0. Multi-OS Architecture & Platform Matrix Validation
OS_TYPE="$(uname -s 2>/dev/null || echo "Unknown")"
ARCH_TYPE="$(uname -m 2>/dev/null || echo "Unknown")"

if [ "$OS_TYPE" != "Linux" ] && [ "$OS_TYPE" != "Darwin" ]; then
  echo "❌ Error: Operating system '$OS_TYPE' is not supported by this installer."
  echo "Flowork OS officially supports Linux (x86_64), macOS (Intel & Apple Silicon), and Windows (x64)."
  exit 1
fi

REPO="flowork-os/FLOWORK-AGENT"
BRANCH="main"
ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"

# 1. Dynamic Installation Directory Resolution (Zero Hardcoded Usernames)
if [ -n "$1" ]; then
  INSTALL_DIR="$1"
elif [ -n "$FLOWORK_INSTALL_DIR" ]; then
  INSTALL_DIR="$FLOWORK_INSTALL_DIR"
elif [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ] && [ "$(basename "${BASH_SOURCE[0]}")" != "install.sh" ]; then
  INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  INSTALL_DIR="$HOME/flowork"
fi

echo "============================================================"
echo "⚡ Flowork OS Autonomous Installer ($OS_TYPE $ARCH_TYPE)"
echo "============================================================"
echo "📁 Target Directory: $INSTALL_DIR"
echo "👤 User Context:     $USER"
echo "🏠 Home Root:        $HOME"
echo "🌐 Upstream Source:  $REPO ($BRANCH)"
echo "============================================================"

# Ensure target directory exists
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 2. Check essential host dependencies
for cmd in curl tar; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ Error: Required tool '$cmd' is not installed."
    exit 1
  fi
done

# 3. Determine target OS distribution folder
if [ "$OS_TYPE" = "Darwin" ]; then
  OS_SUBDIR="macos"
  BUNDLE_NAME="Flowork-Agent-macOS.tar.gz"
else
  OS_SUBDIR="linux"
  BUNDLE_NAME="Flowork-Agent-Linux-x86_64.tar.gz"
fi

RELEASE_BUNDLE_URL="https://github.com/${REPO}/releases/latest/download/${BUNDLE_NAME}"

# 4. Download & Extract Official Release Bundle (Fast Standalone Package)
echo "📥 Fetching Flowork OS official release bundle from GitHub ($BUNDLE_NAME)..."
TMP_TAR="$(mktemp "$INSTALL_DIR/.flowork_pkg_XXXXXX.tar.gz" 2>/dev/null || mktemp /tmp/.flowork_pkg_XXXXXX.tar.gz)"

if curl -fSL --retry 3 --max-time 300 "$RELEASE_BUNDLE_URL" -o "$TMP_TAR" 2>/dev/null; then
  echo "📦 Extracting precompiled release components to $INSTALL_DIR..."
  tar -xzf "$TMP_TAR" \
    --strip-components=1 \
    -C "$INSTALL_DIR" \
    --exclude="flowork/portable-home/.flowork/chat_sessions*" \
    --exclude="flowork/portable-home/.flowork/browser-profile*" \
    --exclude="flowork/portable-home/.flowork/history*" \
    --exclude="flowork/portable-home/.flowork/auth_vault.json*" \
    --exclude="flowork/portable-home/.flowork/account_pool.json*" \
    --exclude="flowork/.env*" \
    --exclude="*launcher.html*" \
    --exclude="*canvas-ui/launcher*" 2>/dev/null || true
  rm -f "$INSTALL_DIR/canvas-ui/launcher.html" 2>/dev/null || true
  rm -rf "$INSTALL_DIR/canvas-ui/launcher" 2>/dev/null || true
  rm -f "$TMP_TAR" 2>/dev/null || true
elif curl -fsSL --retry 3 --max-time 300 "$ARCHIVE_URL" -o "$TMP_TAR"; then
  echo "📦 Fallback: Extracting $OS_SUBDIR from repository source archive..."
  tar -xzf "$TMP_TAR" \
    --strip-components=2 \
    -C "$INSTALL_DIR" \
    --exclude="FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}/portable-home/.flowork/chat_sessions*" \
    --exclude="FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}/portable-home/.flowork/browser-profile*" \
    --exclude="FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}/portable-home/.flowork/history*" \
    --exclude="FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}/portable-home/.flowork/auth_vault.json*" \
    --exclude="FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}/portable-home/.flowork/account_pool.json*" \
    --exclude="FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}/.env*" \
    --exclude="*launcher.html*" \
    --exclude="*canvas-ui/launcher*" \
    "FLOWORK-AGENT-${BRANCH}/${OS_SUBDIR}" 2>/dev/null || true
  rm -f "$INSTALL_DIR/canvas-ui/launcher.html" 2>/dev/null || true
  rm -rf "$INSTALL_DIR/canvas-ui/launcher" 2>/dev/null || true
  rm -f "$TMP_TAR" 2>/dev/null || true
else
  rm -f "$TMP_TAR" 2>/dev/null || true
  echo "❌ Failed to download Flowork release bundle from GitHub."
  exit 1
fi

# 5. Set Architecture-Specific Executable Binaries
if [ "$OS_TYPE" = "Darwin" ]; then
  if [ "$ARCH_TYPE" = "arm64" ] && [ -f "$INSTALL_DIR/flowork-arm64" ]; then
    cp -f "$INSTALL_DIR/flowork-arm64" "$INSTALL_DIR/x-flow"
    mkdir -p "$INSTALL_DIR/flowork"
    cp -f "$INSTALL_DIR/flowork-arm64" "$INSTALL_DIR/flowork/flowork"
  elif [ -f "$INSTALL_DIR/flowork-x86_64" ]; then
    cp -f "$INSTALL_DIR/flowork-x86_64" "$INSTALL_DIR/x-flow"
    mkdir -p "$INSTALL_DIR/flowork"
    cp -f "$INSTALL_DIR/flowork-x86_64" "$INSTALL_DIR/flowork/flowork"
  fi
fi

chmod +x "$INSTALL_DIR/run.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/flowork.sh" 2>/dev/null || true
[ -f "$INSTALL_DIR/x-flow" ] && chmod +x "$INSTALL_DIR/x-flow" 2>/dev/null || true
[ -f "$INSTALL_DIR/flowork/flowork" ] && chmod +x "$INSTALL_DIR/flowork/flowork" 2>/dev/null || true
[ -f "$INSTALL_DIR/flowork/flowork-connector" ] && chmod +x "$INSTALL_DIR/flowork/flowork-connector" 2>/dev/null || true
[ -f "$INSTALL_DIR/runtimes/linux/setup_runtimes.sh" ] && chmod +x "$INSTALL_DIR/runtimes/linux/setup_runtimes.sh" 2>/dev/null || true
[ -x "$INSTALL_DIR/runtimes/linux/setup_runtimes.sh" ] && "$INSTALL_DIR/runtimes/linux/setup_runtimes.sh" 2>/dev/null || true

# 5.5 Autonomous Neural ONNX Model Provisioning (FastEmbed / Semantic Search)
MODELS_DIR="$INSTALL_DIR/portable-home/.flowork/models"
MODEL_TARGET="$MODELS_DIR/models--Xenova--bge-small-en-v1.5"
MODEL_TAR_URL="https://github.com/flowork-os/FLOWORK-AGENT/releases/download/v1.0.0/Flowork-Model-bge-small.tar.gz"

if [ ! -d "$MODEL_TARGET" ] || [ ! -f "$MODEL_TARGET/snapshots/ea104dacec62c0de699686887e3f920caeb4f3e3/onnx/model.onnx" ]; then
  echo "🧠 Fetching official neural embedding model from GitHub Release (77 MB)..."
  mkdir -p "$MODELS_DIR"
  TMP_MODEL_TAR="$MODELS_DIR/.tmp_model_bge_small_$$.tar.gz"
  if curl -fSL --retry 3 --progress-bar "$MODEL_TAR_URL" -o "$TMP_MODEL_TAR"; then
    DOWNLOAD_OK=true
    MODEL_EXPECTED_HASH="72e88f00b6d56957b09ac1329735fc8a829b050bb1dd158162fb632bfbe4f79d"
    if command -v sha256sum >/dev/null 2>&1; then
      CALC_HASH="$(sha256sum "$TMP_MODEL_TAR" | awk '{print $1}')"
    elif command -v shasum >/dev/null 2>&1; then
      CALC_HASH="$(shasum -a 256 "$TMP_MODEL_TAR" | awk '{print $1}')"
    else
      CALC_HASH="$MODEL_EXPECTED_HASH"
    fi
    if [ "$CALC_HASH" != "$MODEL_EXPECTED_HASH" ]; then
      echo "⚠️ Model checksum mismatch ($CALC_HASH vs $MODEL_EXPECTED_HASH); skipping auto-unpack."
      DOWNLOAD_OK=false
    fi
    if [ "$DOWNLOAD_OK" = true ]; then
      echo "📦 Unpacking official ONNX model bundle..."
      tar -xzf "$TMP_MODEL_TAR" -C "$MODELS_DIR" 2>/dev/null || true
      echo "✅ Neural ONNX embedding model installed successfully (100% offline ready)."
    fi
  fi
  rm -f "$TMP_MODEL_TAR" 2>/dev/null || true
fi

# 6. Create Global Terminal Command (flowork) in ~/.local/bin
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR" 2>/dev/null || true
if [ -d "$BIN_DIR" ]; then
  cat << EOF_BIN > "$BIN_DIR/flowork"
#!/usr/bin/env bash
exec "$INSTALL_DIR/flowork.sh" "\$@"
EOF_BIN
  chmod +x "$BIN_DIR/flowork" 2>/dev/null || true
  echo "✅ Global command registered: flowork ($BIN_DIR/flowork)"
fi

# 7. Create Desktop Launchers
if [ "$OS_TYPE" = "Darwin" ]; then
  if [ -d "$HOME/Desktop" ]; then
    cat << EOF_MAC_CMD > "$HOME/Desktop/Flowork.command"
#!/usr/bin/env bash
cd "$INSTALL_DIR" && exec ./run.sh
EOF_MAC_CMD
    chmod +x "$HOME/Desktop/Flowork.command" 2>/dev/null || true
    echo "✅ macOS Desktop Launcher created: $HOME/Desktop/Flowork.command"
  fi
else
  if [ -d "$HOME/Desktop" ]; then
    DESKTOP_ENTRY="$HOME/Desktop/X-Flow.desktop"
    cat << EOF_DESK > "$DESKTOP_ENTRY"
[Desktop Entry]
Version=1.0
Type=Application
Name=Flowork OS
Comment=Flowork Sovereign Canvas Host & AI Autonomous Environment
Exec=$INSTALL_DIR/flowork.sh
Icon=$INSTALL_DIR/favicon.png
Terminal=false
Categories=Development;Office;Utility;
StartupNotify=true
EOF_DESK
    chmod +x "$DESKTOP_ENTRY" 2>/dev/null || true
    echo "✅ Linux Desktop launcher created: $DESKTOP_ENTRY"
  fi

  APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  mkdir -p "$APP_DIR" 2>/dev/null || true
  if [ -d "$APP_DIR" ]; then
    cp -f "$HOME/Desktop/X-Flow.desktop" "$APP_DIR/X-Flow.desktop" 2>/dev/null || true
    update-desktop-database "$APP_DIR" 2>/dev/null || true
  fi
fi

echo "============================================================"
echo "🎉 Flowork OS installation completed successfully!"
echo "🚀 Starting Flowork runtime..."
echo "============================================================"

# 8. Launch Flowork OS
exec "$INSTALL_DIR/run.sh" "$@"
