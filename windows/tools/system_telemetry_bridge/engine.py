#!/usr/bin/env python3
# [FL_INDEX: keywords="telemetry, monitoring, system_health, ipc_bridge, metrics" | purpose="Autonomous system telemetry collector and Canvas app status bridge engine"]
"""
Flowork OS Sovereign Telemetry Bridge Engine
Collects host runtime metrics, active Canvas applications, and process resource utilization,
exposing structured JSON telemetry for cross-agent synchronization and monitoring.
"""

import sys
import os
import json
import psutil
import time
from typing import Dict, Any, List

def get_system_telemetry() -> Dict[str, Any]:
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_count = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "timestamp": int(time.time()),
        "status": "healthy",
        "cpu": {
            "percent": cpu_percent,
            "logical_cores": cpu_count
        },
        "memory": {
            "total_bytes": memory.total,
            "available_bytes": memory.available,
            "used_bytes": memory.used,
            "percent": memory.percent
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "percent": disk.percent
        }
    }

def discover_active_apps(apps_dir: str = None) -> List[Dict[str, Any]]:
    if apps_dir is None:
        workspace_root = os.environ.get("FLOWORK_WORKSPACE", os.getcwd())
        apps_dir = os.path.join(workspace_root, "apps")
    active_apps = []
    if not os.path.exists(apps_dir):
        return active_apps
    
    for item in os.listdir(apps_dir):
        app_path = os.path.join(apps_dir, item)
        if os.path.isdir(app_path):
            manifest_path = os.path.join(app_path, "plugin.json")
            if not os.path.exists(manifest_path):
                manifest_path = os.path.join(app_path, "app.json")
            
            info = {
                "id": item,
                "installed": True,
                "has_manifest": os.path.exists(manifest_path)
            }
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        info["name"] = data.get("name", item)
                        info["version"] = data.get("version", "1.0.0")
                        info["category"] = data.get("category", "General")
                except Exception:
                    pass
            active_apps.append(info)
    return active_apps

def main():
    payload = {
        "telemetry": get_system_telemetry(),
        "canvas_apps": discover_active_apps(),
        "engine": "Flowork Sovereign Telemetry Bridge v1.0.0"
    }
    print(json.dumps(payload, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
