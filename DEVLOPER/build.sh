#!/usr/bin/env bash
# ==============================================================================
# ⚡ FLOWORK OS — OFFICIAL DEVELOPER MULTI-OS BINARY BUILD SCRIPT
# Single Source of Truth Output: /home/mrflow/flowork/flowork
# Co-authored-by: Flowork OS <agent@floworkos.com>
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="${SCRIPT_DIR}/core"
OUTPUT_DIR="${SCRIPT_DIR}/build_output"
FLOWORK_LIVE_DIR="${FLOWORK_LIVE_DIR:-/home/mrflow/flowork}"
FLOWORK_BIN_DIR="${FLOWORK_LIVE_DIR}/flowork"

export PATH="${HOME}/.cargo/bin:${HOME}/.local/zig-linux-x86_64-0.13.0:$PATH"
export SDKROOT="${SDKROOT:-/home/mrflow/.cache/macos-sdk/MacOSX12.3.sdk}"

mkdir -p "${OUTPUT_DIR}/linux" "${OUTPUT_DIR}/windows" "${OUTPUT_DIR}/macos"
mkdir -p "${FLOWORK_BIN_DIR}"

echo "============================================================"
echo "⚡ FLOWORK OS — MULTI-OS RELEASE BINARY BUILDER"
echo "============================================================"
echo "📁 Source Dir:      ${CORE_DIR}"
echo "📦 Build Output:    ${OUTPUT_DIR}"
echo "🎯 Flowork Target:  ${FLOWORK_BIN_DIR}"
echo "============================================================"

# Step 0: Autonomous Architectural Validation & Zero-Trust Gatekeeper
echo "🔍 [Step 0] Executing Sovereign Release Gatekeeper (Anti-Regression)..."
python3 "${SCRIPT_DIR}/hooks/validate_sovereignty.py"

# Check compiler tools
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: cargo is not installed or not in PATH."
    exit 1
fi

TARGET="${1:-all}"

build_linux() {
    echo -e "\n📦 [1/4] Compiling Linux Release Binary (Fat LTO + Stripped)..."
    cargo build --manifest-path "${CORE_DIR}/Cargo.toml" --release --bin flowork
    cp -v "${CORE_DIR}/target/release/flowork" "${OUTPUT_DIR}/linux/x-flow"
    cp -v "${CORE_DIR}/target/release/flowork" "${OUTPUT_DIR}/flowork"
    chmod +x "${OUTPUT_DIR}/linux/x-flow" "${OUTPUT_DIR}/flowork"
    
    # Direct output to live Flowork installation
    install -m 755 "${CORE_DIR}/target/release/flowork" "${FLOWORK_BIN_DIR}/flowork"
    install -m 755 "${CORE_DIR}/target/release/flowork" "${FLOWORK_BIN_DIR}/flowork-linux"
    install -m 755 "${CORE_DIR}/target/release/flowork" "${FLOWORK_LIVE_DIR}/x-flow"
    echo "   ✓ Linux binary installed to: ${FLOWORK_BIN_DIR}/flowork & ${FLOWORK_LIVE_DIR}/x-flow"
}

build_windows() {
    echo -e "\n📦 [2/4] Cross-compiling Windows Release Binary (x86_64-pc-windows-gnu)..."
    if command -v cargo-zigbuild &> /dev/null || cargo zigbuild --version &> /dev/null; then
        cargo zigbuild --manifest-path "${CORE_DIR}/Cargo.toml" --target x86_64-pc-windows-gnu --release --bin flowork
        cp -v "${CORE_DIR}/target/x86_64-pc-windows-gnu/release/flowork.exe" "${OUTPUT_DIR}/windows/x-flow.exe"
        cp -v "${CORE_DIR}/target/x86_64-pc-windows-gnu/release/flowork.exe" "${OUTPUT_DIR}/flowork.exe"
        
        # Direct output to live Flowork installation
        install -m 755 "${CORE_DIR}/target/x86_64-pc-windows-gnu/release/flowork.exe" "${FLOWORK_BIN_DIR}/flowork.exe"
        echo "   ✓ Windows binary installed to: ${FLOWORK_BIN_DIR}/flowork.exe"
    else
        echo "   ⚠️ cargo-zigbuild not found, skipping Windows cross-compilation."
    fi
}

build_macos_x86() {
    echo -e "\n📦 [3/4] Cross-compiling macOS Intel Binary (x86_64-apple-darwin)..."
    if command -v cargo-zigbuild &> /dev/null || cargo zigbuild --version &> /dev/null; then
        cargo zigbuild --manifest-path "${CORE_DIR}/Cargo.toml" --target x86_64-apple-darwin --release --bin flowork
        cp -v "${CORE_DIR}/target/x86_64-apple-darwin/release/flowork" "${OUTPUT_DIR}/macos/x-flow-x86_64"
        cp -v "${CORE_DIR}/target/x86_64-apple-darwin/release/flowork" "${OUTPUT_DIR}/flowork-darwin-x86_64"
        chmod +x "${OUTPUT_DIR}/macos/x-flow-x86_64" "${OUTPUT_DIR}/flowork-darwin-x86_64"
        
        # Direct output to live Flowork installation
        install -m 755 "${CORE_DIR}/target/x86_64-apple-darwin/release/flowork" "${FLOWORK_BIN_DIR}/flowork-darwin-x86_64"
        echo "   ✓ macOS Intel binary installed to: ${FLOWORK_BIN_DIR}/flowork-darwin-x86_64"
    else
        echo "   ⚠️ cargo-zigbuild not found, skipping macOS x86 cross-compilation."
    fi
}

build_macos_arm() {
    echo -e "\n📦 [4/4] Cross-compiling macOS Apple Silicon Binary (aarch64-apple-darwin)..."
    if command -v cargo-zigbuild &> /dev/null || cargo zigbuild --version &> /dev/null; then
        cargo zigbuild --manifest-path "${CORE_DIR}/Cargo.toml" --target aarch64-apple-darwin --release --bin flowork
        cp -v "${CORE_DIR}/target/aarch64-apple-darwin/release/flowork" "${OUTPUT_DIR}/macos/x-flow-arm64"
        cp -v "${CORE_DIR}/target/aarch64-apple-darwin/release/flowork" "${OUTPUT_DIR}/flowork-darwin-arm64"
        chmod +x "${OUTPUT_DIR}/macos/x-flow-arm64" "${OUTPUT_DIR}/flowork-darwin-arm64"
        
        # Direct output to live Flowork installation
        install -m 755 "${CORE_DIR}/target/aarch64-apple-darwin/release/flowork" "${FLOWORK_BIN_DIR}/flowork-darwin-arm64"
        echo "   ✓ macOS ARM binary installed to: ${FLOWORK_BIN_DIR}/flowork-darwin-arm64"
    else
        echo "   ⚠️ cargo-zigbuild not found, skipping macOS ARM cross-compilation."
    fi
}

case "$TARGET" in
    linux)
        build_linux
        ;;
    windows)
        build_windows
        ;;
    macos)
        build_macos_x86
        build_macos_arm
        ;;
    all)
        build_linux
        build_windows
        build_macos_x86
        build_macos_arm
        ;;
    *)
        echo "Usage: $0 [linux|windows|macos|all]"
        exit 1
        ;;
esac

echo -e "\n🔒 Generating Cryptographic SHA-256 Checksums..."
cd "${OUTPUT_DIR}"
find . -type f ! -name "CHECKSUMS.sha256" -exec sha256sum {} + > CHECKSUMS.sha256 || true
echo "============================================================"
echo "🎉 Build Script Execution Completed Successfully!"
echo "   Output available directly in: ${FLOWORK_BIN_DIR}"
echo "============================================================"
