#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — OFFICIAL 1-LINE INSTALLER & AUTONOMOUS BOOTSTRAPPER
# Usage: curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

REPO="flowork-os/FLOWORK-AGENT"

# Dynamic Installation Directory Resolution:
# 1. If script is saved on disk, install right in its directory:
if [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 2. If explicit environment variable passed:
elif [ -n "$FLOWORK_INSTALL_DIR" ]; then
  INSTALL_DIR="$FLOWORK_INSTALL_DIR"
# 3. If executed via piped curl inside a custom subfolder:
elif [ "$(pwd)" != "$HOME" ]; then
  INSTALL_DIR="$(pwd)"
# 4. Fallback if piped in raw $HOME:
else
  INSTALL_DIR="$HOME/flowork"
fi

echo "============================================================"
echo "⚡ Flowork OS Autonomous Installer"
echo "============================================================"
echo "Target Directory: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "📥 Downloading Flowork Smart Launcher..."
curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/LINUX/flowork.sh" -o "$INSTALL_DIR/flowork.sh"
chmod +x "$INSTALL_DIR/flowork.sh"

# Create global binary link if ~/.local/bin exists or can be created
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR" 2>/dev/null || true
if [ -d "$BIN_DIR" ]; then
  ln -sf "$INSTALL_DIR/flowork.sh" "$BIN_DIR/flowork" 2>/dev/null || true
  echo "✅ Global command linked: flowork"
fi

echo "🚀 Initializing ecosystem components in $INSTALL_DIR..."
exec "$INSTALL_DIR/flowork.sh" "$@"
