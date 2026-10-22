#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — ZERO-API SMART AUTONOMOUS LAUNCHER & SELF-UPDATER (LINUX)
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
set -e

# Multi-OS Architecture & Platform Matrix Validation
if [ "$(uname -s 2>/dev/null)" = "Darwin" ]; then
  echo "============================================================"
  echo "🍎 Flowork OS — macOS Support Notice"
  echo "============================================================"
  echo "ℹ️  Flowork OS Stage 1 Release officially supports Linux x86_64 & Windows x64."
  echo "   Native macOS Mach-O binaries are arriving in Stage 2."
  echo "============================================================"
  exit 0
fi

case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "[Flowork] 🪟 Windows environment detected under Bash ($(uname -s))."
    if [ -f "$SCRIPT_DIR/flowork.bat" ]; then
      exec cmd.exe /c "$SCRIPT_DIR\\flowork.bat" "$@"
    elif [ -x "$SCRIPT_DIR/flowork.exe" ]; then
      exec "$SCRIPT_DIR/flowork.exe" "$@"
    elif [ -x "$SCRIPT_DIR/flowork/flowork.exe" ]; then
      exec "$SCRIPT_DIR/flowork/flowork.exe" "$@"
    fi
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"
export FLOWORK_ENGINE_ROOT="$SCRIPT_DIR"
export FLOWORK_PORTABLE_ROOT="$SCRIPT_DIR/portable-home"
export NO_PROXY="127.0.0.1,localhost"
export no_proxy="127.0.0.1,localhost"

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

# Developer Circuit Breaker: Disable auto-update if dev.flowork or dev.flow exists with valid secret key
DEV_MODE_HASH="755edcc90dadcf187a487a608ad0d1140bd9313ddc3763c334e52518fddf15b4"
DEV_LOCKED=false
for dev_file in "$APP_DIR/dev.flowork" "$APP_DIR/dev.flow" "$APP_DIR/portable-home/dev.flowork" "$APP_DIR/portable-home/.flowork/dev.flowork"; do
  if [ -f "$dev_file" ]; then
    FILE_HASH="$(tr -d '\r\n ' < "$dev_file" | sha256sum 2>/dev/null | awk '{print $1}')"
    if [ "$FILE_HASH" = "$DEV_MODE_HASH" ]; then
      DEV_LOCKED=true
      echo "[Flowork] 🛡️ Developer Mode Active ($dev_file authenticated). Auto-update is permanently disabled."
      break
    fi
  fi
done

NEEDS_UPDATE=false
if [ "$DEV_LOCKED" = false ]; then
  if [ ! -f "$APP_DIR/run.sh" ] || [ ! -d "$APP_DIR/system" ] || [ -z "$LOCAL_VER" ]; then
    NEEDS_UPDATE=true
  elif [ -n "$REMOTE_VER" ] && [ "$REMOTE_VER" != "$LOCAL_VER" ]; then
    NEEDS_UPDATE=true
  fi
fi

# 2. Perform Safe Download & Extraction in Sandbox Staging with Checksum Attestation
if [ "$NEEDS_UPDATE" = true ]; then
  if [ -n "$REMOTE_VER" ] || [ ! -f "$APP_DIR/run.sh" ]; then
    echo "[Flowork] ⚡ Synchronizing Flowork OS from upstream (${REMOTE_VER:-initial})..."
    if command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
      mkdir -p "$APP_DIR/.FL_BIN"
      STAGING_DIR="$APP_DIR/.FL_BIN/staging_update_$$"
      mkdir -p "$STAGING_DIR"
      TMP_UPDATE_TAR="$STAGING_DIR/update.tar.gz"
      if curl -fsSL --max-time 120 "$ARCHIVE_URL" -o "$TMP_UPDATE_TAR"; then
        if tar -tzf "$TMP_UPDATE_TAR" >/dev/null 2>&1; then
          mkdir -p "$STAGING_DIR/extracted"
          tar -xzf "$TMP_UPDATE_TAR" \
            --strip-components=2 \
            -C "$STAGING_DIR/extracted" \
            --exclude="FLOWORK-AGENT-main/linux/portable-home/.flowork/*" \
            --exclude="FLOWORK-AGENT-main/linux/.env" \
            --exclude="*launcher.html*" \
            --exclude="*canvas-ui/launcher*" \
            "FLOWORK-AGENT-main/linux" 2>/dev/null || true

          # Purge any launcher files to protect Cloudflare Edge architecture
          rm -f "$STAGING_DIR/extracted/canvas-ui/launcher.html" 2>/dev/null || true
          rm -rf "$STAGING_DIR/extracted/canvas-ui/launcher" 2>/dev/null || true

          # Cryptographic validation against release manifest if available
          UPDATE_VALID=true
          if [ -f "$STAGING_DIR/extracted/x-flow" ]; then
            STAGED_HASH="$(sha256sum "$STAGING_DIR/extracted/x-flow" 2>/dev/null | awk '{print $1}')"
            MANIFEST_URL="https://raw.githubusercontent.com/${UPSTREAM_REPO}/main/linux/release_checksums.json"
            REMOTE_MANIFEST="$STAGING_DIR/release_checksums.json"
            if curl -fsSL --max-time 5 "$MANIFEST_URL" -o "$REMOTE_MANIFEST" 2>/dev/null; then
              if grep -q "$STAGED_HASH" "$REMOTE_MANIFEST" 2>/dev/null; then
                echo "[Flowork] 🔒 Cryptographic checksum verified for x-flow: $STAGED_HASH"
              else
                echo "[Flowork] ⚠️ Staged binary hash ($STAGED_HASH) not in remote release manifest; rejecting update."
                UPDATE_VALID=false
              fi
            fi
          fi

          if [ "$UPDATE_VALID" = true ]; then
            cp -rn "$STAGING_DIR/extracted/"* "$APP_DIR/" 2>/dev/null || cp -r "$STAGING_DIR/extracted/"* "$APP_DIR/" 2>/dev/null || true
            rm -f "$APP_DIR/canvas-ui/launcher.html" 2>/dev/null || true
            rm -rf "$APP_DIR/canvas-ui/launcher" 2>/dev/null || true
            [ -n "$REMOTE_VER" ] && echo "$REMOTE_VER" > "$LOCAL_VER_FILE"
            echo "[Flowork] ✅ Synchronized successfully (v${REMOTE_VER:-$LOCAL_VER})."
          else
            echo "[Flowork] ❌ Synchronize rejected: Cryptographic verification failed."
          fi
        else
          echo "[Flowork] ⚠️ Corrupted update archive detected; aborting extraction."
        fi
      fi
      rm -rf "$STAGING_DIR" 2>/dev/null || true
    else
      echo "[Flowork] ⚠️ curl or tar missing; skipping auto-update."
    fi
  fi
fi

# 3. Ensure Execution Permissions
chmod +x "$APP_DIR/run.sh" 2>/dev/null || true
[ -f "$APP_DIR/x-flow" ] && chmod +x "$APP_DIR/x-flow" 2>/dev/null || true
[ -f "$APP_DIR/flowork/flowork" ] && chmod +x "$APP_DIR/flowork/flowork" 2>/dev/null || true
[ -f "$APP_DIR/flowork/flowork-connector" ] && chmod +x "$APP_DIR/flowork/flowork-connector" 2>/dev/null || true

# 4. Execute Flowork Runtime (Always delegate to run.sh for full port guardian & runtime injection)
if [ -f "$APP_DIR/run.sh" ]; then
  exec "$APP_DIR/run.sh" "$@"
elif [ -x "$APP_DIR/x-flow" ]; then
  exec "$APP_DIR/x-flow" "$@"
elif [ -x "$APP_DIR/flowork/flowork" ]; then
  exec "$APP_DIR/flowork/flowork" "$@"
else
  echo "[Flowork:ERROR] Cannot find runnable Flowork engine in $APP_DIR"
  exit 1
fi
