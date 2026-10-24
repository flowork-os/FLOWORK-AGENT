<!-- CANONICAL_TRIGGER: transcript_forensics | TOOLS: view_file -->
<AGENT_TRANSCRIPT_FORENSICS_DOCTRINE>
1. ZERO-COPY STREAMING JSONL PARSING (`view_file`):
   - Parse transcripts at `{sessions_dir}/{agent_id}/{session_id}_transcript.jsonl` line-by-line via narrow typed schemas (`jsonl_rows`), skipping discarded payload trees.
   - Guard against decoding multi-megabyte base64 vision/image payloads during indexing with strict budget guards (`ImageDecodeBudgetGuard`).
2. MULTI-TURN GRAPH RECONSTRUCTION & SUBAGENT TOPOLOGY:
   - Reconstruct conversation lineages into typed turns, linking subagent delegations (`{sessions_dir}/{subagent_id}/{session_id}_transcript.jsonl`) to parent root sessions without circular traversal.
   - Index sidecar metadata (`{sessions_dir}/{agent_id}/.meta.json`) alongside event streams to resolve tool calls, thoughts, and outputs without re-scanning raw execution history.
3. GRANULAR STEP TOKEN AUDITING & TRAJECTORY METRICS:
   - Extract exact cumulative and per-step token counts (`input_tokens`, `output_tokens`, `cache_read_tokens`) across models and agents.
   - Maintain historical telemetry without inflating SQLite stores by persisting compact tallies (`UsageTally`) and discarding ephemeral tool noise.
</AGENT_TRANSCRIPT_FORENSICS_DOCTRINE>
