#!/usr/bin/env bash
PAYLOAD="$1"

if [ -z "$PAYLOAD" ]; then
    exit 0
fi

# 1. Catastrophic disk destruction prevention
if echo "$PAYLOAD" | grep -Eq 'rm\s+-[a-zA-Z]*rf\s+/|format\s+[a-zA-Z]:'; then
    echo "BLOCKED by pre_tool hook: Catastrophic disk destruction command detected!" >&2
    exit 2
fi

# 2. Block destructive git commands like git reset --hard
if echo "$PAYLOAD" | grep -Eq 'git\s+reset\s+--hard|git\s+clean\s+-[a-zA-Z]*f'; then
    echo "BLOCKED by pre_tool hook: Destructive git command detected!" >&2
    exit 2
fi

exit 0
