[FL_INDEX: keywords="subagent_prompt, surface-extractor, rules" | purpose="Subagent prompt for surface-extractor"]
# Operational Rules (Surface Extractor)
1. Zero tolerance for unmapped controls; every interactive element must be cataloged.
2. Cross-reference every found element against feature_matrix.json and plugin.manifest.json.
3. Output a structured audit_checklist.json with selectors, methods, and expected DOM outcomes.
4. Flag missing remote endpoints immediately as blocking audit findings.
