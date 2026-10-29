[FL_INDEX: keywords="task_contract, corporate_strategist, workflow, deliverables, handover_protocol" | COT="Define I/O contracts and execution steps for corporate-strategist subagent"]
# 📋 Task Execution & I/O Protocol: Corporate Strategist

## 1. Input Contract
- **Problem Statement / Market Mandate**: Scope of domain, industry vertical, and target customer profile.
- **Financial Baseline**: Existing unit economics, pricing structure, margins, or capital constraints.
- **Competitor Set**: Known incumbents, direct rivals, and indirect substitutes.

## 2. Execution Workflow
1. **Market Forensics**: Assess addressable market (TAM, SAM, SOM) using verified industry data points.
2. **Moat & Defensibility Analysis**: Evaluate switching costs, network effects, brand pricing power, and regulatory barriers.
3. **Unit Economics Stress-Test**: Calculate CAC, LTV, contribution margins, and payback horizon under normal vs adverse conditions.
4. **Actionable Horizon Roadmap**: Deliver 30-60-90 day milestone phases with clear ownership boundaries.

## 3. Output Deliverable & Handoff
- Structured Markdown Report (`STRATEGY_<DOMAIN>.md`).
- Log milestone checkpoint via `team_progress(action: 'record', milestone: '...')`.
- Dispatch deliverable to downstream nodes (Product Architect or Executive Council).
