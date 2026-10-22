#!/usr/bin/env python3
"""
🔔 Webhook Ingestion Watcher Daemon (Active Trigger)
Flowork OS Sovereign Canvas Node
Co-authored-by: Flowork OS <agent@floworkos.com>
"""
import os
import sys
import json
import signal
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

CORE_URL = os.environ.get("FLOWORK_CORE_URL", "http://127.0.0.1:19890")
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIR_PATH, "trigger.json")
PROMPT_PATH = os.path.join(DIR_PATH, "prompt.md")

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
        return "Incoming webhook event ingested."

def dispatch_to_agent(target_agent, prompt_text, body_data):
    payload = {
        "trigger_id": "webhook_receiver",
        "to_agent": target_agent,
        "event_payload": body_data,
        "prompt": f"{prompt_text}\n\n```json\n{json.dumps(body_data, indent=2)}\n```"
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

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            body_json = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            body_json = {"raw": body.decode("utf-8", errors="replace")}

        config = load_config()
        target_agent = config.get("target_agent", "system-integrator")
        prompt_text = load_prompt()

        res = dispatch_to_agent(target_agent, prompt_text, body_json)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "dispatched": res}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "active", "trigger": "webhook_receiver"}).encode("utf-8"))

    def log_message(self, format, *args):
        pass

def main():
    config = load_config()
    port = config.get("config", {}).get("listen_port", 19895)

    server = HTTPServer(("127.0.0.1", port), WebhookHandler)

    def handle_shutdown(signum, frame):
        server.server_close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    print(json.dumps({"status": "listening", "port": port}), flush=True)
    server.serve_forever()

if __name__ == "__main__":
    main()
