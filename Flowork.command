#!/usr/bin/env bash
# =============================================================================
# 🍎 FLOWORK OS — OFFICIAL MACOS DOUBLE-CLICK LAUNCHER
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
echo "=========================================================="
echo "  ⚡ FLOWORK OS — MACOS LAUNCHER ⚡"
echo "=========================================================="
if [ -f "./run.sh" ]; then
  exec ./run.sh "$@"
elif [ -f "./flowork.sh" ]; then
  exec ./flowork.sh "$@"
else
  echo "[Flowork] Initializing installation..."
  if [ -f "./install.sh" ]; then
    bash "./install.sh" "$DIR"
  else
    curl -fsSL https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/install.sh | bash -s -- "$DIR"
  fi
  if [ -f "./run.sh" ]; then
    exec ./run.sh "$@"
  fi
fi
