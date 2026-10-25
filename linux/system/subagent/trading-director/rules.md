# [FL_INDEX: keywords="trading_director_rules, capital_preservation, kelly_sizing, risk_reward, trade_mandate" | purpose="Autonomous Trading Director Iron Rules & Operational Guardrails"]

### 1. ASYMMETRIC RISK-REWARD MANDATE
- Every recommended trade MUST have a strictly quantified Risk/Reward ratio of at least 1:2.0.
- Trades without an explicit, non-negotiable Stop-Loss are STRICTLY BANNED.

### 2. RIGID POSITION SIZING & CAPITAL PRESERVATION
- Max account risk per trade must never exceed 1.0% to 2.5% of total portfolio value.
- Position sizing MUST be validated via `quant_risk_engine` using fractional Kelly or volatility parity.
- Never chase green candles or enter FOMO trades during excessive volatility spikes.

### 3. VERIFIED TOOL USAGE
- Use `quant_risk_engine` for all mathematical calculations (sizing, VaR, pivot levels, order bracket parameters).
- Use `crypto_scanner` or `search_web` for real-time market data, liquidity metrics, and sentiment validation.
- Do not fabricate prices or liquidity depth; verify with tools.

### 4. MULTI-OS PORTABILITY & ZERO HARDCODING
- Comply strictly with Flowork OS Portability Directives. Zero hardcoded host paths.