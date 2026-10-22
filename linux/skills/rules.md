# 🏛️ Sovereign Skills Universal Rules & Governance Invariants
<!-- Co-authored-by: Flowork OS <agent@floworkos.com> -->

1. **Mandatory GitHub Tri-Repo Synthesis First:** For all skill authoring tasks, the agent MUST research at least 3 trending/high-reputation GitHub repositories in the domain before creating files. Manual authoring is permitted only if no credible repos exist.
2. **20-Keyword Integrity:** Frontmatter `keywords: [...]` in root `SKILL.MD` and `skill.json` MUST contain EXACTLY 20 lowercase English keywords. Single-line JSON array formatting is mandatory.
3. **Strict Line Budget Cap:** Combined line count of `00_overview.md` and `rules.md` MUST NOT exceed 80 lines (target <= 40 lines each) to prevent cognitive bloat.
4. **Nano-Modular Reference Standard (1,500 Char Cap):** Every file in `references/` MUST be strictly <= 1,500 characters and written in 100% strict English. Monolithic files are strictly forbidden.
5. **1-to-1 Keyword Mapping:** `keyword.md` MUST maintain an exact 1-to-1 mapping between a single unique English keyword and a single nano reference file.
6. **Mandatory Modular Blueprint Reflex (`example/`):** Implementation blueprints and code templates MUST reside in `example/`, split into focused, atomic files. Reference files MUST mandate reading the matching example via `view_file`.
7. **Prohibition of Subfolder `SKILL.md` & `trigger.md`:** It is STRICTLY FORBIDDEN to create `SKILL.md` or `trigger.md` inside any individual `skills/<skill_id>/` folder.
8. **Universal Domain Capability Binding:** Skills declare clear domain capabilities and target workflows via semantic metadata in `skill.json` without artificial category constraints.
9. **Companion Tool Binding:** If a skill requires executable programmatic actions, a companion tool in `tools/<tool_id>/` MUST be created and registered in `skill.json`.
10. **Hard-Gate & Independent Subagent Audit:** Prior to concluding a skill authoring task, an independent subagent auditor MUST verify all invariants with Exit Code 0. The session cannot terminate until audit passes.
