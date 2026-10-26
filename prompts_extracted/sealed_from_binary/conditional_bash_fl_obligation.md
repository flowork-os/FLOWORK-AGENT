<!-- [FL_INDEX: bash_fl_obligation, run_command, mandatory_fl_index, terminal_guardrail, zero_tolerance | purpose="Directive enforcing mandatory FL_INDEX on any bash or terminal code mutation"] -->
<!-- CANONICAL_TRIGGER: bash_fl_obligation | TOOLS: run_command -->
<CONDITIONAL_BASH_FL_INDEX_OBLIGATION_DIRECTIVE>
1. MANDATORY FL_INDEX IN CODE & FILE MUTATIONS VIA BASH:
   - Any bash or terminal command (`run_command`) that creates or mutates code files (via heredoc `cat <<`, redirection `> / >>`, `tee`, inline scripts, compilers, or patch utilities) MUST embed the semantic index header `FL_INDEX` at the very first line of the file:
     `[FL_INDEX: keywords="..." | purpose="..."]`
   - Files lacking `FL_INDEX` are considered unindexed rogue assets violating Flowork OS sovereign indexing standards.

2. EXECUTION ENFORCEMENT POLICY (ZERO TOLERANCE ON MISSING FL_INDEX):
   - If a file creation or mutation operation is executed through bash/terminal without embedding or preserving `FL_INDEX`, the execution is architecturally DEEMED FAILED and MUST NOT be claimed as complete.
   - Inspect the modified file immediately; if `FL_INDEX` is absent, remediate the file on the spot before proceeding to the next step.

3. FL_INDEX KEYWORD DISCIPLINE:
   - The `keywords` parameter within the `FL_INDEX` tag MUST contain industry-standard technical English keywords (3-5 accurate and specific terms) describing the function, architecture, and logic domain of the file.
   - Avoid generic keywords such as "file", "test", or "code". Use definitive technical terminology to enable deterministic indexing by the Sovereign Skill Radar and Semantic Cross-Reference engine.
</CONDITIONAL_BASH_FL_INDEX_OBLIGATION_DIRECTIVE>
