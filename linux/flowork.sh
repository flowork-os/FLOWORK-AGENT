#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — ZERO-API SMART AUTONOMOUS LAUNCHER & SELF-UPDATER (LINUX)
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"

UPSTREAM_REPO="flowork-os/FLOWORK-AGENT"
RAW_VERSION_URL="https://raw.githubusercontent.com/${UPSTREAM_REPO}/main/linux/VERSION"
ARCHIVE_URL="https://github.com/${UPSTREAM_REPO}/archive/refs/heads/main.tar.gz"

LOCAL_VER_FILE="$APP_DIR/VERSION"
LOCAL_VER=""
[ -f "$LOCAL_VER_FILE" ] && LOCAL_VER="$(cat "$LOCAL_VER_FILE" | tr -d '\r\n ')"

# 1. Fast Sentinel Update Check (Max 2s timeout, zero API quota)
REMOTE_VER=""
if command -v curl >/dev/null 2>&1; then
  REMOTE_VER="$(curl -fsSL --max-time 2 "$RAW_VERSION_URL" 2>/dev/null | tr -d '\r\n ' || true)"
fi

NEEDS_UPDATE=false
if [ ! -f "$APP_DIR/run.sh" ] || [ ! -d "$APP_DIR/connection" ] || [ ! -d "$APP_DIR/Persona" ] || [ -z "$LOCAL_VER" ]; then
  NEEDS_UPDATE=true
elif [ -n "$REMOTE_VER" ] && [ "$REMOTE_VER" != "$LOCAL_VER" ]; then
  NEEDS_UPDATE=true
fi

# 2. Perform Safe Download & Extraction if needed
if [ "$NEEDS_UPDATE" = true ]; then
  if [ -n "$REMOTE_VER" ] || [ ! -f "$APP_DIR/run.sh" ]; then
    echo "[Flowork] ⚡ Synchronizing Flowork OS from upstream (${REMOTE_VER:-initial})..."
    if command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
      mkdir -p "$APP_DIR/.FL_BIN"
      TMP_UPDATE_TAR="$APP_DIR/.FL_BIN/update_$$.tar.gz"
      if curl -fsSL --max-time 120 "$ARCHIVE_URL" -o "$TMP_UPDATE_TAR"; then
        if tar -tzf "$TMP_UPDATE_TAR" >/dev/null 2>&1; then
          # Safe-Extract: Never overwrite user credentials or custom environment
          tar -xzf "$TMP_UPDATE_TAR" \
            --strip-components=2 \
            -C "$APP_DIR" \
            --exclude="FLOWORK-AGENT-main/linux/portable-home/.flowork/*" \
            --exclude="FLOWORK-AGENT-main/linux/.env" \
            "FLOWORK-AGENT-main/linux" 2>/dev/null || true
          [ -n "$REMOTE_VER" ] && echo "$REMOTE_VER" > "$LOCAL_VER_FILE"
          echo "[Flowork] ✅ Synchronized successfully (v${REMOTE_VER:-$LOCAL_VER})."
        else
          echo "[Flowork] ⚠️ Corrupted update archive detected; aborting extraction."
        fi
      fi
      rm -f "$TMP_UPDATE_TAR" 2>/dev/null || true
    else
      echo "[Flowork] ⚠️ curl or tar missing; skipping auto-update."
    fi
  fi
fi

# 3. Ensure Execution Permissions
chmod +x "$APP_DIR/run.sh" 2>/dev/null || true
[ -f "$APP_DIR/x-flow" ] && chmod +x "$APP_DIR/x-flow" 2>/dev/null || true
[ -f "$APP_DIR/flowork/flowork" ] && chmod +x "$APP_DIR/flowork/flowork" 2>/dev/null || true

# 4. Execute Flowork Runtime
if [ -f "$APP_DIR/run.sh" ]; then
  exec "$APP_DIR/run.sh" "$@"
elif [ -x "$APP_DIR/x-flow" ]; then
  exec "$APP_DIR/x-flow" "$@"
else
  echo "[Flowork:ERROR] Cannot find runnable Flowork engine in $APP_DIR"
  exit 1
fi
