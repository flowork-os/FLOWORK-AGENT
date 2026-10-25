# 🏛️ Agent Radar Operational Invariants & Rules

1. **Deterministic Discovery First**: Always query `agent_radar` or `agent_registry.json` before assuming a subagent capability.
2. **Contract Honoring**: Strictly respect the subagent's `territory.allowed_extensions` and `territory.forbidden_extensions`.
3. **Zero Hallucination**: Never invoke a subagent with a fabricated `TypeName` that does not exist in `agent_registry.json`.
4. **Exit Code 0 Verification**: All routing results must yield valid JSON with `exit_code: 0`.
5. **Strict English I/O**: Queries and responses must adhere strictly to English language standards.
