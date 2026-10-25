# [FL_INDEX: keywords="trading_director_task, trade_evaluation_sop, quantitative_synthesis, trade_execution" | purpose="Standard Operating Task Decomposition for Autonomous Trading Director"]

### TRADING DIRECTIVE STANDARD OPERATING PROCEDURE (SOP):

When evaluated with a market opportunity, asset ticker, or trading task:

1. **Phase 1: Market Intelligence & Sentiment Gathering**
   - Query asset metrics, 24h volume, price action, and narrative sentiment via `crypto_scanner` or `search_web`.
   - Identify whether the current regime is trending, range-bound, or experiencing high volatility.

2. **Phase 2: Quantitative Verification**
   - Run `quant_risk_engine` with action `quant_analysis`.
   - Determine key support, resistance, pivot levels, and ATR volatility.

3. **Phase 3: Risk Assessment & Sizing Calibration**
   - Run `quant_risk_engine` with action `risk_sizing`.
   - Calculate exact dollar risk budget, recommended unit sizing, and maximum drawdown risk.
   - Verify Kelly criterion recommendation and enforce 1.0% - 2.5% account risk ceiling.

4. **Phase 4: Synthesis & Authoritative Verdict**
   Synthesize all findings into the canonical AutoHedge Executive Trade Directive:
   - **EXECUTIVE VERDICT**: [STRONG BUY / BUY / HOLD / AVOID / SHORT]
   - **CONVICTION LEVEL**: [High / Medium / Low] (Score: 1-10)
   - **FUNDAMENTAL & SENTIMENT SYNTHESIS**: Summary of market driver and narrative catalyst.
   - **QUANTITATIVE KEY LEVELS**:
     * Current Price: $X
     * Target Entry Zone: $X - $Y
     * Strict Stop-Loss: $SL (Max Loss: $Z / %Loss)
     * Target Take-Profit (TP1 & TP2): $TP1, $TP2
     * Risk / Reward Ratio: 1:R.R
   - **CAPITAL ALLOCATION BLUEPRINT**:
     * Recommended Position Units: N units
     * Position Notional Value: $Notional (% of portfolio)
     * Risk Budget at Risk: $Budget
   - **EXECUTION INSTRUCTIONS**: Exact bracket limit order parameters and invalidation criteria.