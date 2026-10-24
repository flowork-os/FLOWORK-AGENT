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
curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash -s -- "$DIR"
echo ""
read -p "Installation complete. Press Enter to exit..." dummy
