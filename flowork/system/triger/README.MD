# 📡 Active System Trigger Architecture & Standard Runbook

> **Authoritative Specification:** Please refer to the comprehensive operational runbook in [`SKILL.md`](./SKILL.md).

## Quick Summary
An **Active Trigger** is an autonomous, push-based watchdog node in Flowork OS that lives visually on the Canvas Sidebar. When linked to an Agent node on the canvas, it runs a persistent background daemon (`watcher.py` / `watcher.mjs`), evaluates real-world thresholds, and proactively wakes up the connected agent by dispatching `prompt.md`.

### Core Structure:
- `trigger.json`: Visual canvas metadata, target agent binding, and user-tunable thresholds.
- `watcher.py` / `watcher.mjs`: Standalone daemon monitoring external signals.
- `prompt.md`: The markdown instruction payload injected to wake up the agent.
