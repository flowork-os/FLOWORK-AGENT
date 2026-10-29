[FL_INDEX: keywords="task_contract, financial_analyst, proforma_pnl, runway_model, unit_economics" | COT="Define I/O contracts and execution steps for financial-analyst subagent"]
# 📋 Task Execution & I/O Protocol: Financial Analyst

## 1. Input Contract
- **Strategy Baseline**: Addressable market (TAM/SAM/SOM), target customer segments, and monetization vectors from `corporate-strategist`.
- **Operational Cost Assumptions**: Headcount costs, cloud infrastructure burn, customer acquisition expenses, and tax/regulatory compliance overhead.

## 2. Execution Workflow
1. **Unit Economics Decomposition**: Compute CAC, ARPU, gross margin per user, and payback months.
2. **Burn Rate & Runway Projection**: Map monthly net burn, gross burn, and zero-cash date under base vs bear assumptions.
3. **P&L Pro-Forma Synthesis**: Construct a 12-to-24 month pro-forma statement detailing top-line, COGS, OpEx, and EBITDA.
4. **Capital Requirement Audit**: Determine exact minimum funding or cash cushion needed to reach break-even.

## 3. Output Deliverable & Handoff
- Financial Validation Document (`FINANCIAL_MODEL_<DOMAIN>.md`).
- Log milestone checkpoint via `team_progress(action: 'record', milestone: '...')`.
- Relay output to downstream compliance auditor (`legal-counsel`).
