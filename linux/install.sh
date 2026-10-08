#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — OFFICIAL 1-LINE INSTALLER & AUTONOMOUS BOOTSTRAPPER (LINUX)
# Usage: curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/install.sh | bash
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

REPO="flowork-os/FLOWORK-AGENT"

# Dynamic Installation Directory Resolution:
if [ -n "$FLOWORK_INSTALL_DIR" ]; then
  INSTALL_DIR="$FLOWORK_INSTALL_DIR"
elif [ -n "${BASH_SOURCE[0]}" ] && [ -f "${BASH_SOURCE[0]}" ] && [ "$(basename "${BASH_SOURCE[0]}")" != "bash" ]; then
  PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ "$PARENT_DIR" != "$HOME" ] && [ "$PARENT_DIR" != "/tmp" ]; then
    INSTALL_DIR="$PARENT_DIR"
  else
    INSTALL_DIR="$HOME/Flowork-Agent"
  fi
elif [ "$(pwd)" != "$HOME" ] && [ "$(pwd)" != "/tmp" ]; then
  INSTALL_DIR="$(pwd)"
else
  INSTALL_DIR="$HOME/Flowork-Agent"
fi

echo "============================================================"
echo "⚡ FLOWORK OS — SOVEREIGN AI AGENT INSTALLER (LINUX)"
echo "============================================================"
echo "Target Directory: $INSTALL_DIR"

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo "📥 Fetching Flowork Smart Launcher from official repository..."
curl -fsSL "https://raw.githubusercontent.com/${REPO}/main/linux/flowork.sh" -o "$INSTALL_DIR/flowork.sh"
chmod +x "$INSTALL_DIR/flowork.sh"

# 1. Create global binary link if ~/.local/bin exists or can be created
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR" 2>/dev/null || true
if [ -d "$BIN_DIR" ]; then
  ln -sf "$INSTALL_DIR/flowork.sh" "$BIN_DIR/flowork" 2>/dev/null || true
  echo "✅ Global terminal command registered: flowork"
fi

# 2. Register Desktop Application Shortcut
APP_DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DESKTOP_DIR" 2>/dev/null || true
DESKTOP_ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=Flowork Agent
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

echo "🚀 Launching Flowork Agent engine..."
exec "$INSTALL_DIR/flowork.sh" "$@"
