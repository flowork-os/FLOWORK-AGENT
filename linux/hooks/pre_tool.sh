#!/usr/bin/env bash
# [FL_INDEX: refine pre tool hook git check | COT: Only pass terminal commands to block-dangerous-git.sh to avoid false positives on file content text | AT: 2026-10-21T20:38:03Z]
# [FLOWORKOS:HOOK] Pre-Tool Interceptor
set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Protect against destructive Git operations (only for terminal/run_command execution)
TOOL_NAME=$(echo "$PAYLOAD" | grep -o '"tool":"[^"]*"' | cut -d'"' -f4 || echo "")
if [[ "$TOOL_NAME" == "run_command" ]] || [[ -z "$TOOL_NAME" && "$PAYLOAD" =~ "CommandLine" ]]; then
  if echo "$PAYLOAD" | grep -qi "git"; then
    if [[ -f "$SCRIPT_DIR/block-dangerous-git.sh" ]]; then
      "$SCRIPT_DIR/block-dangerous-git.sh" "$PAYLOAD"
    fi
  fi
fi

# 2. General Guardrails: Block catastrophic disk-wipe patterns
if echo "$PAYLOAD" | grep -qE "(rm[[:space:]]+-[a-zA-Z]*rf[[:space:]]+/[[:space:]]*$|mkfs\.|dd[[:space:]]+if=.*of=/dev/)"; then
  echo "BLOCKED by pre_tool hook: Catastrophic disk destruction command detected!" >&2
  exit 2
fi

exit 0
