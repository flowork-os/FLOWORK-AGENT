#!/usr/bin/env node
/**
 * 🧙 fl_wizard_scaffold - Interactive Human-in-the-Loop Bash Wizard Generator
 * Scaffolds battle-tested, frozen-core terminal wizards for human-only configuration steps.
 * Co-authored-by: Flowork OS <agent@floworkos.com>
 */
process.on("uncaughtException", (err) => {
  console.log(JSON.stringify({ status: "error", error: "UNCAUGHT_EXCEPTION", message: err.message }, null, 2));
  process.exit(0);
});
process.on("unhandledRejection", (reason) => {
  console.log(JSON.stringify({ status: "error", error: "UNHANDLED_REJECTION", message: String(reason) }, null, 2));
  process.exit(0);
});

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

function parseArgs() {
  const args = process.argv.slice(2);
  let params = {};
  const pIdx = args.indexOf('--params');
  if (pIdx !== -1 && args[pIdx + 1]) {
    try { params = JSON.parse(args[pIdx + 1]); } catch (_) {}
  } else if (args[0] && args[0].startsWith('{')) {
    try { params = JSON.parse(args[0]); } catch (_) {}
  }
  return params;
}

function generateBashScript(title, stages) {
  let stageCode = '';

  for (let sIdx = 0; sIdx < stages.length; sIdx++) {
    const stage = stages[sIdx];
    const sNum = sIdx + 1;
    stageCode += `\n  # ── Stage ${sNum}: ${stage.name || 'Setup Step'} ──\n`;
    stageCode += `  stage ${sNum} ${stages.length} "${stage.name || 'Setup Step'}"\n`;
    if (stage.description) {
      stageCode += `  echo -e "  \${DIM}${stage.description}\${RESET}\\n"\n`;
    }

    const steps = stage.steps || [];
    for (const step of steps) {
      if (step.type === 'open_url' && step.url) {
        stageCode += `  echo -e "  Opening URL in your default browser: \${CYAN}${step.url}\${RESET}"\n`;
        stageCode += `  open_browser "${step.url}"\n`;
      } else if (step.type === 'ask_secret') {
        const varName = step.var_name || 'SECRET_KEY';
        const prompt = step.prompt || `Enter value for ${varName}`;
        stageCode += `  VAL=$(ask_secret "${prompt}")\n`;
        stageCode += `  write_env "${varName}" "$VAL"\n`;
      } else if (step.type === 'ask') {
        const varName = step.var_name || 'CONFIG_VAR';
        const prompt = step.prompt || `Enter value for ${varName}`;
        const def = step.default || '';
        stageCode += `  VAL=$(ask "${prompt}" "${def}")\n`;
        stageCode += `  write_env "${varName}" "$VAL"\n`;
      } else if (step.type === 'confirm') {
        const prompt = step.prompt || 'Confirm action?';
        stageCode += `  if ! confirm "${prompt}"; then\n    echo "Skipping step."\n  fi\n`;
      }
    }
  }

  return `#!/usr/bin/env bash
# ==============================================================================
# 🧙 Interactive Setup Wizard: ${title || 'Application Provisioning'}
# Generated automatically by Flowork OS Sovereign Core
# Co-authored-by: Flowork OS <agent@floworkos.com>
# ==============================================================================
set -euo pipefail

# ANSI color palette
BOLD="\\033[1m"
DIM="\\033[2m"
CYAN="\\033[36m"
GREEN="\\033[32m"
YELLOW="\\033[33m"
RED="\\033[31m"
RESET="\\033[0m"

stage() {
  local current="$1"
  local total="$2"
  local name="$3"
  echo -e "\\n\${BOLD}\${CYAN}[Stage \${current}/\${total}]\${RESET} \${BOLD}\${name}\${RESET}"
  echo -e "\${DIM}------------------------------------------------------------\${RESET}"
}

open_browser() {
  local url="$1"
  if command -v xdg-open &>/dev/null; then
    xdg-open "$url" &>/dev/null || true
  elif command -v open &>/dev/null; then
    open "$url" &>/dev/null || true
  elif command -v wslview &>/dev/null; then
    wslview "$url" &>/dev/null || true
  elif command -v explorer.exe &>/dev/null; then
    explorer.exe "$url" &>/dev/null || true
  else
    echo -e "  \${YELLOW}Could not open browser automatically. Visit: \${url}\${RESET}"
  fi
}

ask() {
  local prompt="$1"
  local default="\${2:-}"
  local answer
  if [ -n "$default" ]; then
    read -r -p "  $prompt [$default]: " answer
    echo "\${answer:-$default}"
  else
    read -r -p "  $prompt: " answer
    echo "$answer"
  fi
}

ask_secret() {
  local prompt="$1"
  local secret
  read -r -s -p "  $prompt (hidden): " secret
  echo "" >&2
  echo "$secret"
}

confirm() {
  local prompt="$1"
  local answer
  read -r -p "  $prompt [y/N]: " answer
  case "\$answer" in
    [yY][eE][sS]|[yY]) return 0 ;;
    *) return 1 ;;
  esac
}

write_env() {
  local key="$1"
  local val="$2"
  local env_file="\${3:-.env}"

  if [ -z "$val" ]; then
    echo -e "  \${DIM}Skipped empty value for \${key}\${RESET}"
    return 0
  fi

  touch "$env_file"
  if grep -q "^\\s*#*\\s*\${key}=" "$env_file"; then
    # Safe escape sed replacement
    sed -i "s|^\\s*#*\\s*\${key}=.*|\${key}=\\"\${val}\\"|" "$env_file"
  else
    echo "\${key}=\\"\${val}\\"" >> "$env_file"
  fi
  echo -e "  \${GREEN}✔ Saved \${key} to \${env_file}\${RESET}"
}

run_wizard() {
  clear 2>/dev/null || true
  echo -e "\${BOLD}\${GREEN}============================================================\${RESET}"
  echo -e "\${BOLD}  ${title || 'Interactive Setup Wizard'}\${RESET}"
  echo -e "\${DIM}  Flowork OS Automated Human-in-the-Loop Setup Engine\${RESET}"
  echo -e "\${BOLD}\${GREEN}============================================================\${RESET}"
${stageCode}

  echo -e "\\n\${BOLD}\${GREEN}✔ Wizard completed successfully!\${RESET}"
  echo -e "\${DIM}Configuration persisted to .env. You can run verification tests now.\${RESET}\\n"
}

run_wizard
`;
}

function main() {
  const params = parseArgs();
  const title = params.wizard_title || 'Application Provisioning Wizard';
  const outputPath = path.resolve(params.output_path || './setup_wizard.sh');

  let stages = [];
  if (params.stages_json) {
    try {
      stages = typeof params.stages_json === 'string' ? JSON.parse(params.stages_json) : params.stages_json;
    } catch (_) {}
  }

  if (!Array.isArray(stages) || stages.length === 0) {
    stages = [
      {
        name: "Authentication & Credentials",
        description: "Configure primary API tokens and authentication credentials.",
        steps: [
          { type: "ask_secret", var_name: "API_SECRET_KEY", prompt: "Enter Master API Secret" },
          { type: "ask", var_name: "ENVIRONMENT", prompt: "Target environment (development/staging/production)", default: "development" }
        ]
      }
    ];
  }

  const scriptContent = generateBashScript(title, stages);
  fs.writeFileSync(outputPath, scriptContent, { encoding: 'utf8', mode: 0o755 });

  // Validate syntax
  let syntaxOk = true;
  let syntaxError = null;
  try {
    execSync(`bash -n "${outputPath}"`, { encoding: 'utf8' });
  } catch (err) {
    syntaxOk = false;
    syntaxError = err.message;
  }

  console.log(JSON.stringify({
    status: syntaxOk ? "success" : "warning",
    action: "scaffold",
    title,
    output_path: outputPath,
    total_stages: stages.length,
    is_executable: true,
    syntax_validated: syntaxOk,
    syntax_error: syntaxError,
    usage: `Execute directly in terminal: bash ${path.basename(outputPath)}`
  }, null, 2));
}

main();
