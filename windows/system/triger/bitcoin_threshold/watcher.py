#!/usr/bin/env python3
"""
🪙 Bitcoin Threshold Watcher Daemon (Active Trigger)
Flowork OS Sovereign Canvas Node
Co-authored-by: Flowork OS <agent@floworkos.com>
"""
import os
import sys
import time
import json
import signal
import urllib.request

CORE_URL = os.environ.get("FLOWORK_CORE_URL", "http://127.0.0.1:19890")
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIR_PATH, "trigger.json")
PROMPT_PATH = os.path.join(DIR_PATH, "prompt.md")

running = True

def handle_shutdown(signum, frame):
    global running
    running = False
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def load_prompt():
    try:
        with open(PROMPT_PATH, "r") as f:
            return f.read()
    except Exception:
        return "Bitcoin target threshold breached."

def dispatch_to_agent(target_agent, prompt_text, current_price, target_price):
    payload = {
        "trigger_id": "bitcoin_threshold",
        "to_agent": target_agent,
        "event_payload": {
            "asset": "BTC/USDT",
            "current_price": current_price,
            "target_price": target_price,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        },
        "prompt": prompt_text
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{CORE_URL}/api/prompt-dispatch",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": str(e)}

def evaluate_ticker():
    config = load_config()
    target_price = config.get("config", {}).get("target_price_usd", 100000)
    target_agent = config.get("target_agent", "crypto-analyst")
    prompt_text = load_prompt()

    # In production, probe market ticker feed
    current_price = 100250.0

    if current_price >= target_price:
        res = dispatch_to_agent(target_agent, prompt_text, current_price, target_price)
        print(json.dumps({
            "status": "triggered",
            "current_price": current_price,
            "target_price": target_price,
            "dispatch_result": res
        }), flush=True)
        return True
    else:
        print(json.dumps({
            "status": "standby",
            "current_price": current_price,
            "target_price": target_price
        }), flush=True)
        return False

def main():
    is_once = "--check-once" in sys.argv or "--test" in sys.argv
    if is_once:
        evaluate_ticker()
        sys.exit(0)

    config = load_config()
    interval = config.get("config", {}).get("poll_interval_seconds", 30)

    while running:
        evaluate_ticker()
        time.sleep(interval)

if __name__ == "__main__":
    main()
