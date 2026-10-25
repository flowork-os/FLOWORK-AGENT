<!-- [FL_INDEX: keywords="process_watchdog, runaway_process, zombie_pid, cpu_throttle, system_health" | purpose="Active trigger payload alert for runaway tool processes and excessive resource consumption"] -->
# 🚨 Runaway Process / Heavy Resource Alert

The Sovereign Watchdog Daemon has detected one or more tool processes (`PID`) consuming anomalous system resources or executing longer than the allowed threshold.

### 📊 Telemetry Details:
- **Detected Trigger**: Active Tool / Process Watchdog
- **Threshold Exceeded**: Sustained High CPU (>80%), Memory Spike (>1.5 GB), or Long Execution (>120s)
- **Status**: Edge-triggered with 180s hysteresis debounce cooldown

### 🛠️ Mandatory Sovereign Remediation Steps:
1. **Identify Anomalous PIDs**: Check the active processes, subshells, or runaway helper scripts using `run_command` or task management.
2. **Evaluate Process Sanctity**: Verify if the process is a legitimate long-running job (e.g. ffmpeg render, dataset build) or an orphan/stuck zombie tool process.
3. **Graceful Termination / Throttle**: If it is an unmonitored zombie or stuck loop, terminate the PID gracefully (`SIGTERM`, fallback to `SIGKILL`) to free system resources.
4. **Notify Operator**: Log an executive telemetry summary explaining the action taken and system health status.
