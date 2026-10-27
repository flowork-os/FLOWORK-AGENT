# System Telemetry Bridge
[FL_INDEX: keywords="telemetry, monitoring, system_health, bridge, documentation" | purpose="Documentation and usage guide for system telemetry bridge tool"]

## Overview
`system_telemetry_bridge` is an autonomous diagnostic and monitoring feature for Flowork OS. It provides real-time telemetry on system resources (CPU, RAM, Disk) and dynamically checks the presence and status of installed Canvas applications.

## Usage
Execute via Flowork external tool runner or directly via Python:
```bash
python3 tools/system_telemetry_bridge/engine.py
```
