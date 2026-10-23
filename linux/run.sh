#!/usr/bin/env bash
# X-Flow Desktop Canvas Launcher — Sovereign Dynamic Multi-OS Architecture
# Co-authored-by: Flowork OS <agent@floworkos.com>
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

# Dynamically resolve root script directory regardless of where it is invoked from or where folder is moved
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
[ -d "$HOME/.cargo/bin" ] && export PATH="$HOME/.cargo/bin:$PATH"

# Inject Portable Runtimes into PATH (Zero-Dependency Plug and Play)
[ -d "$SCRIPT_DIR/runtimes/node/bin" ] && export PATH="$SCRIPT_DIR/runtimes/node/bin:$PATH"
[ -d "$SCRIPT_DIR/runtimes/node" ] && export PATH="$SCRIPT_DIR/runtimes/node:$PATH"
[ -d "$SCRIPT_DIR/runtimes/python/bin" ] && export PATH="$SCRIPT_DIR/runtimes/python/bin:$PATH"
[ -d "$SCRIPT_DIR/runtimes/python" ] && export PATH="$SCRIPT_DIR/runtimes/python:$PATH"
[ -d "$SCRIPT_DIR/portable-home/bin" ] && export PATH="$SCRIPT_DIR/portable-home/bin:$PATH"

# Sovereign Proxy Neutralizer: Exclude local loopback sacred ports from system/VPN proxies
export NO_PROXY="127.0.0.1,localhost"
export no_proxy="127.0.0.1,localhost"

# Ignore .desktop metadata argument if passed by desktop launcher
if [[ "$1" == *.desktop ]]; then
  shift
fi

# -------------------------------------------------------------
# Flowork Sovereign Cloud-Native Self-Healer & Fast Updater (Zero-API)
# -------------------------------------------------------------
LOCAL_VER_FILE="$SCRIPT_DIR/VERSION"
LOCAL_VER=""
[ -f "$LOCAL_VER_FILE" ] && LOCAL_VER="$(cat "$LOCAL_VER_FILE" | tr -d '\r\n ')"
REMOTE_VER=""
if command -v curl >/dev/null 2>&1; then
  REMOTE_VER="$(curl -fsSL --max-time 2 "https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/VERSION" 2>/dev/null | tr -d '\r\n ' || true)"
fi

# Developer Circuit Breaker: Disable auto-update if dev.flowork or dev.flow exists with valid secret key
DEV_MODE_HASH="755edcc90dadcf187a487a608ad0d1140bd9313ddc3763c334e52518fddf15b4"
DEV_LOCKED=false
for dev_file in "$SCRIPT_DIR/dev.flowork" "$SCRIPT_DIR/dev.flow" "$SCRIPT_DIR/portable-home/dev.flowork" "$SCRIPT_DIR/portable-home/.flowork/dev.flowork"; do
  if [ -f "$dev_file" ]; then
    FILE_HASH="$(tr -d '\r\n ' < "$dev_file" | sha256sum 2>/dev/null | awk '{print $1}')"
    if [ "$FILE_HASH" = "$DEV_MODE_HASH" ]; then
      DEV_LOCKED=true
      echo "[X-Flow] 🛡️ Developer Mode Active ($dev_file authenticated). Auto-update is permanently disabled."
      break
    fi
  fi
done

NEEDS_SYNC=false
if [ "$DEV_LOCKED" = false ]; then
  if [ ! -d "$SCRIPT_DIR/canvas-ui" ] || [ ! -d "$SCRIPT_DIR/hooks" ] || [ ! -f "$SCRIPT_DIR/models.json" ] || [ -z "$LOCAL_VER" ]; then
    NEEDS_SYNC=true
  elif [ -n "$REMOTE_VER" ] && [ "$REMOTE_VER" != "$LOCAL_VER" ]; then
    NEEDS_SYNC=true
  fi
fi

if [ "$NEEDS_SYNC" = true ] && [ -n "$REMOTE_VER" ]; then
  echo "[X-Flow] 🌐 Synchronizing ecosystem components (v${REMOTE_VER})..."
  if command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    mkdir -p "$SCRIPT_DIR/.FL_BIN"
    STAGING_DIR="$SCRIPT_DIR/.FL_BIN/staging_update_$$"
    mkdir -p "$STAGING_DIR"
    TMP_SYNC_TAR="$STAGING_DIR/sync_update.tar.gz"
    if curl -fsSL --max-time 120 "https://github.com/flowork-os/FLOWORK-AGENT/archive/refs/heads/main.tar.gz" -o "$TMP_SYNC_TAR"; then
      if tar -tzf "$TMP_SYNC_TAR" >/dev/null 2>&1; then
        mkdir -p "$STAGING_DIR/extracted"
        tar -xzf "$TMP_SYNC_TAR" \
          --strip-components=2 \
          -C "$STAGING_DIR/extracted" \
          --exclude="FLOWORK-AGENT-main/linux/portable-home/.flowork/*" \
          --exclude="FLOWORK-AGENT-main/linux/.env" \
          --exclude="*launcher.html*" \
          --exclude="*canvas-ui/launcher*" \
          "FLOWORK-AGENT-main/linux" 2>/dev/null || true

        # Ensure launcher remains banished from disk (Cloudflare Edge exclusively)
        rm -f "$STAGING_DIR/extracted/canvas-ui/launcher.html" 2>/dev/null || true
        rm -rf "$STAGING_DIR/extracted/canvas-ui/launcher" 2>/dev/null || true

        # Cryptographic & integrity verification against official checksum manifest
        UPDATE_VALID=true
        if [ -f "$STAGING_DIR/extracted/x-flow" ]; then
          STAGED_HASH="$(sha256sum "$STAGING_DIR/extracted/x-flow" 2>/dev/null | awk '{print $1}')"
          MANIFEST_URL="https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/linux/release_checksums.json"
          REMOTE_MANIFEST="$STAGING_DIR/release_checksums.json"
          if curl -fsSL --max-time 5 "$MANIFEST_URL" -o "$REMOTE_MANIFEST" 2>/dev/null; then
            if grep -q "$STAGED_HASH" "$REMOTE_MANIFEST" 2>/dev/null; then
              echo "[X-Flow] 🔒 Cryptographic checksum verified for x-flow: $STAGED_HASH"
            else
              echo "[X-Flow] ⚠️ Staged binary hash ($STAGED_HASH) not in remote release manifest; rejecting update."
              UPDATE_VALID=false
            fi
          fi
        fi

        if [ "$UPDATE_VALID" = true ]; then
          cp -rn "$STAGING_DIR/extracted/"* "$SCRIPT_DIR/" 2>/dev/null || cp -r "$STAGING_DIR/extracted/"* "$SCRIPT_DIR/" 2>/dev/null || true
          rm -f "$SCRIPT_DIR/canvas-ui/launcher.html" 2>/dev/null || true
          rm -rf "$SCRIPT_DIR/canvas-ui/launcher" 2>/dev/null || true
          echo "$REMOTE_VER" > "$LOCAL_VER_FILE"
          echo "[X-Flow] ✅ Synchronized successfully (v${REMOTE_VER})."
        else
          echo "[X-Flow] ❌ Synchronize rejected: Cryptographic verification failed."
        fi
      else
        echo "[X-Flow] ⚠️ Corrupted update archive detected; aborting extraction."
      fi
    fi
    rm -rf "$STAGING_DIR" 2>/dev/null || true
  fi
fi

# Ensure x-flow binary is available safely without broken symlink loops
if [ -L "$SCRIPT_DIR/x-flow" ] && [ ! -e "$SCRIPT_DIR/x-flow" ]; then
  rm -f "$SCRIPT_DIR/x-flow"
fi

if [ ! -f "$SCRIPT_DIR/x-flow" ]; then
  if [ -f "$SCRIPT_DIR/flowork/flowork" ] && [ ! -L "$SCRIPT_DIR/flowork/flowork" ]; then
    cp "$SCRIPT_DIR/flowork/flowork" "$SCRIPT_DIR/x-flow"
    chmod +x "$SCRIPT_DIR/x-flow" 2>/dev/null || true
  elif [ -f "$SCRIPT_DIR/flowork/x-flow" ] && [ ! -L "$SCRIPT_DIR/flowork/x-flow" ]; then
    cp "$SCRIPT_DIR/flowork/x-flow" "$SCRIPT_DIR/x-flow"
    chmod +x "$SCRIPT_DIR/x-flow" 2>/dev/null || true
  fi
fi

# Send desktop notification if GUI is present
if [ -n "$DISPLAY" ] && command -v notify-send >/dev/null 2>&1; then
  local_icon="$SCRIPT_DIR/favicon.png"
  [ ! -f "$local_icon" ] && local_icon="$SCRIPT_DIR/favicon.svg"
  notify-send -i "$local_icon" "X-Flow" "Launching Sovereign Canvas Host..." --expire-time=2000 || true
fi

# Sovereign Multi-OS Port Guardian Helper
sovereign_kill_port() {
  local p="$1"
  if command -v fuser >/dev/null 2>&1; then
    fuser -k -9 "${p}/tcp" 2>/dev/null || true
  fi
  if command -v lsof >/dev/null 2>&1; then
    local lpids
    lpids="$(lsof -ti tcp:"${p}" 2>/dev/null || true)"
    [ -n "$lpids" ] && kill -9 $lpids 2>/dev/null || true
  fi
  if command -v ss >/dev/null 2>&1; then
    local spids
    spids="$(ss -tulpn 2>/dev/null | grep ":${p} " | grep -o 'pid=[0-9]*' | cut -d= -f2 || true)"
    [ -n "$spids" ] && kill -9 $spids 2>/dev/null || true
  fi
}

# Clean up any lingering old instance, zombie router, & browser processes to guarantee free ports & zero deadlock
if pgrep -x "x-flow" > /dev/null 2>&1 || pgrep -x "flowork" > /dev/null 2>&1 || pgrep -f "flowork/flowork" > /dev/null 2>&1 || pgrep -x "flowork-connector" > /dev/null 2>&1 || pgrep -f "flowork-connector" > /dev/null 2>&1 || pgrep -f "xflow-canvas-profile" > /dev/null 2>&1 || pgrep -f "connection/router.js" > /dev/null 2>&1 || (command -v fuser >/dev/null 2>&1 && fuser 19890/tcp > /dev/null 2>&1) || (command -v fuser >/dev/null 2>&1 && fuser 9099/tcp > /dev/null 2>&1); then
  echo "[X-Flow] Stopping previous instance, canvas browser & CONECTOR router..."
  pkill -x "x-flow" 2>/dev/null || true
  pkill -x "flowork" 2>/dev/null || true
  pkill -f "flowork/flowork" 2>/dev/null || true
  pkill -x "flowork-connector" 2>/dev/null || true
  pkill -f "flowork-connector" 2>/dev/null || true
  sovereign_kill_port 19890
  pkill -f "xflow-canvas-profile" 2>/dev/null || true
  pkill -f "connection/router.js" 2>/dev/null || true
  pkill -f "sealed_connector/router.js" 2>/dev/null || true
  sovereign_kill_port 9099
  pkill -f "plugins/.*/engine/server.mjs" 2>/dev/null || true
  pkill -f "enable-unsafe-swiftshader" 2>/dev/null || true
  sleep 0.5
fi

# Force kill any stubborn lingering browser or router processes holding profile locks or ports
if pgrep -x "x-flow" > /dev/null 2>&1 || pgrep -x "flowork" > /dev/null 2>&1 || pgrep -f "flowork/flowork" > /dev/null 2>&1 || pgrep -x "flowork-connector" > /dev/null 2>&1 || pgrep -f "flowork-connector" > /dev/null 2>&1 || pgrep -f "xflow-canvas-profile" > /dev/null 2>&1 || pgrep -f "connection/router.js" > /dev/null 2>&1 || pgrep -f "sealed_connector/router.js" > /dev/null 2>&1 || (command -v fuser >/dev/null 2>&1 && fuser 19890/tcp > /dev/null 2>&1) || (command -v fuser >/dev/null 2>&1 && fuser 9099/tcp > /dev/null 2>&1); then
  pkill -9 -x "x-flow" 2>/dev/null || true
  pkill -9 -x "flowork" 2>/dev/null || true
  pkill -9 -f "flowork/flowork" 2>/dev/null || true
  pkill -9 -x "flowork-connector" 2>/dev/null || true
  pkill -9 -f "flowork-connector" 2>/dev/null || true
  sovereign_kill_port 19890
  sovereign_kill_port 9099
  pkill -9 -f "xflow-canvas-profile" 2>/dev/null || true
  pkill -9 -f "connection/router.js" 2>/dev/null || true
  pkill -9 -f "sealed_connector/router.js" 2>/dev/null || true
  pkill -9 -f "plugins/.*/engine/server.mjs" 2>/dev/null || true
  pkill -9 -f "enable-unsafe-swiftshader" 2>/dev/null || true
  sleep 0.2
fi

# Clean stale browser singleton locks safely once processes are terminated (Symlink-safe)
CANVAS_PROFILE="$SCRIPT_DIR/portable-home/.flowork/browser-profile"
mkdir -p "$CANVAS_PROFILE" 2>/dev/null || true
if [ -d "$CANVAS_PROFILE" ] && [ ! -L "$CANVAS_PROFILE" ]; then
  rm -f "$CANVAS_PROFILE"/Singleton* 2>/dev/null || true
fi

# Multi-OS Dynamic Portability Shield:
# If active_workspace.json contains a stale cross-OS path (e.g. Windows paths on Linux)
# or points to a non-existent directory from another PC, purge it so x-flow binds
# dynamically to the current working directory ($SCRIPT_DIR) without hardcoding.
for ws_cfg in "$SCRIPT_DIR/portable-home/.flowork/config/active_workspace.json" "$SCRIPT_DIR/.flowork/config/active_workspace.json"; do
  if [ -f "$ws_cfg" ]; then
    if grep -q -E '\\\\|[a-zA-Z]:' "$ws_cfg" 2>/dev/null; then
      rm -f "$ws_cfg" 2>/dev/null || true
    elif command -v python3 >/dev/null 2>&1; then
      ws_target="$(python3 -c "import json, sys; d=json.load(open('$ws_cfg')); sys.stdout.write(d.get('path',''))" 2>/dev/null || true)"
      if [ -n "$ws_target" ] && [ ! -d "$ws_target" ]; then
        rm -f "$ws_cfg" 2>/dev/null || true
      fi
    fi
  fi
done

# Anti-Zombie Sanitization Shield: Guarantee no rogue xflow, .flowork, .flowork_spam, SOUL, or PROMPT_AUDIT exist
[ -d "$SCRIPT_DIR/xflow" ] && rm -rf "$SCRIPT_DIR/xflow" 2>/dev/null || true
[ -d "$SCRIPT_DIR/.flowork" ] && rm -rf "$SCRIPT_DIR/.flowork" 2>/dev/null || true
[ -e "$SCRIPT_DIR/.flowork_spam" ] && rm -rf "$SCRIPT_DIR/.flowork_spam" 2>/dev/null || true
[ -d "$SCRIPT_DIR/SOUL" ] && rm -rf "$SCRIPT_DIR/SOUL" 2>/dev/null || true
[ -d "$SCRIPT_DIR/PROMPT_AUDIT" ] && rm -rf "$SCRIPT_DIR/PROMPT_AUDIT" 2>/dev/null || true
[ -L "$SCRIPT_DIR/connection" ] && rm -f "$SCRIPT_DIR/connection" 2>/dev/null || true

# Explicitly export engine root and portable root to ensure child processes and CLI inherit current folder
export FLOWORK_ENGINE_ROOT="$SCRIPT_DIR"
export FLOWORK_PORTABLE_ROOT="$SCRIPT_DIR/portable-home"
export FLOWAI_CLI_HOME="$SCRIPT_DIR/portable-home"

# -------------------------------------------------------------
# Dynamic Sovereign Launcher Sync (Portability Shield)
# Automatically registers/updates .desktop files to current location on any PC
# -------------------------------------------------------------
sync_desktop_launchers() {
  local apps_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  local desktop_dir="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
  local icons_base="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor"

  mkdir -p "$apps_dir" 2>/dev/null || true

  # 1. Sovereign Portable Binaries in portable-home/bin
  local portable_bin="$SCRIPT_DIR/portable-home/bin"
  mkdir -p "$portable_bin" 2>/dev/null || true

  local host_bin="${HOME}/.local/bin"
  local portable_cfg="$SCRIPT_DIR/portable-home/.flowork/config"
  mkdir -p "$host_bin" "$portable_cfg" 2>/dev/null || true

  # Save current directory as known active installation path inside portable-home
  echo "$SCRIPT_DIR" > "$portable_cfg/active_path" 2>/dev/null || true

  # Install Universal Multi-OS Dynamic Launcher into portable-home/bin
  cat << 'EOF_LAUNCHER' > "$portable_bin/flowork-launcher"
#!/usr/bin/env bash
# Flowork Sovereign Universal Multi-OS Launcher & Dynamic Path Resolver
# Co-authored-by: Flowork OS <agent@floworkos.com>
set -e

# Priority 1: Self-relative location (Rock-solid multi-OS portability)
# Since launcher resides in <FLOWORK_ROOT>/portable-home/bin/flowork-launcher
SELF_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")" 2>/dev/null && pwd)"
TARGET_DIR=""

is_flowork_dir() {
  local dir="$1"
  [ -n "$dir" ] && [ -d "$dir" ] && ([ -f "$dir/run.sh" ] || [ -f "$dir/flowork.sh" ] || [ -f "$dir/x-flow" ] || [ -f "$dir/flowork/flowork" ] || [ -f "$dir/flowork.exe" ])
}

if [ -n "$SELF_DIR" ]; then
  CAND_ROOT="$(cd "$SELF_DIR/../.." 2>/dev/null && pwd)"
  if is_flowork_dir "$CAND_ROOT"; then
    TARGET_DIR="$CAND_ROOT"
  fi
fi

# Priority 2: Resolve from desktop entry argument (%k or file path)
if [ -z "$TARGET_DIR" ] && [ -n "$1" ]; then
  RAW="$1"
  RAW="${RAW#file://}"
  CANDIDATE="$(readlink -m "$RAW" 2>/dev/null || echo "$RAW")"
  if [ -f "$CANDIDATE" ]; then
    CANDIDATE="$(dirname "$CANDIDATE")"
  fi
  if is_flowork_dir "$CANDIDATE"; then
    TARGET_DIR="$CANDIDATE"
  elif is_flowork_dir "$CANDIDATE/flowork"; then
    TARGET_DIR="$CANDIDATE/flowork"
  fi
fi

# Ignore .desktop metadata argument so child processes don't receive it
if [[ "$1" == *.desktop ]]; then
  shift
fi

# Priority 3: Resolve from saved active path
CONFIG_FILE="${HOME}/.config/flowork/active_path"
if [ -z "$TARGET_DIR" ] && [ -f "$CONFIG_FILE" ]; then
  SAVED_DIR="$(cat "$CONFIG_FILE" 2>/dev/null | tr -d '\r\n')"
  if is_flowork_dir "$SAVED_DIR"; then
    TARGET_DIR="$SAVED_DIR"
  elif is_flowork_dir "$SAVED_DIR/flowork"; then
    TARGET_DIR="$SAVED_DIR/flowork"
  fi
fi

# Priority 4: Current working directory
if [ -z "$TARGET_DIR" ] && is_flowork_dir "$(pwd)"; then
  TARGET_DIR="$(pwd)"
fi

# Priority 5: Resolve from standard path candidates
if [ -z "$TARGET_DIR" ]; then
  for CANDIDATE in \
    "${HOME}/Desktop/project/flowork" \
    "${HOME}/Desktop/flowork" \
    "${HOME}/flowork" \
    "${HOME}/FLOWORK" \
    "${HOME}/Desktop/FLOWORK" \
    "${HOME}/Desktop/xflow" \
    "${HOME}/Music/flowork/linux" \
    "${HOME}/Music/flowork/xflow" \
    "${HOME}/Downloads/flowork" \
    "${HOME}/Downloads/FLOWORK" \
    "${HOME}/Documents/flowork" \
    "${HOME}/Documents/FLOWORK" \
    "/opt/flowork" \
    "/opt/FLOWORK"; do
    if is_flowork_dir "$CANDIDATE"; then
      TARGET_DIR="$CANDIDATE"
      break
    fi
  done
fi

# Priority 6: Fast scan fallback if moved to arbitrary location
if [ -z "$TARGET_DIR" ]; then
  while IFS= read -r f_candidate; do
    if is_flowork_dir "$f_candidate"; then
      TARGET_DIR="$f_candidate"
      break
    fi
  done < <(find "$HOME" -maxdepth 4 -type d -name "flowork" 2>/dev/null)
fi

# Priority 7: Last resort: scan for run.sh
if [ -z "$TARGET_DIR" ]; then
  FOUND_RUN="$(find "$HOME" -maxdepth 4 -name "run.sh" -type f 2>/dev/null | grep -E "flowork|xflow" | head -n 1 || true)"
  if [ -n "$FOUND_RUN" ]; then
    r_cand="$(dirname "$FOUND_RUN")"
    if is_flowork_dir "$r_cand"; then
      TARGET_DIR="$r_cand"
    fi
  fi
fi

if [ -z "$TARGET_DIR" ] || ! is_flowork_dir "$TARGET_DIR"; then
  command -v notify-send >/dev/null 2>&1 && notify-send "Flowork OS" "Cannot find valid FLOWORK directory." --icon=dialog-error || true
  echo "[flowork-launcher:ERROR] Cannot find valid FLOWORK directory." >&2
  exit 1
fi

echo "$TARGET_DIR" > "$CONFIG_FILE" 2>/dev/null || true
cd "$TARGET_DIR"

# Ensure x-flow binary link
if [ -L "$TARGET_DIR/x-flow" ] && [ ! -e "$TARGET_DIR/x-flow" ]; then
  rm -f "$TARGET_DIR/x-flow"
fi
if [ ! -f "$TARGET_DIR/x-flow" ]; then
  if [ -f "$TARGET_DIR/flowork/flowork" ] && [ ! -L "$TARGET_DIR/flowork/flowork" ]; then
    cp -f "$TARGET_DIR/flowork/flowork" "$TARGET_DIR/x-flow"
  elif [ -f "$TARGET_DIR/flowork/x-flow" ] && [ ! -L "$TARGET_DIR/flowork/x-flow" ]; then
    cp -f "$TARGET_DIR/flowork/x-flow" "$TARGET_DIR/x-flow"
  fi
  chmod +x "$TARGET_DIR/x-flow" 2>/dev/null || true
fi

if [ -f "$TARGET_DIR/run.sh" ]; then
  chmod +x "$TARGET_DIR/run.sh" 2>/dev/null || true
  exec "$TARGET_DIR/run.sh" "$@"
elif [ -f "$TARGET_DIR/flowork.sh" ]; then
  chmod +x "$TARGET_DIR/flowork.sh" 2>/dev/null || true
  exec "$TARGET_DIR/flowork.sh" "$@"
elif [ -f "$TARGET_DIR/x-flow" ]; then
  exec "$TARGET_DIR/x-flow" "$@"
elif [ -f "$TARGET_DIR/flowork/flowork" ]; then
  exec "$TARGET_DIR/flowork/flowork" "$@"
fi
EOF_LAUNCHER
  chmod +x "$portable_bin/flowork-launcher" 2>/dev/null || true
  cp -f "$portable_bin/flowork-launcher" "$portable_bin/flowork" 2>/dev/null || true

  # Optional Host integration: standalone direct copy (no symlinks) into ~/.local/bin if directory exists
  if [ -d "$host_bin" ]; then
    rm -f "$host_bin/flowork-launcher" "$host_bin/flowork" "$host_bin/x-flow" 2>/dev/null || true
    cp -f "$portable_bin/flowork-launcher" "$host_bin/flowork-launcher" 2>/dev/null || true
    cp -f "$portable_bin/flowork-launcher" "$host_bin/flowork" 2>/dev/null || true
    chmod +x "$host_bin/flowork-launcher" "$host_bin/flowork" 2>/dev/null || true
  fi

  # Sovereign Binary Thumbnailer in portable-home/bin
  cat << 'EOF_THUMB' > "$portable_bin/flowork-thumbnailer"
#!/usr/bin/env python3
import sys, os, argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('-i', required=True)
parser.add_argument('-o', required=True)
parser.add_argument('-s', type=int, default=256)
args, _ = parser.parse_known_args()

script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
flowork_icon = os.path.join(script_dir, "favicon.png")
if os.path.exists(flowork_icon):
    try:
        im = Image.open(flowork_icon).convert("RGBA")
        im = im.resize((args.s, args.s), Image.Resampling.LANCZOS)
        im.save(args.o, "PNG")
        sys.exit(0)
    except Exception:
        sys.exit(1)
sys.exit(1)
EOF_THUMB
  chmod +x "$portable_bin/flowork-thumbnailer" 2>/dev/null || true
  if [ -d "$host_bin" ]; then
    rm -f "$host_bin/flowork-thumbnailer" 2>/dev/null || true
    cp -f "$portable_bin/flowork-thumbnailer" "$host_bin/flowork-thumbnailer" 2>/dev/null || true
    chmod +x "$host_bin/flowork-thumbnailer" 2>/dev/null || true
  fi

  local thumb_dir="${XDG_DATA_HOME:-$HOME/.local/share}/thumbnailers"
  mkdir -p "$thumb_dir" 2>/dev/null || true
  cat << EOF_ENTRY > "$thumb_dir/flowork-executable.thumbnailer"
[Thumbnailer Entry]
TryExec=$portable_bin/flowork-thumbnailer
Exec=$portable_bin/flowork-thumbnailer -i %i -o %o -s %s
MimeType=application/x-executable;application/x-pie-executable;application/x-sharedlib;application/vnd.microsoft.portable-executable;application/x-ms-dos-executable;application/x-msdownload;
EOF_ENTRY

  # Ensure favicon is present from canvas-ui if not in root
  if [ ! -f "$SCRIPT_DIR/favicon.png" ] && [ -f "$SCRIPT_DIR/canvas-ui/favicon.png" ]; then
    cp -f "$SCRIPT_DIR/canvas-ui/favicon.png" "$SCRIPT_DIR/favicon.png" 2>/dev/null || true
  fi

  # Ensure icon is registered in standard hicolor icon themes
  if [ -f "$SCRIPT_DIR/favicon.png" ]; then
    for sz in 16 32 48 64 128 256; do
      local sz_dir="$icons_base/${sz}x${sz}/apps"
      mkdir -p "$sz_dir" 2>/dev/null || true
      cp -f "$SCRIPT_DIR/favicon.png" "$sz_dir/x-flow.png" 2>/dev/null || true
      cp -f "$SCRIPT_DIR/favicon.png" "$sz_dir/flowork.png" 2>/dev/null || true
    done
    gtk-update-icon-cache -f "$icons_base" 2>/dev/null || true
  fi

  # Apply metadata custom-icon directly on local binaries using self-contained favicon
  if command -v gio >/dev/null 2>&1; then
    for target in "$SCRIPT_DIR/x-flow" "$SCRIPT_DIR/x-flow.exe" "$SCRIPT_DIR/flowork" "$SCRIPT_DIR/flowork/flowork" "$SCRIPT_DIR/flowork/flowork.exe"; do
      if [ -e "$target" ]; then
        gio set "$target" metadata::custom-icon-name "flowork" 2>/dev/null || true
        if [ -f "$SCRIPT_DIR/favicon.png" ]; then
          gio set "$target" metadata::custom-icon "file://$SCRIPT_DIR/favicon.png" 2>/dev/null || true
        fi
      fi
    done
  fi

  # -------------------------------------------------------------
  # 1. 100% Sovereign Portable Desktop Entry inside Repository / Folder
  # ZERO hardcoded absolute paths, completely agnostic to host / username
  # -------------------------------------------------------------
  local portable_desktop_content="[Desktop Entry]
Version=1.0
Type=Application
Name=X-Flow Canvas Host
Comment=Sovereign Multi-OS Canvas Host & Polyglot Engine
Exec=bash -c 'DIR=\"\$(cd \"\$(dirname \"\$1\")\" 2>/dev/null && pwd)\"; if [ -x \"\$DIR/portable-home/bin/flowork-launcher\" ]; then exec \"\$DIR/portable-home/bin/flowork-launcher\" \"\$@\"; elif [ -f \"\$DIR/run.sh\" ]; then exec \"\$DIR/run.sh\" \"\$@\"; elif [ -f \"./run.sh\" ]; then exec \"./run.sh\" \"\$@\"; fi' _ %k
Icon=flowork
Terminal=false
Categories=Development;
StartupNotify=true
StartupWMClass=127.0.0.1"

  echo "$portable_desktop_content" > "$SCRIPT_DIR/X-Flow.desktop"
  chmod +x "$SCRIPT_DIR/X-Flow.desktop" 2>/dev/null || true
  gio set "$SCRIPT_DIR/X-Flow.desktop" metadata::trusted true 2>/dev/null || true
  gio set "$SCRIPT_DIR/X-Flow.desktop" metadata::trusted yes 2>/dev/null || true

  # -------------------------------------------------------------
  # 2. Host System Desktop Integration (Applications menu & Desktop)
  # Points directly to portable-home/bin/flowork-launcher of this active installation
  # -------------------------------------------------------------
  local host_launcher_content="[Desktop Entry]
Version=1.0
Type=Application
Name=X-Flow Canvas Host
Comment=Sovereign Multi-OS Canvas Host & Polyglot Engine
Exec=$portable_bin/flowork-launcher
Path=$SCRIPT_DIR
Icon=flowork
Terminal=false
Categories=Development;
StartupNotify=true
StartupWMClass=127.0.0.1"

  # Sync to user applications menu
  if [ -d "$apps_dir" ]; then
    echo "$host_launcher_content" > "$apps_dir/X-Flow.desktop"
    chmod +x "$apps_dir/X-Flow.desktop" 2>/dev/null || true
    cp -f "$apps_dir/X-Flow.desktop" "$apps_dir/127.0.0.1.desktop" 2>/dev/null || true
    update-desktop-database "$apps_dir" 2>/dev/null || true
  fi

  # Sync to Desktop if folder exists
  if [ -d "$desktop_dir" ]; then
    echo "$host_launcher_content" > "$desktop_dir/X-Flow.desktop"
    chmod +x "$desktop_dir/X-Flow.desktop" 2>/dev/null || true
    gio set "$desktop_dir/X-Flow.desktop" metadata::trusted true 2>/dev/null || true
    gio set "$desktop_dir/X-Flow.desktop" metadata::trusted yes 2>/dev/null || true
  fi
}
sync_desktop_launchers 2>/dev/null || true

# Rebuild or link if binary missing
if [ -L "./x-flow" ] && [ ! -e "./x-flow" ]; then
  rm -f "./x-flow"
fi

if [ ! -f "./x-flow" ]; then
  if [ -f "./flowork/flowork" ] && [ ! -L "./flowork/flowork" ]; then
    echo "[X-Flow] Copying binary from flowork/flowork..."
    cp -f "./flowork/flowork" "./x-flow"
  elif [ -f "./flowork/x-flow" ] && [ ! -L "./flowork/x-flow" ]; then
    echo "[X-Flow] Copying binary from flowork/x-flow..."
    cp -f "./flowork/x-flow" "./x-flow"
  elif [ -f "core/Cargo.toml" ]; then
    echo "[X-Flow] Building hardened release binary..."
    cargo build --release --manifest-path core/Cargo.toml
    cp -f core/target/release/x-flow ./x-flow
  elif [ -f "../core/Cargo.toml" ]; then
    echo "[X-Flow] Building hardened release binary..."
    cargo build --release --manifest-path ../core/Cargo.toml
    cp -f ../core/target/release/x-flow ./x-flow
  fi
fi

chmod +x ./x-flow
if [ -f "./akungithub" ]; then
  export GITHUB_TOKEN="$(cat ./akungithub | tr -d '\r\n')"
fi

# Ensure Sovereign Router Switchboard (:9099) is running
mkdir -p "$SCRIPT_DIR/.FL_BIN"
mkdir -p "$SCRIPT_DIR/portable-home/.flowork/logs"
is_port_9099_listening() {
  (command -v ss >/dev/null 2>&1 && ss -tulpn 2>/dev/null | grep -q ":9099 ") || \
  (command -v lsof >/dev/null 2>&1 && lsof -i :9099 >/dev/null 2>&1) || \
  (command -v fuser >/dev/null 2>&1 && fuser 9099/tcp >/dev/null 2>&1)
}

launch_router_daemon() {
  local exec_cmd="$1"
  local log_dest="$SCRIPT_DIR/portable-home/.flowork/logs/connector.log"
  if command -v setsid >/dev/null 2>&1; then
    FLOWORK_PORTABLE_ROOT="$SCRIPT_DIR/portable-home" setsid -f $exec_cmd >> "$log_dest" 2>&1 < /dev/null || \
    FLOWORK_PORTABLE_ROOT="$SCRIPT_DIR/portable-home" nohup $exec_cmd >> "$log_dest" 2>&1 < /dev/null &
  else
    FLOWORK_PORTABLE_ROOT="$SCRIPT_DIR/portable-home" nohup $exec_cmd >> "$log_dest" 2>&1 < /dev/null &
  fi
}

start_node_router_fallback() {
  local NODE_BIN="node"
  if [ -x "$SCRIPT_DIR/runtimes/node/bin/node" ]; then
    NODE_BIN="$SCRIPT_DIR/runtimes/node/bin/node"
  elif [ -x "$SCRIPT_DIR/runtimes/node/node" ]; then
    NODE_BIN="$SCRIPT_DIR/runtimes/node/node"
  fi

  local ROUTER_JS=""
  if [ -f "$SCRIPT_DIR/portable-home/.flowork/sealed_connector/router.js" ]; then
    ROUTER_JS="$SCRIPT_DIR/portable-home/.flowork/sealed_connector/router.js"
  elif [ -f "$SCRIPT_DIR/connection/router.js" ]; then
    ROUTER_JS="$SCRIPT_DIR/connection/router.js"
  elif [ -f "$SCRIPT_DIR/connector/router.js" ]; then
    ROUTER_JS="$SCRIPT_DIR/connector/router.js"
  fi

  if [ -n "$ROUTER_JS" ]; then
    echo "[X-Flow] 🚀 Launching Universal Node.js Switchboard Router on port 9099 ($NODE_BIN)..."
    launch_router_daemon "$NODE_BIN $ROUTER_JS"
    for i in {1..12}; do
      if is_port_9099_listening; then
        echo "[X-Flow] ✅ Sovereign Router Switchboard active on port 9099."
        return 0
      fi
      sleep 0.5
    done
    echo "[X-Flow] ⚠️ Warning: Port 9099 not detected within timeout. Check portable-home/.flowork/logs/connector.log"
  else
    echo "[X-Flow] ❌ Error: Neither native connector nor connection/router.js found."
  fi
}

if ! is_port_9099_listening; then
  # Layer 1: CPU Architecture & Instruction Set Pre-flight Check (AVX2/BMI2)
  # Legacy CPUs (e.g. Intel Sandy Bridge, Ivy Bridge i3/i5/i7) lack AVX2 and crash with SIGILL on native bun binary.
  SUPPORTS_AVX2=true
  if [ -f "/proc/cpuinfo" ]; then
    if ! grep -q -E "avx2|bmi2" /proc/cpuinfo 2>/dev/null; then
      SUPPORTS_AVX2=false
    fi
  fi

  NATIVE_LAUNCHED=false
  if [ "$SUPPORTS_AVX2" = true ]; then
    NATIVE_BIN=""
    if [ -x "$SCRIPT_DIR/flowork/flowork-connector" ]; then
      NATIVE_BIN="$SCRIPT_DIR/flowork/flowork-connector"
    elif [ -x "$SCRIPT_DIR/flowork-connector" ]; then
      NATIVE_BIN="$SCRIPT_DIR/flowork-connector"
    fi

    if [ -n "$NATIVE_BIN" ]; then
      echo "[X-Flow] ⚡ Modern CPU detected (AVX2/BMI2 OK). Launching Native Connector Binary on port 9099..."
      launch_router_daemon "$NATIVE_BIN"
      NATIVE_LAUNCHED=true

      # Layer 2: Crash Guard & Liveness Verification
      # Wait up to 3 seconds for port 9099 to bind. If native binary crashes (SIGILL or abort), auto-fallback!
      for i in {1..6}; do
        if is_port_9099_listening; then
          echo "[X-Flow] ✅ Native Connector bound successfully to port 9099."
          break
        fi
        sleep 0.5
      done
    fi
  else
    echo "[X-Flow] 🛡️ CPU Instruction Guard: Older CPU without AVX2 detected (e.g. Ivy/Sandy Bridge)."
    echo "[X-Flow] ⚡ Bypassing native AVX2 binary to prevent SIGILL crash. Engaging universal Node.js router..."
  fi

  # Layer 3: Automatic Failover to Universal Portable Node.js Router if port 9099 is still dead
  if ! is_port_9099_listening; then
    if [ "$NATIVE_LAUNCHED" = true ]; then
      echo "[X-Flow] ⚠️ Native binary failed to bind port 9099 (crashed or SIGILL). Auto-failing over to Node.js router..."
      pkill -9 -x "flowork-connector" 2>/dev/null || true
      pkill -9 -f "flowork-connector" 2>/dev/null || true
    fi
    start_node_router_fallback
  fi
fi

# Cookie Leak Shield: If not authenticated or logged out, wipe browser profile safely
AUTH_VAULT="$SCRIPT_DIR/portable-home/.flowork/auth_vault.json"
if [ ! -f "$AUTH_VAULT" ] || grep -q '"is_logged_out": true' "$AUTH_VAULT" 2>/dev/null || ! grep -q '"flowork_token": "eyJ' "$AUTH_VAULT" 2>/dev/null; then
  if [ -L "$CANVAS_PROFILE" ]; then
    rm -f "$CANVAS_PROFILE" 2>/dev/null || true
  elif [ -d "$CANVAS_PROFILE" ]; then
    rm -rf "$CANVAS_PROFILE" 2>/dev/null || true
  fi
fi

# Sovereign Accelerated Browser Shim: Hardware Acceleration & Zero-CPU SwiftShader Neutralizer
mkdir -p "$SCRIPT_DIR/.FL_BIN"
cat << 'EOF_BROWSER_WRAPPER' > "$SCRIPT_DIR/.FL_BIN/google-chrome"
#!/usr/bin/env bash
REAL_BIN=""
for c in /opt/google/chrome/chrome /usr/bin/google-chrome /usr/bin/google-chrome-stable /usr/bin/chromium /usr/bin/chromium-browser; do
  if [ -x "$c" ] && [ "$(readlink -f "$c" 2>/dev/null)" != "$(readlink -f "$0" 2>/dev/null)" ]; then
    REAL_BIN="$c"
    break
  fi
done

# Filter out CPU-destroying software rasterizers injected by x-flow binary or legacy scripts
CLEAN_ARGS=()
for arg in "$@"; do
  if [ "$arg" = "--enable-unsafe-swiftshader" ] || [ "$arg" = "--use-gl=swiftshader" ]; then
    continue
  fi
  CLEAN_ARGS+=("$arg")
done

if [ -n "$REAL_BIN" ]; then
  exec "$REAL_BIN" --ignore-gpu-blocklist --enable-webgl --enable-accelerated-2d-canvas "${CLEAN_ARGS[@]}"
else
  exec /usr/bin/google-chrome --ignore-gpu-blocklist --enable-webgl --enable-accelerated-2d-canvas "${CLEAN_ARGS[@]}"
fi
EOF_BROWSER_WRAPPER
chmod +x "$SCRIPT_DIR/.FL_BIN/google-chrome" 2>/dev/null || true
cp -f "$SCRIPT_DIR/.FL_BIN/google-chrome" "$SCRIPT_DIR/.FL_BIN/google-chrome-stable" 2>/dev/null || true
cp -f "$SCRIPT_DIR/.FL_BIN/google-chrome" "$SCRIPT_DIR/.FL_BIN/chromium" 2>/dev/null || true
cp -f "$SCRIPT_DIR/.FL_BIN/google-chrome" "$SCRIPT_DIR/.FL_BIN/chromium-browser" 2>/dev/null || true
cp -f "$SCRIPT_DIR/.FL_BIN/google-chrome" "$SCRIPT_DIR/.FL_BIN/brave-browser" 2>/dev/null || true
cp -f "$SCRIPT_DIR/.FL_BIN/google-chrome" "$SCRIPT_DIR/.FL_BIN/microsoft-edge" 2>/dev/null || true
export PATH="$SCRIPT_DIR/.FL_BIN:$PATH"

echo "[X-Flow] Starting Sovereign Canvas Host on http://127.0.0.1:19890..."
exec ./x-flow "$@"

