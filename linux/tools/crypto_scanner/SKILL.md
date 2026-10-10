---
name: crypto-scanner
description: Standard Operating Procedure for analyzing cryptocurrency market metrics, 24h trading volume, order book depth, and liquidity spread.
keywords:
  - cryptocurrency
  - market
  - liquidity
  - volume
  - scanner
  - trading
  - volatility
  - depth
  - orderbook
  - pair
  - bitcoin
  - ethereum
  - solana
  - binance
  - telemetry
  - price
  - analytics
  - arbitrage
  - finance
  - inspection
---

# 🪙 CRYPTO SCANNER — OPERATIONAL RUNBOOK (SOP)

## 1. PURPOSE & CAPABILITY
The `crypto_scanner` tool performs real-time market microstructure analysis across top cryptocurrency trading pairs. It inspects 24-hour volume distribution, order book bid/ask depth, price volatility ratios, and liquidity spreads.

## 2. PREREQUISITES & MANDATORY GATE
> [!IMPORTANT]
> **DOKTRIN KEDAULATAN:** Every external dynamic tool must be inspected via its `SKILL.md` before execution. Never guess tool parameters without reading this document.

## 3. PARAMETERS & INPUT SCHEMA
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `pair` | string | No | `"BTC/USDT"` | The currency pair symbol (e.g., `BTC/USDT`, `ETH/USDT`, `SOL/USDT`). |
| `timeframe` | string | No | `"1h"` | Analysis window (`15m`, `1h`, `4h`, `1d`). |
| `depth` | number | No | `20` | Depth levels of the order book snapshot to calculate slippage. |

## 4. EXECUTION COMMANDS
Execute via shell runner:
```bash
node tools/crypto_scanner/main.mjs "BTC/USDT" "1h" 20
```
Or via JSON parameter invocation:
```bash
node tools/crypto_scanner/main.mjs --params '{"pair":"ETH/USDT","timeframe":"4h","depth":25}'
```

## 5. RETURN SCHEMA & INTERPRETATION
The scanner returns an Exit Code `0` structured JSON payload:
```json
{
  "status": "SUCCESS",
  "symbol": "BTC/USDT",
  "last_price": 64280.50,
  "change_24h_pct": 2.45,
  "volume_24h_usd": 18450200300,
  "bid_ask_spread_pct": 0.012,
  "liquidity_rating": "DEEP",
  "volatility_score": "MEDIUM",
  "timestamp": 1791566800
}
```

## 6. ERROR HANDLING & MITIGATION
* **Invalid Pair Symbol:** Ensure pairs follow standard uppercase slash notation (`COIN/QUOTE`), e.g., `BTC/USDT`.
* **Network Rate Limiting:** Scanner uses internal cache with a 5-second TTL to avoid exchange API exhaustion.
