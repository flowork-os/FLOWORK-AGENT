#!/usr/bin/env bash
# X-Flow Desktop Canvas Launcher — Sovereign Dynamic Multi-OS Architecture
# Co-authored-by: Flowork OS <agent@floworkos.com>
set -e

# Dynamically resolve root script directory regardless of where it is invoked from or where folder is moved
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
  REMOTE_VER="$(curl -fsSL --max-time 2 "https://raw.githubusercontent.com/flowork-os/FLOWORK-AGENT/main/LINUX/VERSION" 2>/dev/null | tr -d '\r\n ' || true)"
fi

NEEDS_SYNC=false
if [ ! -d "$SCRIPT_DIR/connection" ] || [ ! -d "$SCRIPT_DIR/canvas-ui" ] || [ ! -d "$SCRIPT_DIR/hooks" ] || [ ! -f "$SCRIPT_DIR/models.json" ] || [ -z "$LOCAL_VER" ]; then
  NEEDS_SYNC=true
elif [ -n "$REMOTE_VER" ] && [ "$REMOTE_VER" != "$LOCAL_VER" ]; then
  NEEDS_SYNC=true
fi

if [ "$NEEDS_SYNC" = true ] && [ -n "$REMOTE_VER" ]; then
  echo "[X-Flow] 🌐 Synchronizing ecosystem components (v${REMOTE_VER})..."
  if command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    mkdir -p "$SCRIPT_DIR/.FL_BIN"
    TMP_SYNC_TAR="$SCRIPT_DIR/.FL_BIN/sync_update_$$.tar.gz"
    if curl -fsSL --max-time 120 "https://github.com/flowork-os/FLOWORK-AGENT/archive/refs/heads/main.tar.gz" -o "$TMP_SYNC_TAR"; then
      if tar -tzf "$TMP_SYNC_TAR" >/dev/null 2>&1; then
        tar -xzf "$TMP_SYNC_TAR" \
          --strip-components=2 \
          -C "$SCRIPT_DIR" \
          --exclude="FLOWORK-AGENT-main/LINUX/portable-home/.flowork/*" \
          --exclude="FLOWORK-AGENT-main/LINUX/.env" \
          "FLOWORK-AGENT-main/LINUX" 2>/dev/null || true
        echo "$REMOTE_VER" > "$LOCAL_VER_FILE"
      else
        echo "[X-Flow] ⚠️ Corrupted update archive detected; aborting extraction."
      fi
    fi
    rm -f "$TMP_SYNC_TAR" 2>/dev/null || true
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

# Clean up any lingering old instance, zombie router, & browser processes to guarantee free ports & zero deadlock
if pgrep -x "x-flow" > /dev/null 2>&1 || pgrep -x "flowork" > /dev/null 2>&1 || pgrep -f "flowork/flowork" > /dev/null 2>&1 || pgrep -f "xflow-canvas-profile" > /dev/null 2>&1 || pgrep -f "connection/router.js" > /dev/null 2>&1 || (command -v fuser >/dev/null 2>&1 && fuser 19890/tcp > /dev/null 2>&1); then
  echo "[X-Flow] Stopping previous instance, canvas browser & CONECTOR router..."
  pkill -x "x-flow" 2>/dev/null || true
  pkill -x "flowork" 2>/dev/null || true
  pkill -f "flowork/flowork" 2>/dev/null || true
  command -v fuser >/dev/null 2>&1 && fuser -k 19890/tcp 2>/dev/null || true
  pkill -f "xflow-canvas-profile" 2>/dev/null || true
  pkill -f "connection/router.js" 2>/dev/null || true
  sleep 0.5
fi

# Force kill any stubborn lingering browser or router processes holding profile locks or ports
if pgrep -x "x-flow" > /dev/null 2>&1 || pgrep -x "flowork" > /dev/null 2>&1 || pgrep -f "flowork/flowork" > /dev/null 2>&1 || pgrep -f "xflow-canvas-profile" > /dev/null 2>&1 || pgrep -f "connection/router.js" > /dev/null 2>&1 || (command -v fuser >/dev/null 2>&1 && fuser 19890/tcp > /dev/null 2>&1); then
  pkill -9 -x "x-flow" 2>/dev/null || true
  pkill -9 -x "flowork" 2>/dev/null || true
  pkill -9 -f "flowork/flowork" 2>/dev/null || true
  command -v fuser >/dev/null 2>&1 && fuser -k -9 19890/tcp 2>/dev/null || true
  pkill -9 -f "xflow-canvas-profile" 2>/dev/null || true
  pkill -9 -f "connection/router.js" 2>/dev/null || true
  sleep 0.2
fi

# Clean stale browser singleton locks safely once processes are terminated (Symlink-safe)
if [ -d "/tmp/xflow-canvas-profile" ] && [ ! -L "/tmp/xflow-canvas-profile" ]; then
  rm -f /tmp/xflow-canvas-profile/Singleton* 2>/dev/null || true
fi

# Multi-OS Dynamic Portability Shield:
# If active_workspace.json contains a stale cross-OS path (e.g. Windows paths on Linux)
# or points to a non-existent directory from another PC, purge it so x-flow binds
# dynamically to the current working directory ($SCRIPT_DIR) without hardcoding.
ws_cfg="$SCRIPT_DIR/.flowork/config/active_workspace.json"
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

# Anti-Zombie Sanitization Shield: Guarantee no rogue xflow, .flowork, .flowork_spam, SOUL, or PROMPT_AUDIT exist
[ -d "$SCRIPT_DIR/xflow" ] && rm -rf "$SCRIPT_DIR/xflow" 2>/dev/null || true
[ -d "$SCRIPT_DIR/.flowork" ] && rm -rf "$SCRIPT_DIR/.flowork" 2>/dev/null || true
[ -e "$SCRIPT_DIR/.flowork_spam" ] && rm -rf "$SCRIPT_DIR/.flowork_spam" 2>/dev/null || true
[ -d "$SCRIPT_DIR/SOUL" ] && rm -rf "$SCRIPT_DIR/SOUL" 2>/dev/null || true
[ -d "$SCRIPT_DIR/PROMPT_AUDIT" ] && rm -rf "$SCRIPT_DIR/PROMPT_AUDIT" 2>/dev/null || true
[ -L "$SCRIPT_DIR/connection" ] && rm -f "$SCRIPT_DIR/connection" 2>/dev/null || true

# Explicitly export portable root to ensure child processes and CLI inherit current folder
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

  local bin_dir="${HOME}/.local/bin"
  mkdir -p "$bin_dir" "${HOME}/.config/flowork" 2>/dev/null || true

  # Save current directory as known active installation path
  echo "$SCRIPT_DIR" > "${HOME}/.config/flowork/active_path" 2>/dev/null || true

  # Install Universal Multi-OS Dynamic Launcher into ~/.local/bin
  cat << 'EOF_LAUNCHER' > "$bin_dir/flowork-launcher"
#!/usr/bin/env bash
# Flowork Sovereign Universal Multi-OS Launcher & Dynamic Path Resolver
# Co-authored-by: Flowork OS <agent@floworkos.com>
set -e

CONFIG_FILE="${HOME}/.config/flowork/active_path"
TARGET_DIR=""

# 1. Resolve from desktop entry argument (%k)
if [ -n "$1" ]; then
  RAW="$1"
  RAW="${RAW#file://}"
  CANDIDATE="$(dirname "$(readlink -m "$RAW")")"
  if [ -d "$CANDIDATE/flowork" ] || [ -f "$CANDIDATE/run.sh" ] || [ -f "$CANDIDATE/x-flow" ]; then
    TARGET_DIR="$CANDIDATE"
  fi
fi

# Ignore .desktop metadata argument so child processes don't receive it
if [[ "$1" == *.desktop ]]; then
  shift
fi

# 2. Resolve from saved active path
if [ -z "$TARGET_DIR" ] && [ -f "$CONFIG_FILE" ]; then
  SAVED_DIR="$(cat "$CONFIG_FILE" 2>/dev/null | tr -d '\r\n')"
  if [ -n "$SAVED_DIR" ] && ([ -d "$SAVED_DIR/flowork" ] || [ -f "$SAVED_DIR/run.sh" ] || [ -f "$SAVED_DIR/x-flow" ]); then
    TARGET_DIR="$SAVED_DIR"
  fi
fi

# 3. Resolve from standard path candidates
if [ -z "$TARGET_DIR" ]; then
  for CANDIDATE in \
    "${HOME}/Music/flowork/linux" \
    "${HOME}/Desktop/FLOWORK" \
    "${HOME}/Desktop/xflow" \
    "${HOME}/Music/flowork/xflow" \
    "${HOME}/flowork" \
    "${HOME}/FLOWORK" \
    "${HOME}/Downloads/FLOWORK" \
    "${HOME}/Documents/FLOWORK" \
    "/opt/flowork" \
    "/opt/FLOWORK"; do
    if [ -d "$CANDIDATE/flowork" ] || [ -f "$CANDIDATE/run.sh" ] || [ -f "$CANDIDATE/x-flow" ]; then
      TARGET_DIR="$CANDIDATE"
      break
    fi
  done
fi

# 4. Fast scan fallback if moved to arbitrary location
if [ -z "$TARGET_DIR" ]; then
  FOUND="$(find "$HOME" -maxdepth 4 -name "flowork" -type d 2>/dev/null | head -n 1)"
  if [ -n "$FOUND" ]; then
    CANDIDATE="$(dirname "$FOUND")"
    TARGET_DIR="$CANDIDATE"
  fi
fi

if [ -z "$TARGET_DIR" ]; then
  command -v notify-send >/dev/null 2>&1 && notify-send "Flowork OS" "Cannot find FLOWORK directory." --icon=dialog-error || true
  exit 1
fi

echo "$TARGET_DIR" > "$CONFIG_FILE"
cd "$TARGET_DIR"

# Cloud-Native Self-Healer fallback if launcher clicked on fresh/clean directory
if [ ! -f "$TARGET_DIR/run.sh" ] || [ ! -d "$TARGET_DIR/connection" ] || [ ! -d "$TARGET_DIR/canvas-ui" ] || [ ! -f "$TARGET_DIR/models.json" ]; then
  if command -v curl >/dev/null 2>&1 && command -v tar >/dev/null 2>&1; then
    curl -sL "https://github.com/flowork-os/FLOWORK-AGENT/archive/refs/heads/main.tar.gz" | tar -xzf - --strip-components=2 -C "$TARGET_DIR" "FLOWORK-AGENT-main/LINUX" 2>/dev/null || true
  fi
fi

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
elif [ -f "$TARGET_DIR/x-flow" ]; then
  exec "$TARGET_DIR/x-flow" "$@"
elif [ -f "$TARGET_DIR/flowork/flowork" ]; then
  exec "$TARGET_DIR/flowork/flowork" "$@"
fi
EOF_LAUNCHER
  chmod +x "$bin_dir/flowork-launcher" 2>/dev/null || true
  ln -sf "$bin_dir/flowork-launcher" "$bin_dir/flowork" 2>/dev/null || true

  # Ensure binary is symlinked into ~/.local/bin for global terminal execution
  if [ -f "$SCRIPT_DIR/x-flow" ]; then
    ln -sf "$SCRIPT_DIR/x-flow" "$bin_dir/x-flow" 2>/dev/null || true
  fi

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

  # Register in ~/.icons for universal GTK theme fallback
  mkdir -p "$HOME/.icons" 2>/dev/null || true
  if [ -f "$SCRIPT_DIR/favicon.png" ]; then
    cp -f "$SCRIPT_DIR/favicon.png" "$HOME/.icons/flowork.png" 2>/dev/null || true
    cp -f "$SCRIPT_DIR/favicon.png" "$HOME/.icons/x-flow.png" 2>/dev/null || true
  fi

  # 100% Portable Desktop Entry with Absolute Exec and Path
  local launcher_content="[Desktop Entry]
Version=1.0
Type=Application
Name=X-Flow Canvas Host
Comment=Sovereign Multi-OS Canvas Host & Polyglot Engine
Exec=$bin_dir/flowork-launcher
Path=$SCRIPT_DIR
Icon=flowork
Terminal=false
Categories=Development;
StartupNotify=true
StartupWMClass=127.0.0.1"

  # Sovereign Binary Thumbnailer (Dynamic per-PC $HOME path)
  local thumb_dir="${XDG_DATA_HOME:-$HOME/.local/share}/thumbnailers"
  mkdir -p "$thumb_dir" 2>/dev/null || true
  cat << 'EOF_THUMB' > "$bin_dir/flowork-thumbnailer"
#!/usr/bin/env python3
import sys, os, argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('-i', required=True)
parser.add_argument('-o', required=True)
parser.add_argument('-s', type=int, default=256)
args, _ = parser.parse_known_args()

flowork_icon = os.path.expanduser("~/.icons/flowork.png")
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
  chmod +x "$bin_dir/flowork-thumbnailer" 2>/dev/null || true

  cat << EOF_ENTRY > "$thumb_dir/flowork-executable.thumbnailer"
[Thumbnailer Entry]
TryExec=$bin_dir/flowork-thumbnailer
Exec=$bin_dir/flowork-thumbnailer -i %i -o %o -s %s
MimeType=application/x-executable;application/x-pie-executable;application/x-sharedlib;application/vnd.microsoft.portable-executable;application/x-ms-dos-executable;application/x-msdownload;
EOF_ENTRY

  # Apply metadata custom-icon directly on local binaries
  if command -v gio >/dev/null 2>&1; then
    for target in "$SCRIPT_DIR/x-flow" "$SCRIPT_DIR/x-flow.exe" "$SCRIPT_DIR/flowork" "$SCRIPT_DIR/flowork/flowork" "$SCRIPT_DIR/flowork/flowork.exe"; do
      if [ -e "$target" ]; then
        gio set "$target" metadata::custom-icon-name "flowork" 2>/dev/null || true
        if [ -f "$HOME/.icons/flowork.png" ]; then
          gio set "$target" metadata::custom-icon "file://$HOME/.icons/flowork.png" 2>/dev/null || true
        fi
      fi
    done
  fi

  # Sync to user applications menu
  if [ -d "$apps_dir" ]; then
    echo "$launcher_content" > "$apps_dir/X-Flow.desktop"
    chmod +x "$apps_dir/X-Flow.desktop" 2>/dev/null || true
    ln -sf "$apps_dir/X-Flow.desktop" "$apps_dir/127.0.0.1.desktop" 2>/dev/null || true
    update-desktop-database "$apps_dir" 2>/dev/null || true
  fi

  # Sync to Desktop if folder exists
  if [ -d "$desktop_dir" ]; then
    echo "$launcher_content" > "$desktop_dir/X-Flow.desktop"
    chmod +x "$desktop_dir/X-Flow.desktop" 2>/dev/null || true
    gio set "$desktop_dir/X-Flow.desktop" metadata::trusted true 2>/dev/null || true
    gio set "$desktop_dir/X-Flow.desktop" metadata::trusted yes 2>/dev/null || true
  fi

  echo "$launcher_content" > "$SCRIPT_DIR/X-Flow.desktop"
  chmod +x "$SCRIPT_DIR/X-Flow.desktop" 2>/dev/null || true
  gio set "$SCRIPT_DIR/X-Flow.desktop" metadata::trusted true 2>/dev/null || true
  gio set "$SCRIPT_DIR/X-Flow.desktop" metadata::trusted yes 2>/dev/null || true
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
[ -e "$SCRIPT_DIR/.flowork_spam" ] && rm -rf "$SCRIPT_DIR/.flowork_spam" 2>/dev/null || true
if ! ss -tulpn 2>/dev/null | grep -q ":9099 "; then
  echo "[X-Flow] Launching Sovereign Router Switchboard on port 9099..."
  FLOWORK_PORTABLE_ROOT="$SCRIPT_DIR/portable-home" setsid -f node "$SCRIPT_DIR/connection/router.js" >> "$SCRIPT_DIR/.FL_BIN/conector.log" 2>&1 < /dev/null
  sleep 1
fi

# Cookie Leak Shield: If not authenticated or logged out, wipe /tmp/xflow-canvas-profile safely (Symlink-safe)
AUTH_VAULT="$SCRIPT_DIR/portable-home/.flowork/auth_vault.json"
if [ ! -f "$AUTH_VAULT" ] || grep -q '"is_logged_out": true' "$AUTH_VAULT" 2>/dev/null || ! grep -q '"flowork_token": "eyJ' "$AUTH_VAULT" 2>/dev/null; then
  if [ -L "/tmp/xflow-canvas-profile" ]; then
    rm -f "/tmp/xflow-canvas-profile" 2>/dev/null || true
  elif [ -d "/tmp/xflow-canvas-profile" ]; then
    if [ "$(stat -c '%u' "/tmp/xflow-canvas-profile" 2>/dev/null)" = "$UID" ]; then
      rm -rf "/tmp/xflow-canvas-profile" 2>/dev/null || true
    fi
  fi
fi

echo "[X-Flow] Starting Sovereign Canvas Host on http://127.0.0.1:19890..."
exec ./x-flow "$@"

