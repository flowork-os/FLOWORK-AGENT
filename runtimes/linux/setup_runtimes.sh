#!/usr/bin/env bash
# [FL_INDEX: setup_runtimes, linux_portable, node_embed, python_embed, zero_dependency | purpose="Autonomous zero-installer provisioner for Flowork OS portable runtimes on Linux"]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIMES_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NODE_DIR="$RUNTIMES_ROOT/node"
PYTHON_DIR="$RUNTIMES_ROOT/python"

echo "============================================================"
echo "⚡ Flowork OS — Autonomous Runtime Provisioner (Linux)"
echo "============================================================"

ARCH="$(uname -m)"
case "$ARCH" in
    x86_64)
        NODE_ARCH="x64"
        ;;
    aarch64|arm64)
        NODE_ARCH="arm64"
        ;;
    *)
        echo "⚠️ Unsupported CPU architecture for pre-packaged binary: $ARCH"
        exit 0
        ;;
esac

# 1. Check Node.js
if [ -x "$NODE_DIR/bin/node" ]; then
    echo "✅ Portable Node.js already present: $NODE_DIR/bin/node ($("$NODE_DIR/bin/node" -v))"
elif command -v node >/dev/null 2>&1 && node -v >/dev/null 2>&1; then
    echo "✅ Host Node.js detected: $(which node) ($(node -v))"
elif command -v bun >/dev/null 2>&1; then
    echo "✅ Host Bun runtime detected: $(which bun) (v$(bun --version))"
else
    echo "📥 Provisioning portable standalone Node.js for Linux ($NODE_ARCH)..."
    mkdir -p "$NODE_DIR"
    NODE_VERSION="v20.18.0"
    NODE_TAR="node-${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"
    TMP_TAR="/tmp/${NODE_TAR}"
    
    if curl -sSL "https://nodejs.org/dist/${NODE_VERSION}/${NODE_TAR}" -o "$TMP_TAR"; then
        tar -xJf "$TMP_TAR" -C "$NODE_DIR" --strip-components=1
        rm -f "$TMP_TAR"
        echo "✅ Portable Node.js installed to $NODE_DIR/bin/node"
    else
        echo "⚠️ Failed to fetch portable Node.js tarball."
    fi
fi

# 2. Check Python 3
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Host Python 3 detected: $(which python3) ($(python3 --version))"
else
    echo "ℹ️ Python 3 is optional. Can be installed via system package manager (apt/dnf/pacman)."
fi

echo "============================================================"
echo "✅ Runtime verification finished."
echo "============================================================"
