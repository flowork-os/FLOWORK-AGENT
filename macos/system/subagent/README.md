# 👥 Flowork OS Autonomous Subagent Squad Architecture

The `system/subagent/` subsystem defines specialist squad roles, cognitive styles, tool capabilities, and operational rules for delegated subagents under the Flowork Sovereign Swarm Architecture.

---

## 🏛️ Specialist Squad Roles

| Squad Role | Directory | Primary Directives | Key Tool Contracts |
|---|---|---|---|
| **Architect / Leader** | `default/` | System architecture, task breakdown, pipeline wiring | `team_dispatch`, `view_file`, `write_to_file` |
| **Backend Engineer** | `backend-engineer/` | APIs, database schemas, test-driven logic, performance | `run_command`, `replace_file_content`, `view_file` |
| **Frontend Engineer** | `frontend-engineer/` | Canvas UI, responsive CSS, brand themes, visual QC | `screenshot`, `replace_file_content`, `view_file` |
| **Quality Control (QA)** | `quality-control/` | Terminal verification, Exit Code 0, regression testing | `run_command`, `view_file` |
| **Security Auditor** | `security-auditor/` | Zero-leak audit, token safety, AST & binary inspection | `run_command`, `view_file` |
| **Marketing Strategist**| `marketing-strategist/`| Market dynamics, distribution, user engagement | `search_web`, `read_url_content` |

---

## 📜 Role Configuration Contract

Each subagent folder contains:
1. `agent.json`: Role metadata, model configuration, and capability flags (`enable_mcp_tools`, `enable_write_tools`, etc.).
2. `persona.md`: Behavioral voice, identity, and cognitive posture.
3. `rules.md`: Strict operational guardrails, dispatch tables, and execution doctrines.
4. `task.md`: Template for decomposition and task delegation.
5. `style.json`: Visual canvas node theme, avatar styling, and accent colors.
