#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — PORTABLE 1-LINE INSTALLER & AUTONOMOUS BOOTSTRAPPER (LINUX)
# Installs directly in the folder where executed or placed (100% Portable).
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

REPO="flowork-os/FLOWORK-AGENT"

# 1. 100% Portable Directory Resolution:
# Always prioritize the folder where the user called the installer!
if [ -n "$1" ]; then
  INSTALL_DIR="$(cd "$1" 2>/dev/null && pwd || echo "$1")"
elif [ -n "$FLOWORK_INSTALL_DIR" ]; then
  INSTALL_DIR="$FLOWORK_INSTALL_DIR"
elif [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ] && [ "$(basename "${BASH_SOURCE[0]}")" != "bash" ]; then
  INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  INSTALL_DIR="$(pwd)"
fi

echo "============================================================"
echo "⚡ FLOWORK OS — PORTABLE SOVEREIGN AGENT INSTALLER (LINUX)"
echo "============================================================"
echo "[Portable Mode] Target Directory: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "📥 Fetching Flowork Smart Launcher from official repository..."
TMP_SH="$(mktemp "$INSTALL_DIR/.flowork_tmp_XXXXXX.sh" 2>/dev/null || mktemp /tmp/.flowork_tmp_XXXXXX.sh)"
if curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/linux/flowork.sh" -o "$TMP_SH"; then
  if grep -q "FLOWORK OS" "$TMP_SH" 2>/dev/null; then
    mv -f "$TMP_SH" "$INSTALL_DIR/flowork.sh"
    chmod 755 "$INSTALL_DIR/flowork.sh"
  else
    rm -f "$TMP_SH"
    echo "❌ Downloaded script verification failed."
    exit 1
  fi
else
  rm -f "$TMP_SH"
  echo "❌ Failed to download Flowork Smart Launcher."
  exit 1
fi

# 2. Register Global Command Link (if ~/.local/bin exists or can be created)
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR" 2>/dev/null || true
if [ -d "$BIN_DIR" ]; then
  ln -sf "$INSTALL_DIR/flowork.sh" "$BIN_DIR/flowork" 2>/dev/null || true
  echo "✅ Global terminal command registered: flowork"
fi

# 3. Register Desktop Shortcut pointing to this portable installation
APP_DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DESKTOP_DIR" 2>/dev/null || true
DESKTOP_ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=Flowork Agent (Portable)
GenericName=Sovereign AI Agent & Canvas Host
Comment=Flowork OS Autonomous AI Agent Switchboard
Exec=/bin/bash -c \"cd '$INSTALL_DIR' && ./flowork.sh\"
Icon=system-run
Terminal=true
Categories=Development;Utility;
StartupNotify=true"

echo "$DESKTOP_ENTRY" > "$APP_DESKTOP_DIR/flowork-agent.desktop"
chmod +x "$APP_DESKTOP_DIR/flowork-agent.desktop" 2>/dev/null || true

if [ -d "$HOME/Desktop" ]; then
  echo "$DESKTOP_ENTRY" > "$HOME/Desktop/Flowork-Agent.desktop"
  chmod +x "$HOME/Desktop/Flowork-Agent.desktop" 2>/dev/null || true
  echo "✅ Desktop shortcut created: ~/Desktop/Flowork-Agent.desktop"
fi

echo "🚀 Launching Flowork Agent in $INSTALL_DIR..."
exec "$INSTALL_DIR/flowork.sh" "$@"
