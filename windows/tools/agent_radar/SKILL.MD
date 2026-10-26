---
name: agent_radar
description: Sovereign dynamic subagent discovery radar and JIT dispatcher matching task intent to specialist squads.
keywords: ["agent", "agents", "agent_discovery", "agent_radar", "agent_search", "delegation", "dispatcher", "orchestration", "persona", "quality_control", "radar", "red_team", "roles", "routing", "security_auditor", "specialist", "subagent", "subagent_discovery", "subagents", "swarm"]
---

# 📡 Sovereign Subagent Radar & JIT Dispatcher

The **Agent Radar** is an autonomous discovery engine that resolves the optimal specialist subagent from `system/subagent/` for any incoming task intent, preventing orchestrator guessing and eliminating prompt bloat.

## 🏛️ Operational SOP

1. **Task Intent Assessment**: Before delegating a complex multi-step task, invoke `agent_radar` with the specific task requirements.
2. **Relevance Scoring**: The radar scores all registered subagents against trigger keywords, departmental domains, and contract invariants.
3. **Seamless Swarm Handoff**: Use the top candidate's `recommended_subagent_call` object (`TypeName`, `Role`, `Model`) directly inside `invoke_subagent`.

## 📜 Execution Contract

- **Command**: `node tools/agent_radar/main.mjs --params '{"query": "<task intent>"}'`
- **Output**: JSON payload with `status: SUCCESS`, `exit_code: 0`, and ranked `candidates`.
