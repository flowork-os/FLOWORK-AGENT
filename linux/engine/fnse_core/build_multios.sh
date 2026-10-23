#!/usr/bin/env bash
# ==============================================================================
# ⚡ FLOWORK OS — FNSE MULTI-OS RELEASE CROSS-COMPILER
# Builds: Linux (ELF), Windows (PE .exe), macOS Intel (Mach-O), macOS Apple Silicon (Mach-O)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="${HOME}/.local/zig-linux-x86_64-0.13.0:${HOME}/.cargo/bin:$PATH"

DIST_DIR="${SCRIPT_DIR}/dist"
mkdir -p "${DIST_DIR}/linux" "${DIST_DIR}/windows" "${DIST_DIR}/macos"

echo "============================================================"
echo "⚡ FLOWORK NEURAL-STORAGE ENGINE (FNSE) MULTI-OS BUILD"
echo "============================================================"

# 1. Linux x86_64 Build
echo -e "\n📦 [1/4] Compiling for Linux (x86_64-unknown-linux-gnu)..."
cargo zigbuild --manifest-path "${SCRIPT_DIR}/Cargo.toml" --target x86_64-unknown-linux-gnu --release --bin benchmark
cp "${SCRIPT_DIR}/target/x86_64-unknown-linux-gnu/release/benchmark" "${DIST_DIR}/linux/fnse-benchmark"
chmod +x "${DIST_DIR}/linux/fnse-benchmark"
echo "   ✓ Linux binary: ${DIST_DIR}/linux/fnse-benchmark"

# 2. Windows x86_64 Build
echo -e "\n📦 [2/4] Compiling for Windows (x86_64-pc-windows-gnu)..."
cargo zigbuild --manifest-path "${SCRIPT_DIR}/Cargo.toml" --target x86_64-pc-windows-gnu --release --bin benchmark
cp "${SCRIPT_DIR}/target/x86_64-pc-windows-gnu/release/benchmark.exe" "${DIST_DIR}/windows/fnse-benchmark.exe"
echo "   ✓ Windows binary: ${DIST_DIR}/windows/fnse-benchmark.exe"

# 3. macOS Intel (x86_64-apple-darwin) Build
echo -e "\n📦 [3/4] Compiling for macOS Intel (x86_64-apple-darwin)..."
cargo zigbuild --manifest-path "${SCRIPT_DIR}/Cargo.toml" --target x86_64-apple-darwin --release --bin benchmark
cp "${SCRIPT_DIR}/target/x86_64-apple-darwin/release/benchmark" "${DIST_DIR}/macos/fnse-benchmark-x86_64"
chmod +x "${DIST_DIR}/macos/fnse-benchmark-x86_64"
echo "   ✓ macOS Intel binary: ${DIST_DIR}/macos/fnse-benchmark-x86_64"

# 4. macOS Apple Silicon (aarch64-apple-darwin) Build
echo -e "\n📦 [4/4] Compiling for macOS Apple Silicon (aarch64-apple-darwin)..."
cargo zigbuild --manifest-path "${SCRIPT_DIR}/Cargo.toml" --target aarch64-apple-darwin --release --bin benchmark
cp "${SCRIPT_DIR}/target/aarch64-apple-darwin/release/benchmark" "${DIST_DIR}/macos/fnse-benchmark-aarch64"
chmod +x "${DIST_DIR}/macos/fnse-benchmark-aarch64"
echo "   ✓ macOS Apple Silicon binary: ${DIST_DIR}/macos/fnse-benchmark-aarch64"

# 5. Checksum Generation
echo -e "\n🔒 Generating Cryptographic SHA-256 Checksums..."
cd "${DIST_DIR}"
sha256sum linux/* windows/* macos/* > CHECKSUMS.sha256
cat CHECKSUMS.sha256

echo "============================================================"
echo "🎉 SUCCESS: All 4 Multi-OS Binaries Built & Verified Cleanly!"
echo "============================================================"
