#!/usr/bin/env bash
# =============================================================================
# 🍎 FLOWORK OS — OFFICIAL MACOS RUNTIME LAUNCHER
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ARCH="$(uname -m 2>/dev/null || echo "x86_64")"

# Ensure binary exists for current architecture
if [ "$ARCH" = "arm64" ] && [ -f "$SCRIPT_DIR/flowork-arm64" ]; then
  cp -f "$SCRIPT_DIR/flowork-arm64" "$SCRIPT_DIR/x-flow"
elif [ -f "$SCRIPT_DIR/flowork-x86_64" ]; then
  cp -f "$SCRIPT_DIR/flowork-x86_64" "$SCRIPT_DIR/x-flow"
elif [ -f "$SCRIPT_DIR/flowork/flowork" ]; then
  cp -f "$SCRIPT_DIR/flowork/flowork" "$SCRIPT_DIR/x-flow"
fi

chmod +x "$SCRIPT_DIR/x-flow" 2>/dev/null || true

# Start connector if present
if [ -x "$SCRIPT_DIR/flowork/flowork-connector" ] && ! lsof -i :9099 >/dev/null 2>&1; then
  "$SCRIPT_DIR/flowork/flowork-connector" >/dev/null 2>&1 &
fi

# Launch default browser after short delay
(sleep 2 && (open "http://127.0.0.1:19890" 2>/dev/null || true)) &

# Launch core
exec "$SCRIPT_DIR/x-flow" "$@"
