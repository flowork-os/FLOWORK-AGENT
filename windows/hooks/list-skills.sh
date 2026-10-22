#!/usr/bin/env bash
# Flowork OS Sovereign Engineering Doctrines Lister
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO"
find doctrines -name DOCTRINE.md -not -path '*/node_modules/*' | sed 's|^\./||' | sort
