#!/usr/bin/env bash
# Flowork OS Sovereign Git Safety Guardrail
# 100% Aligned with Rust Kernel `x-flow` (`check_git_safety` in core/src/tools.rs)
# Blocks destructive git commands before terminal execution

if [[ -n "$1" ]]; then
  INPUT="$1"
elif [ ! -t 0 ]; then
  INPUT=$(cat)
else
  INPUT=""
fi

# Extract command string supporting JSON (.tool_input.command / .CommandLine / .command / .cmd) or raw text
COMMAND=""
if [[ "$INPUT" =~ ^[[:space:]]*\{ ]]; then
  if command -v python3 >/dev/null 2>&1; then
    COMMAND=$(echo "$INPUT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tool_input', {}).get('command') or data.get('CommandLine') or data.get('command') or data.get('cmd') or '')" 2>/dev/null || true)
  elif command -v node >/dev/null 2>&1; then
    COMMAND=$(echo "$INPUT" | node -e "let d=''; process.stdin.on('data', c=>d+=c); process.stdin.on('end', ()=>{ try { const j=JSON.parse(d); console.log(j?.tool_input?.command || j?.CommandLine || j?.command || j?.cmd || ''); } catch(e){} });" 2>/dev/null || true)
  elif command -v jq >/dev/null 2>&1; then
    COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .CommandLine // .command // .cmd // empty' 2>/dev/null || true)
  fi
  if [ -z "$COMMAND" ]; then
    COMMAND=$(echo "$INPUT" | grep -oE '"(tool_input"\s*:\s*\{[^}]*"command"|CommandLine|command|cmd)"\s*:\s*"[^"]*"' | sed -E 's/.*"([^"]+)"$/\1/' || true)
  fi
fi

if [ -z "$COMMAND" ]; then
  COMMAND="$INPUT"
fi

COMMAND="$(echo "$COMMAND" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
[ -z "$COMMAND" ] && exit 0

# Check explicit authorization override (Rust Kernel Parity)
if echo "$COMMAND" | grep -qE -- "(--allow-destructive-git|--flowork-force-allow)"; then
  exit 0
fi

CMD_LOWER="$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')"

# 1. Force push (git push ... --force, -f, origin +branch, upstream +branch)
if echo "$CMD_LOWER" | grep -qE "(^|[;&|[:space:]])push([[:space:]]|$)" && \
   echo "$CMD_LOWER" | grep -qE -- "(--force|([[:space:]]-f([[:space:]]|=|$))|origin[[:space:]]+\+|upstream[[:space:]]+\+)"; then
  echo "BLOCKED: Perintah '$COMMAND' memuat operasi force push git. Doktrin Kedaulatan Flowork OS melarang force push untuk mencegah penimpaan riwayat repository. Gunakan branch baru atau sertakan flag '--allow-destructive-git'." >&2
  exit 2
fi

# 2. Hard reset (git reset --hard)
if echo "$CMD_LOWER" | grep -qE "(^|[;&|[:space:]])reset([[:space:]]|$)" && \
   echo "$CMD_LOWER" | grep -qE -- "--hard"; then
  echo "BLOCKED: Perintah '$COMMAND' memuat 'reset --hard'. Doktrin Kedaulatan Flowork OS melarang hard reset yang menghapus perubahan uncommitted / commits. Sertakan flag '--allow-destructive-git' jika dikehendaki." >&2
  exit 2
fi

# 3. Clean purge (git clean -f, -fd, -xdf, etc.)
if echo "$CMD_LOWER" | grep -qE "(^|[;&|[:space:]])clean([[:space:]]|$)" && \
   echo "$CMD_LOWER" | grep -qE -- "(-[a-zA-Z]*f|--force)"; then
  echo "BLOCKED: Perintah '$COMMAND' memuat 'git clean -f' (pemusnahan file untracked). Doktrin Kedaulatan Flowork OS melarang pemusnahan berkas tanpa otorisasi tertulis eksplisit." >&2
  exit 2
fi

# 4. Branch force delete (git branch -D, --delete --force)
if echo "$COMMAND" | grep -qE -- "branch[[:space:]]+-D" || \
   (echo "$CMD_LOWER" | grep -qE "(^|[;&|[:space:]])branch([[:space:]]|$)" && echo "$CMD_LOWER" | grep -qE -- "--delete" && echo "$CMD_LOWER" | grep -qE -- "--force"); then
  echo "BLOCKED: Perintah '$COMMAND' memuat penghapusan paksa cabang git (-D). Doktrin Kedaulatan Flowork OS melarang penghapusan cabang unmerged tanpa flag '--allow-destructive-git'." >&2
  exit 2
fi

# 5. Discard changes (git checkout . or git restore .)
if echo "$CMD_LOWER" | grep -qE "(checkout|restore)" && \
   echo "$CMD_LOWER" | grep -qE "[[:space:]]\.([[:space:]]|$)"; then
  echo "BLOCKED: Perintah '$COMMAND' memuat pembatalan seluruh perubahan kerja ('checkout .' / 'restore .'). Doktrin Kedaulatan Flowork OS melindungi integritas file kerja aktif." >&2
  exit 2
fi

exit 0
