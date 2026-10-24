<!-- [FL_INDEX: keywords="flowork os, directory structure, distribution specification, sovereign blueprint, system organs" | purpose="Comprehensive architectural distribution map and directory layout specification for Flowork OS"] -->
# 🏛️ FLOWORK OS DISTRIBUTION SPECIFICATION & ARCHITECTURAL BLUEPRINT
<!-- Co-authored-by: Flowork OS <agent@floworkos.com> -->

This specification defines the authoritative Canonical Directory Layout, subsystem organ roles, and sacred sovereign territorial boundaries between the Flowork OS system root and the user's active project workspace.

---

## 🗺️ 1. Canonical Directory Hierarchy (Engine Root)

```text
flowork/                                # Engine Root & Body of Flowork OS
├── README.MD                           # System architecture, vision, and comprehensive manual
├── STRUCTURE.MD                        # Canonical distribution specification & directory map (This file)
├── VERSION                             # Official Flowork OS release version
│
├── flowork.sh                          # Native Linux/macOS launcher script
├── flowork.bat                         # Native Windows launcher script (CMD / PowerShell)
├── run.sh                              # Linux runtime bootstrap launcher
├── run.bat                             # Windows runtime bootstrap launcher
│
├── system/                             # Core Flowork OS System Organs
│   ├── config.json                     # System turn budget, JIT, and tool visibility config
│   ├── pipeline_dag.json               # Multi-agent autonomous workflow DAG orchestration
│   ├── security_rules/                 # Dynamic security guardrails & AST validators
│   ├── subagent/                       # Autonomous specialist squad roles & swarm definitions
│   │   ├── README.md                   # Squad architecture & specialist contracts overview
│   │   ├── default/                    # Swarm architect, commander & pipeline orchestrator
│   │   ├── backend-engineer/           # Backend logic, API contracts, database, and TDD specialist
│   │   ├── frontend-engineer/          # Canvas UI, responsive stylesheets, and visual QC specialist
│   │   ├── quality-control/            # Quality Assurance gatekeeper (Empirical Exit Code 0 verification)
│   │   └── security-auditor/           # Vulnerability auditor, host-path sanitization, and SAST specialist
│   ├── system_promp/                   # Passive Environmental Triggers (Ambient sensory instincts)
│   │   ├── triggers.json               # Declarative passive trigger switch registry
│   │   ├── rules/                      # Ambient condition evaluation engines (*.rs)
│   │   ├── promp/                      # Behavioral guideline prompt instruction payloads (*.md)
│   │   └── SKILL.md                    # Authoritative passive trigger architecture runbook
│   └── triger/                         # Active Watchdog Triggers (Push-based canvas palette nodes)
│       ├── SKILL.md                    # Authoritative active trigger architecture runbook
│       ├── README.md                   # Active triggers quick guide
│       ├── bitcoin_threshold/          # Example: Crypto market price threshold monitor
│       └── webhook_receiver/           # Example: Ingress HTTP webhook event listener
│
├── apps/                               # Flowork Canvas Visual Applications (Port 18000-18999)
│   ├── apps.json                       # Catalog of active visual canvas applications
│   ├── rules.md                        # Hybrid anatomy iron laws for Canvas applications
│   ├── SKILL.MD                        # Authoritative runbook for authoring visual applications
│   ├── trigger.md                      # Keyword heuristic activation specification
│   └── <app_id>/                       # Individual application directory (Naked GUI + sealed logic)
│
├── tools/                              # Autonomous External Tools (CLI / Headless nano-plugs)
│   ├── README.md                       # Dynamic external tools registry & dual-wing manifest guide
│   ├── rules.md                        # Standard invariants for external tools
│   ├── SKILL.MD                        # Authoritative runbook for authoring external tools
│   ├── trigger.md                      # Keyword radar trigger mappings
│   └── <tool_id>/                      # Standalone tool directory (manifest.json, executable entrypoint)
│
├── skills/                             # Curated Domain SOPs & Specialist On-Demand Runbooks
│   ├── README.md                       # Sovereign skills registry & dual-wing radar guide
│   ├── rules.md                        # Exact 20-keyword YAML frontmatter & nano-modular standards
│   ├── SKILL.MD                        # Master runbook for skill curation and authoring
│   ├── trigger.md                      # Skill radar trigger mappings
│   └── <skill_id>/                     # Individual skill package (00_overview, rules, references)
│
├── flowork/                            # Native Core Binaries (x-flow, flowork-connector on port 9099)
│   └── flowork-connector               # Sealed Universal AI Switchboard Gateway (Port 127.0.0.1:9099)
│
├── canvas-ui/                          # Graphical User Interface (Desktop Webview & Canvas)
│   ├── index.html                      # Root canvas desktop layout
│   ├── styles/                         # Cyberpunk & Flowork Sovereign UI styling
│   └── js/                             # Frontend canvas interaction & state manager
│
├── hooks/                              # Lifecycle Interceptors for Tools & Sessions
│   ├── pre_tool.sh                     # Pre-execution security and guardrail interceptor
│   ├── post_tool.sh                    # Post-execution audit and indexing interceptor
│   ├── block-dangerous-git.sh          # Destructive git command defense guardrail
│   └── link-skills.sh                  # Dynamic skill symlink orchestrator
│
├── mcp/                                # Official Anthropic Model Context Protocol Subsystem
│   ├── README.MD                       # Comprehensive Anthropic MCP (2024-11-05) documentation
│   ├── run.mjs                         # Master MCP Runner (JSON-RPC 2.0 stdio/sse + Canvas legacy)
│   └── mcp_servers.json                # Standard external MCP server configuration registry
│
├── portable-home/                      # Portable User Home Directory (Isolated session & vault storage)
│   └── .flowork/chat_sessions/         # Session history transcripts (isolated outside project workspace)
│
├── .fl_brain/                          # Sovereign Memory Vault (Crystallized atomic solutions)
│   └── memories/                       # Verified solutions verified with Exit Code 0 proof
│
└── .FL_BIN/                            # Supporting Executables & Ephemeral Sandbox
    └── scratch/                        # Isolated temporary testing and scratch directory
```

---

## 🏛️ 2. The Three Sacred Territorial Boundaries

Flowork OS enforces strict demarcation across three isolated territorial zones to ensure absolute system stability, immutability, and zero cross-contamination:

1. **Flowork OS Engine Body (`flowork/`)**:
   - Contains immutable core binaries (`x-flow`, `flowork-connector`), runtime engines, system organs (`system/`, `apps/`, `tools/`, `skills/`), and the Canvas UI.
   - Strictly isolated from the user's active workspace. Engine files must never be contaminated with temporary project files.

2. **User Project Workspace (`{effective_ws}/`)**:
   - The designated project territory where agents analyze, build, and refactor code requested by the user.
   - All scratch scripts and temporary execution artifacts must reside inside `{effective_ws}/.FL_BIN/scratch/` or `.fl_brain/`.

3. **Portable Session & Vault Sanctuary (`portable-home/.flowork/`)**:
   - Encapsulates cryptographic auth vaults, browser profiles, session histories, and local cache with strict permissions (`chmod 600`) without polluting public git tracking.

---

## ⚡ 3. Sovereign System Organ Matrix

| System Organ | Directory Path | Primary Responsibility | Authoritative Specification |
| :--- | :--- | :--- | :--- |
| **Subagents** | `system/subagent/<id>/` | Specialist swarm roles, cognitive styles, and task boundaries | `system/subagent/README.md` |
| **Passive Triggers** | `system/system_promp/` | Ambient zero-daemon sensory instincts evaluated on turn assembly | `system/system_promp/SKILL.md` |
| **Active Triggers** | `system/triger/<id>/` | Persistent watchdog daemons dispatching prompt signals on Canvas | `system/triger/SKILL.md` |
| **Visual Apps** | `apps/<app_id>/` | Human-in-the-loop interactive Canvas applications (Naked GUI) | `apps/SKILL.MD` |
| **External Tools** | `tools/<tool_id>/` | Headless, autonomous nano-plugs with dual-wing manifests | `tools/SKILL.MD` |
| **Sovereign Skills** | `skills/<skill_id>/` | Curated domain runbooks with exact 20 English keywords | `skills/SKILL.MD` |
| **MCP Subsystem** | `mcp/` | Universal Anthropic MCP Client (JSON-RPC 2.0 stdio & sse) | `mcp/README.MD` |
| **AI Switchboard** | `flowork/flowork-connector` | Sealed multi-account AI router and failover on port 9099 | `flowork/flowork-connector` |

---

## 🛡️ 4. System Integrity & Portability Invariants

1. **Zero Hardcoded Paths**: All path references must remain strictly relative or resolved dynamically at runtime (`process.cwd()`, `std::env::current_dir()`).
2. **Sanctity of `@lock`**: Any file or line tagged with `@lock` or `@frozen` directives must NEVER be modified or deleted without explicit authorization.
3. **Empirical Verification Obligation**: All architectural modifications, tool authoring, and bug fixes must be backed by live terminal verification with **Exit Code 0 proof**.
