#!/usr/bin/env bash
# =============================================================================
# 🚀 FLOWORK OS — GITHUB DEPLOYMENT WRAPPER
# Forwarding to sovereign upload_to_repo.sh
# Co-authored-by: Flowork OS <agent@floworkos.com>
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/upload_to_repo.sh" "$@"
