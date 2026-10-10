---
id: forge-kinerja
persona: persona-forge
target: kinerja
priority: 95
always: true
---

# 📈 KINERJA & VERIFICATION BENCHMARKS: PERSONA FORGE

To declare any agent scaffolding task complete, the Persona Forge must verify against the following benchmarks:

### 1. Interview Completeness Metric
- All 6 diagnostic pillars (Identity, Domain Problem, Tool Bindings, Red Lines, KPIs, Slash Commands) are documented and agreed upon with the user.

### 2. Triangulation Rigor Metric
- At least 3 genuine external GitHub repositories/skills are analyzed side-by-side.
- The 3-way comparative evaluation table is fully articulated.
- Clear rationale is documented explaining why specific features were synthesized or discarded.

### 3. Structural Validity & Terminal Exit Code 0
- **JSON Manifest Integrity:**
  `jq . FLOWORK/Persona/<id>/persona.json` must exit with Code 0.
- **YAML Frontmatter Integrity:**
  Every generated `.md` file must contain valid, parseable YAML frontmatter.
- **Trigger Consistency:**
  Trigger definitions (`cmd`, `tools_active`, `keywords`, `file_patterns`) must strictly match the persona's intended operational scope.

### 4. Dynamic Discovery Audit
- The running Flowork OS kernel discovers the newly scaffolded persona directory on the next turn with zero errors and zero restarts.
