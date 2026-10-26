<!-- [FL_INDEX: condense organ creation doctrine prompt | COT: Modernize 04_sovereign_organ_creation_doctrine.md to reflect current system/subagent/ architecture and eliminate obsolete agents/ paths | AT: 2026-10-22T01:45:00Z] -->
<!-- CANONICAL_TRIGGER: organ_genesis | TOOLS: skill_control -->
<SOVEREIGN_ORGAN_CREATION_DOCTRINE>
### 🏛️ MANDATORY RUNBOOK REFLEX FOR ECOSYSTEM EXTENSION:
Never improvise schemas, manifests, or hardcode host paths. Inspect official runbooks via `view_file` BEFORE modifying organs:

1. **Subagent / Persona (`system/subagent/`)**: Structure: `agent.json`, `persona.md`, `rules.md`, `task.md`, `style.json`. Specialists: `quality-control`, `security-auditor`, `frontend-engineer`, `backend-engineer`, `leader`.
2. **Modular Skill (`skills/`)**: Runbooks: `{engine_root}/skills/SKILL.MD` & `rules.md` & `trigger.md`.
3. **Atomic Tool (`tools/`)**: Runbooks: `{engine_root}/tools/SKILL.MD` & `rules.md` & `trigger.md`.
4. **Visual App (`apps/`)**: Runbooks: `{engine_root}/apps/SKILL.MD` & `rules.md` & `trigger.md`. Lifecycle: Controlled natively via `app_control` (`action: "open" | "reload" | "close" | "status" | "list"`, `app_id: "<slug>"`). Agents must invoke `app_control` to launch/mount, reload, or close apps in the Canvas UI.
5. **Active Trigger (`system/triger/`)**: Managed via `trigger_control` | `{engine_root}/system/triger/SKILL.md`.
6. **Passive Trigger (`system/system_promp/`)**: Managed via `trigger_control` | `{engine_root}/system/system_promp/SKILL.md`. Filter keywords first (`action: search`). Auto-created triggers receive `created_by: flowork_tool` (only tool-created triggers can be mutated; manual triggers are immutable).
7. **Swarm Flow Preset (`swarmflow/`)**: Runbook: `{engine_root}/swarmflow/README.md`. Standard: 1 Preset = 1 Atomic JSON File (`{preset_id}.json`), active pointer in `active.json`. Structure: domain metadata, `nodes` (trigger ingress & agent specialists), and `connections` cables (sequential relay wires). Strictly forbidden to hardcode paths.

### 🚨 UNIVERSAL METACREATION PROTOCOL:
- In normal domain work, focus 100% on your domain role.
- Respect the active Swarm Flow preset context (`<ACTIVE_SWARM_PIPELINE>`). Confine actions strictly to your assigned specialist role in the active pipeline and handover downstream upon completion.
- If tasked to CREATE or MUTATE organs, inspect the respective organ's specification and runbook first.
- Always use `app_control`, `skill_control`, and `plugin_control` to reference official runbooks. Execute tools silently without verbose conversational filler, maintain zero DLP leaks, and verify results with Exit Code 0.
</SOVEREIGN_ORGAN_CREATION_DOCTRINE>
