---
trigger_id: "TOOL-SYS-HEALTH-THERMAL"
name: "System Health & Thermal Overheat Diagnostic Trigger"
scopes:
  - "universal_all"
events:
  - "always_active"
  - "terminal_execution"
categories:
  - "all"
conditions:
  hw:
    cpu_temp_celsius: "> 70"
    cpu_load_percent: "> 85"
    ram_used_percent: "> 85"
---

# Trigger Directives & Operational Rationale
When host CPU temperature exceeds 70.0°C, CPU load exceeds 85%, or RAM utilization exceeds 85%:
1. Sovereign Tool Radar MUST elevate `sys_health` to the top recommendation banner.
2. The agent MUST inspect hardware telemetry before launching resource-intensive compilation, test suites, or background subagents.
3. If CPU temperature exceeds 80.0°C, background daemon concurrency MUST be throttled to 1 worker.
