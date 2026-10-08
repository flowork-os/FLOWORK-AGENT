---
id: tactical-hud-charts-specification
title: Standardized JSON Schema and Prompt Rules for In-Chat Tactical HUD Charts
created_at: 2026-10-08T10:59:00Z
category: frontend-visualization
status: resolved
keywords:
  - tactical-charts
  - trading-candlestick
  - donut-chart
  - bar-chart
  - line-chart
  - svg-visualization
  - json-schema
  - canvas-chat-renderer
  - prompt-engineering
  - system-rules
  - flowork-os
---

# In-Chat Tactical HUD Charts Specification & Prompt Integration

## Problem
While the Canvas UI frontend has built-in SVG renderers for `chart:trading`, `chart:donut`, `chart:bar`, and `chart:line`, the LLM agent would not naturally know how to emit these structured JSON markdown code blocks unless explicitly instructed via its prompt, rules, or skill runbooks. Without prompt training, the agent would default to generic markdown tables, ASCII art, or Python matplotlib scripts.

## Resolution
1. **Skill Runbook**: Created `skills/tactical_charts/SKILL.md` compliant with the 20 English keywords standard, providing strict JSON schemas for:
   - `chart:trading` / `chart:candlestick` (OHLC + Volume + Ticker)
   - `chart:donut` / `chart:pie` (Segments, Center KPI Text, Subtitle)
   - `chart:bar` (Categorical comparisons)
   - `chart:line` / `chart:area` (Continuous metrics and trend lines)
2. **Rule Standard**: Registered in `FL_RULES.MD` ensuring agents prioritize tactical chart code blocks whenever visual metrics or market data are requested.
3. **Frontend Integration**: Handled natively in `canvas-ui/canvas.js` via `renderTacticalChartCard`, generating zero-dependency pure SVG elements with download buttons and raw JSON data toggles.
