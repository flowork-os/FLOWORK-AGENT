#!/usr/bin/env bash
# =============================================================================
# 🍎 FLOWORK OS — OFFICIAL MACOS DOUBLE-CLICK INSTALLER BOOTSTRAPPER
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=========================================================="
echo "  ⚡ FLOWORK OS — PORTABLE AGENT INSTALLER (MACOS) ⚡"
echo "=========================================================="
echo "[Portable Mode] Installing in: $DIR"
if [ -f "$DIR/install.sh" ]; then
  bash "$DIR/install.sh" "$DIR"
else
  curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash -s -- "$DIR"
fi
echo ""
read -p "Installation complete. Press Enter to exit..." dummy
