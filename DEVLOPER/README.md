# ⚡ Flowork OS — Developer & Architecture Handbook

> **Confidentiality & Integrity Notice**: This document governs the internal developer workflows, multi-OS build architecture, and hardware compatibility doctrines for Flowork OS (`FLOWORK-AGENT`). Flowork OS is an autonomous, sovereign agentic operating system engineered for extreme resilience, complete offline capability, and universal cross-platform parity.

---

## 🏛️ 1. Architectural Foundations & Sovereign Doctrines

Flowork OS operates under strict sovereign design rules to ensure zero drift, absolute stability, and zero runtime surprises:

1. **Single Source of Truth (SSOT)**:
   - The live operating system at `/home/mrflow/flowork` serves as the authoritative source of truth.
   - All tools, runtimes, models, and UI assets originate from this canonical tree.
2. **Strict Developer Isolation (`DEVLOPER/`)**:
   - The developer repository (`Documents/project`) strictly isolates all development assets, Rust source code, compilers, staging directories, and temporary tools within `DEVLOPER/`.
   - Gate 0 enforces that no unapproved loose files exist at the project repository root.
3. **Zero-Leak Security Doctrine**:
   - Sensitive developer directories (`connector/`, `connection/`, `connector_src/`, `prompts/`, `.fl_brain/`, `.flowork_brain/`, credential vaults) are strictly filtered out and never packaged into distribution releases or pushed to public repositories.
   - The Connector is pre-compiled into standalone native binary executables (`flowork-connector`, `flowork-connector.exe`, `flowork-connector-darwin-*`).
4. **Kesucian `@lock` & `@freez`**:
   - Core files and critical operational hooks bearing `@lock` or `@freez` directives are inviolable and cannot be deleted or arbitrarily rewritten.
5. **Anti-Zombie & Zero-Trust Hygiene**:
   - Dead code, deprecated wrappers, and zombie background processes must be aggressively eliminated. Every command and builder process must terminate cleanly with **Exit Code 0**.

---

## 💻 2. Intel Core i3 & Universal Baseline Architecture (Non-AVX2 Compatibility)

### 2.1 The Root Problem on Older CPUs
Modern high-performance runtimes (such as standard Bun or Rust binaries compiled with modern target CPU flags) default to utilizing advanced vector extensions (**AVX2**, **BMI2**, and **FMA**).

When run on older microarchitectures—most notably **Intel Core i3** (pre-Haswell/pre-AVX2), older **Intel Celeron / Pentium**, or older virtualized cloud environments—standard binaries immediately crash on startup with:
```
SIGILL (Illegal Instruction)
```

In legacy launcher scripts (`run.sh` / `flowork.bat`), this was previously handled by checking CPU flags:
```bash
# ⚠️ THE DEPRECATED, FLAWED LOGIC:
if [ "$SUPPORTS_AVX2" = true ]; then
    ./flowork-connector
else
    # FLAW: Bypassed native binary entirely on older CPUs!
    node connection/router.js
fi
```

### 2.2 Why the Legacy Fallback Failed on Fresh Installs
The legacy bypass caused catastrophic failures on fresh client installations:
1. **No System Node.js**: A brand new user machine (fresh install) does not have system `node` installed in `PATH`.
2. **Confidentiality / Zero-Leak**: The `connection/` folder contains proprietary source code and was intentionally removed from public releases.
3. **Symptom**: On an Intel Core i3 machine, the launcher skipped the native binary, attempted to execute `node connection/router.js`, silently failed, and left **Port 9099 offline**. This resulted in errors such as `Failed to fetch` and `Port offline 9099 check connector` when users attempted to connect or download account credentials.

### 2.3 The Sovereign Solution: Universal Baseline Compilation
To achieve 100% plug-and-play operation without requiring external runtimes, Flowork OS compiles the connector using **universal baseline targets**:

```bash
# Linux Universal Baseline (runs on all Intel Core i3, i5, i7, Celeron, Pentium, AMD)
bun build --compile --minify --target=bun-linux-x64-baseline connector/router.js --outfile flowork/flowork-connector

# Windows Universal Baseline
bun build --compile --minify --target=bun-windows-x64-baseline connector/router.js --outfile flowork/flowork-connector.exe

# macOS Intel Universal Baseline
bun build --compile --minify --target=bun-darwin-x64-baseline connector/router.js --outfile flowork/flowork-connector-darwin-x64

# macOS Apple Silicon (ARM64)
bun build --compile --minify --target=bun-darwin-arm64 connector/router.js --outfile flowork/flowork-connector-darwin-arm64
```

These baseline binaries exclude AVX2/BMI2 vector instructions, allowing them to execute natively on any x86_64 CPU produced since 2008 without external dependencies.

### 2.4 Multi-Layered Launch & Liveness Sequence in `run.sh`
The launch sequence in `run.sh` preserves direct execution of the native baseline binary on both modern and older CPUs:

```bash
if ! is_port_9099_listening; then
  # Layer 1: Hardware Capability Telemetry & Universal Launch
  SUPPORTS_AVX2=true
  if [ -f "/proc/cpuinfo" ]; then
    if ! grep -q -E "avx2|bmi2" /proc/cpuinfo 2>/dev/null; then
      SUPPORTS_AVX2=false
    fi
  fi

  NATIVE_LAUNCHED=false
  NATIVE_BIN=""
  if [ -x "$SCRIPT_DIR/flowork/flowork-connector" ]; then
    NATIVE_BIN="$SCRIPT_DIR/flowork/flowork-connector"
  elif [ -x "$SCRIPT_DIR/flowork-connector" ]; then
    NATIVE_BIN="$SCRIPT_DIR/flowork-connector"
  fi

  if [ -n "$NATIVE_BIN" ]; then
    if [ "$SUPPORTS_AVX2" = true ]; then
      echo "[X-Flow] ⚡ Modern CPU detected (AVX2/BMI2 OK). Launching Native Connector Binary on port 9099..."
    else
      echo "[X-Flow] 🛡️ Older CPU detected (Intel Core i3 / Non-AVX2). Launching Universal Baseline Connector Binary on port 9099..."
    fi
    launch_router_daemon "$NATIVE_BIN"
    NATIVE_LAUNCHED=true

    # Layer 2: Crash Guard & Liveness Verification Loop
    for i in {1..6}; do
      if is_port_9099_listening; then
        echo "[X-Flow] ✅ Native Connector bound successfully to port 9099."
        break
      fi
      sleep 0.5
    done
  fi

  # Layer 3: Failsafe Fallback (Only triggered if native binary crashes or fails to bind)
  if ! is_port_9099_listening; then
    if [ "$NATIVE_LAUNCHED" = true ]; then
      echo "[X-Flow] ⚠️ Native binary failed to bind port 9099. Auto-failing over to Node.js router..."
      pkill -9 -x "flowork-connector" 2>/dev/null || true
    fi
    start_node_router_fallback
  fi
fi
```

On Windows (`flowork.bat`), the native `flowork-connector.exe` is similarly prioritized as Layer 1, verified via `netstat -a -n -o | findstr ":9099 "`, and only falls back to Node.js if `flowork-connector.exe` is absent.

---

## ⏱️ 3. 120s Auto-Ping Watchdog & Subprocess Resilience

### 3.1 Bounded Stdout/Stderr Pipe Drain
A major source of hanging processes occurred when user scripts or background daemons (e.g. `nohup node server.js &` or dev servers) inherited stdout/stderr file descriptors. If an agent waited for the subprocess output stream to close before returning, it would hang indefinitely (e.g., 487+ seconds).

**Resolution in `DEVLOPER/core/src/native_tools.rs`**:
Both stdout and stderr drain tasks are wrapped with a strict 1,500ms bounded timeout:
```rust
let stdout_content = match tokio::time::timeout(Duration::from_millis(1500), stdout_task).await {
    Ok(Ok(content)) => content,
    _ => String::from("[TRUNCATED OR BACKGROUNDED PROCESS STDOUT]"),
};
```
If child background processes keep the inherited write pipe open, the parent process safely terminates the read task without stalling the agent.

### 3.2 120s Auto-Ping Notification Default
In `native_tools.rs`, when a command executes longer than 120,000ms (120s):
- The tool automatically emits an `[AUTO-PING NOTIFICATION // 120s ELAPSED]` heartbeat payload.
- In `canvas.js`, the live runner displays a reactive badge: `⏱️ AUTO-PING (120s)`.
- If an agent command remains unresponsive past 125 seconds, the circuit breaker in `agent.rs` intercepts the call, releasing the UI from freeze state.

### 3.3 Native Application Lifecycle (`restart` / `relaunch`)
The `app_control` native tool provides a first-class `restart` action:
- Gracefully terminates the running app process.
- Re-spawns the app under a clean session.
- Exposes REST endpoints: `POST /api/apps/:id/restart` and `POST /api/plugins/:id/restart`.

---

## 🛠️ 4. Build & Distribution Scripts

| Script | Purpose | Output Location |
| :--- | :--- | :--- |
| `DEVLOPER/build.sh all` | Compiles Rust core for Linux, Windows, and macOS (x86_64 & ARM64) | `DEVLOPER/build_output/` & `/home/mrflow/flowork/flowork/` |
| `DEVLOPER/build_connector.sh` | Compiles universal baseline Connector binaries for Linux, Windows, and macOS | `/home/mrflow/flowork/flowork/` |
| `DEVLOPER/upload_to_repo.sh` | Executes Gatekeeper checks, stages multi-OS distributions, and publishes to GitHub | Upstream `flowork-os/FLOWORK-AGENT` (`main`) |

---

## 🛡️ 5. Architectural Gatekeeper Checks (`validate_sovereignty.py`)

Before any release build or repository publication, `validate_sovereignty.py` executes 6 zero-trust verification gates:

- **Gate 0: Project Root Cleanliness**: Verifies that `Documents/project/` only contains `DEVLOPER/`, `.git`, and `.gitignore`.
- **Gate 1: Dynamic API Resolution**: Forbids hardcoded relative fetch calls (`/api/`) in app GUI files.
- **Gate 2: Zero Remote Redirections**: Blocks external redirects to remote launchers, ensuring 100% local operation.
- **Gate 3: SwarmFlow & DAG Integrity**: Ensures pipeline DAGs and SwarmFlow presets are intact and non-empty.
- **Gate 4: Subagent Roster Completeness**: Verifies all 9 core subagents (`mrflow`, `surface-extractor`, `remote-tester`, etc.) exist with valid metadata.
- **Gate 5: CPU Failover Guards**: Validates that `run.sh` and `flowork.bat` contain the non-AVX2 / Intel Core i3 universal baseline launch guards.

---
*Flowork OS Architecture Team — Sovereign Engine Division*
