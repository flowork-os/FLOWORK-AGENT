<!-- CANONICAL_TRIGGER: network_har | TOOLS: fl_inspect_web_network_capture -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE STATIC ANALYSIS & FIRST-PARTY RELEASE INTEGRITY AUDIT -->
# NetworkPcapHarAnalysis

Operational directive for offline network traffic forensics, HAR/SAZ packet inspection, and web script payload analysis.

## 1. Diagnostic Step-by-Step Workflow
1. **Offline Capture Ingestion**: Ingest HAR or SAZ captures offline, parsing headers, query params, and payloads via `fl_inspect_web_network_capture`.
2. **Session Observation & Comparison**: Analyze recorded session states with `fl_observe_web_session` and diff multi-session traffic using `fl_compare_web_captures`.
3. **Payload Extraction & Bundle Analysis**: Extract transmitted JavaScript assets via `fl_export_web_scripts` and audit embedded routes using `fl_analyze_web_bundle`.
4. **Module Graph & Semantic Tracing**: Resolve dependency imports with `fl_trace_web_module_imports` and trace client API ingestion dataflows via `fl_trace_javascript_semantics`.

## 2. Defensive Systems Verification & Robustness Analysis
- **Zero Ingress Invariant**: Prohibit re-fetching recorded URLs or spawning live listeners; analyze captures purely offline.
- **Prototype Pollution Prevention**: Validate deserialized network JSON against strict schemas before consumption; reject `__proto__` mutations.
- **Socket & Payload Dissection**: Inspect chunked transfer anomalies and detect socket exhaustion during high-concurrency stream replays.
- **Credential & Token Redaction**: Redact bearer tokens, API keys, and session cookies from exported payloads and diagnostic logs.

## 3. Strict Guardrails & Anti-Hallucination
- **Evidence Digest Lock**: Require valid SHA-256 hashes for all PCAP/HAR bundles prior to forensic evaluation.
- **No Speculative Endpoints**: Disallow asserting unobserved API routes without explicit transaction payloads or static AST matches.
