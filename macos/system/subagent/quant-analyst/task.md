# [FL_INDEX: keywords="quant_analyst_task, technical_breakdown, quantitative_score, key_levels" | purpose="Task Workflow for Quantitative Analyst Subagent"]

1. Query market price and 24h high/low data.
2. Run `quant_risk_engine` (action: `quant_analysis`) with target ticker and price parameters.
3. Formulate Quantitative Briefing:
   - Asset & Price: Current price & 24h range
   - Key Levels: Pivot, R1, R2, S1, S2
   - Volatility Index: ATR / Volatility %
   - Technical Conviction Score: 1-10
