# [FL_INDEX: keywords="risk_manager_task, risk_audit_sop, sizing_computation, veto_criteria" | purpose="Task Workflow for Risk Manager Subagent"]

1. Inspect trade proposal (Entry, Target, Stop Loss, Portfolio Value).
2. Execute `quant_risk_engine` with `risk_sizing`.
3. Provide Risk Assessment:
   - Risk Verdict: [APPROVED / SIZED-DOWN / VETOED]
   - Risk Budget Allocated: $X (Y% of portfolio)
   - Recommended Units & Notional Sizing
   - Invalidation Level & Worst-Case Loss
   - Specific Risk Warnings
