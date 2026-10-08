---
id: gemini-1m-token-upstream-shield
title: Gemini 1M Token Upstream Overflow & Context Shield Solution
created_at: 2026-10-08T10:31:30Z
category: llm-gateway-optimization
status: resolved
keywords:
  - gemini
  - token-limit
  - upstream-400
  - context-shield
  - function-response
  - trajectory-pruning
  - account-rotator
  - cloud-code-pa
  - deep-audit-tools
  - payload-compaction
  - self-healing-proxy
  - linux
---

# Upstream 400 Inference Failure Root Cause & Resolution

## Problem
Agent requests frequently fail with:
`[Flowork Engine Notice] Permintaan inferensi tidak dapat diproses upstream. Silakan coba kembali.`
after multiple steps of deep audits or diagnostics (`audit_security`, `detect_hardcode`, long bash logs, large file reads).

## Root Cause
1. Deep diagnostic tools return hundreds of findings in large unconstrained arrays (e.g. 120+ SAST findings, 172+ violations with duplicate objects and long code snippets).
2. Trajectory history accumulates across 10-15 steps, ballooning outbound request payloads past 2.6 MB (>1,048,576 tokens).
3. Google Gemini's Cloud Code endpoint enforces a strict 1,048,576 token hard ceiling, returning `HTTP 400: The input token count exceeds the maximum number of tokens allowed 1048576.`
4. The proxy gateway treated non-geoblock HTTP 400 responses as fatal, masking the true error behind a generic fallback notice.

## Solution Implemented
1. **Flowork Context Shield (Proactive)**:
   - Added `pruneOversizedToolOutputs` in `connection/tool_virtualizer.js` and `connection/antygravity/account_rotator.js`.
   - Capped array findings within tool responses to the top 25 items while retaining summary metrics (`total_issues`, `health_score`, `exit_code`).
   - Sliced raw string dumps exceeding 30,000 characters using head/tail retention.
   - Reduced payload size from 2,716,178 bytes to 120,129 bytes (95.5% reduction, ~35,746 tokens).
2. **Reactive 400 Token Overflow Failover**:
   - In `account_rotator.js` HTTP 400 handler, detects token overflow patterns (`maximum number of tokens`, `exceeds the maximum number of tokens allowed`, `input token count exceeds`).
   - Automatically engages emergency trajectory compaction (aggressive mode) and re-dispatches up to 5 attempts.
   - Dispatches successfully with `HTTP 200 OK`.
