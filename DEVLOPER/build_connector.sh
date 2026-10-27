#!/usr/bin/env bash
# ==============================================================================
# ⚡ FLOWORK OS — CONNECTOR MULTI-OS COMPILER SCRIPT
# Single Source of Truth Output: /home/mrflow/flowork/flowork
# Co-authored-by: Flowork OS <agent@floworkos.com>
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONNECTOR_DIR="${SCRIPT_DIR}/connector"
FLOWORK_LIVE_DIR="${FLOWORK_LIVE_DIR:-/home/mrflow/flowork}"
FLOWORK_BIN_DIR="${FLOWORK_LIVE_DIR}/flowork"

mkdir -p "${FLOWORK_BIN_DIR}"

if ! command -v bun &> /dev/null; then
    echo "❌ Error: bun is not installed or not in PATH."
    exit 1
fi

echo "============================================================"
echo "⚡ FLOWORK CONNECTOR — MULTI-OS BINARY BUILDER"
echo "============================================================"
echo "📁 Source Dir:      ${CONNECTOR_DIR}/router.js"
echo "🎯 Flowork Target:  ${FLOWORK_BIN_DIR}"
echo "============================================================"

# 1. Linux x64 (Universal Baseline for Intel Core i3/i5/i7 & Non-AVX2 CPUs)
echo -e "\n📦 [1/4] Compiling Linux Connector Binary (Universal Baseline)..."
bun build --compile --minify --target=bun-linux-x64-baseline "${CONNECTOR_DIR}/router.js" --outfile "${FLOWORK_BIN_DIR}/flowork-connector"
chmod +x "${FLOWORK_BIN_DIR}/flowork-connector"
cp -f "${FLOWORK_BIN_DIR}/flowork-connector" "${FLOWORK_BIN_DIR}/flowork-connector-linux"
echo "   ✓ Linux connector: ${FLOWORK_BIN_DIR}/flowork-connector"

# 2. Windows x64 (Universal Baseline for Intel Core i3/i5/i7 & Non-AVX2 CPUs)
echo -e "\n📦 [2/4] Cross-compiling Windows Connector Binary (Universal Baseline)..."
bun build --compile --minify --target=bun-windows-x64-baseline "${CONNECTOR_DIR}/router.js" --outfile "${FLOWORK_BIN_DIR}/flowork-connector-windows.exe"
cp -f "${FLOWORK_BIN_DIR}/flowork-connector-windows.exe" "${FLOWORK_BIN_DIR}/flowork-connector.exe"
echo "   ✓ Windows connector: ${FLOWORK_BIN_DIR}/flowork-connector-windows.exe & flowork-connector.exe"

# 3. macOS Intel x64 (Universal Baseline)
echo -e "\n📦 [3/4] Cross-compiling macOS Intel Connector Binary (Universal Baseline)..."
bun build --compile --minify --target=bun-darwin-x64-baseline "${CONNECTOR_DIR}/router.js" --outfile "${FLOWORK_BIN_DIR}/flowork-connector-darwin-x64"
chmod +x "${FLOWORK_BIN_DIR}/flowork-connector-darwin-x64"
cp -f "${FLOWORK_BIN_DIR}/flowork-connector-darwin-x64" "${FLOWORK_BIN_DIR}/flowork-connector-darwin-x86_64"
echo "   ✓ macOS Intel connector: ${FLOWORK_BIN_DIR}/flowork-connector-darwin-x64"

# 4. macOS Apple Silicon (ARM64)
echo -e "\n📦 [4/4] Cross-compiling macOS ARM Connector Binary..."
bun build --compile --minify --target=bun-darwin-arm64 "${CONNECTOR_DIR}/router.js" --outfile "${FLOWORK_BIN_DIR}/flowork-connector-darwin-arm64"
chmod +x "${FLOWORK_BIN_DIR}/flowork-connector-darwin-arm64"
echo "   ✓ macOS ARM connector: ${FLOWORK_BIN_DIR}/flowork-connector-darwin-arm64"

echo "============================================================"
echo "🎉 Connector Build Completed Successfully!"
echo "   All 4 OS binaries updated in: ${FLOWORK_BIN_DIR}"
echo "============================================================"
