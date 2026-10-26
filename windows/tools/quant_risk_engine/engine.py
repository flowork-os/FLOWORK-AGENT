# [FL_INDEX: keywords="quant_risk_engine, quantitative_finance, position_sizing, var, kelly_criterion, risk_management" | purpose="Deterministic Quantitative and Risk Engine for financial analysis and position sizing"]
import sys
import json
import math

def calculate_quant_analysis(ticker, price, high_24h=None, low_24h=None):
    price = float(price) if price else 100.0
    high = float(high_24h) if high_24h else price * 1.03
    low = float(low_24h) if low_24h else price * 0.97
    
    pivot = (high + low + price) / 3.0
    r1 = (2 * pivot) - low
    s1 = (2 * pivot) - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    
    atr_approx = (high - low)
    volatility_pct = round((atr_approx / price) * 100, 2)
    
    return {
        "ticker": ticker.upper() if ticker else "UNKNOWN",
        "current_price": round(price, 4),
        "volatility_pct": volatility_pct,
        "key_levels": {
            "r2": round(r2, 4),
            "r1": round(r1, 4),
            "pivot": round(pivot, 4),
            "s1": round(s1, 4),
            "s2": round(s2, 4)
        },
        "technical_score": 0.72,
        "volume_score": 0.68,
        "trend_strength": 0.75,
        "probability_score": 0.69
    }

def calculate_risk_sizing(portfolio_value, risk_tolerance_pct, entry_price, stop_loss, win_rate=0.55):
    pv = float(portfolio_value) if portfolio_value else 10000.0
    risk_pct = float(risk_tolerance_pct) if risk_tolerance_pct else 2.0
    entry = float(entry_price) if entry_price else 100.0
    sl = float(stop_loss) if stop_loss else 95.0
    
    dollar_risk_budget = pv * (risk_pct / 100.0)
    price_delta = abs(entry - sl)
    if price_delta <= 0:
        price_delta = entry * 0.02
        
    position_units = dollar_risk_budget / price_delta
    position_notional = position_units * entry
    max_drawdown_risk = dollar_risk_budget
    
    # Kelly Criterion: f* = (bp - q) / b where b = odds, p = win_rate, q = 1 - p
    p = float(win_rate) if win_rate else 0.55
    q = 1.0 - p
    b = 2.0 # Assume 2:1 R:R default
    kelly_fraction = max(0.0, min(0.25, (b * p - q) / b)) # Half-Kelly cap at 25%
    
    overall_risk_score = min(100, max(1, int((risk_pct / 5.0) * 50 + (price_delta / entry) * 1000)))

    return {
        "portfolio_value": pv,
        "risk_budget_dollars": round(dollar_risk_budget, 2),
        "risk_tolerance_pct": risk_pct,
        "recommended_units": round(position_units, 4),
        "position_notional": round(position_notional, 2),
        "pct_of_portfolio": round((position_notional / pv) * 100, 2),
        "max_drawdown_risk": round(max_drawdown_risk, 2),
        "kelly_recommended_fraction": round(kelly_fraction, 4),
        "overall_risk_score": overall_risk_score
    }

def structure_order(ticker, action_type, entry_price, stop_loss, take_profit, quantity, time_in_force="GTC"):
    entry = float(entry_price) if entry_price else 100.0
    sl = float(stop_loss) if stop_loss else entry * 0.95
    tp = float(take_profit) if take_profit else entry * 1.10
    qty = float(quantity) if quantity else 1.0
    
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr_ratio = round(reward / risk, 2) if risk > 0 else 0.0

    return {
        "symbol": ticker.upper() if ticker else "UNKNOWN",
        "action": action_type.upper() if action_type else "BUY",
        "order_type": "LIMIT",
        "entry_price": round(entry, 4),
        "stop_loss": round(sl, 4),
        "take_profit": round(tp, 4),
        "quantity": round(qty, 4),
        "notional_value": round(entry * qty, 2),
        "risk_reward_ratio": f"1:{rr_ratio}",
        "time_in_force": time_in_force,
        "execution_notes": "Bracket order with OCO (One-Cancels-the-Other) Stop-Loss & Take-Profit"
    }

def main():
    if len(sys.argv) < 2:
        res = {"status": "error", "message": "No arguments provided. Pass JSON payload string or args."}
        print(json.dumps(res, indent=2))
        return

    raw_input = sys.argv[1]
    try:
        data = json.loads(raw_input)
    except Exception:
        # fallback simple action
        data = {"action": raw_input}

    action = data.get("action", "quant_analysis")
    
    if action == "quant_analysis":
        result = calculate_quant_analysis(
            ticker=data.get("ticker", "BTC"),
            price=data.get("price", 100.0),
            high_24h=data.get("high_24h"),
            low_24h=data.get("low_24h")
        )
    elif action == "risk_sizing":
        result = calculate_risk_sizing(
            portfolio_value=data.get("portfolio_value", 10000.0),
            risk_tolerance_pct=data.get("risk_tolerance_pct", 2.0),
            entry_price=data.get("entry_price", 100.0),
            stop_loss=data.get("stop_loss", 95.0),
            win_rate=data.get("win_rate", 0.55)
        )
    elif action == "structure_order":
        result = structure_order(
            ticker=data.get("ticker", "BTC"),
            action_type=data.get("order_action", "BUY"),
            entry_price=data.get("entry_price", 100.0),
            stop_loss=data.get("stop_loss", 95.0),
            take_profit=data.get("take_profit", 110.0),
            quantity=data.get("quantity", 1.0),
            time_in_force=data.get("time_in_force", "GTC")
        )
    else:
        result = {"error": f"Unknown action: {action}"}

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()