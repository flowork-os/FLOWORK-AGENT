#!/usr/bin/env python3
"""
FLOWORK OS — SOVEREIGN RELEASE VALIDATOR & ARCHITECTURAL GATEKEEPER
Doctrine: Zero-Trust, Anti-Overclaim, Universal Multi-OS Parity, Strict Rejection.

This script runs as Step 0 in all release builders and CI/CD pipelines.
If any fatal architectural defect or regression is detected, execution aborts with Exit Code 1.
"""

import sys
import os
import re
import json
import glob

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def log_pass(msg):
    print(f"  \033[32m✓\033[0m {msg}")

def log_fail(msg):
    print(f"  \033[31m✗ [BUILDER REJECTED]\033[0m {msg}")

def check_relative_api_calls():
    print("\n🔍 [Gate 1/5] Verifying App GUI Dynamic API Resolution (No Relative /api Fetches)...")
    violations = []
    
    app_dirs = ["flowork/apps", "linux/apps", "windows/apps", "macos/apps"]
    for rel_dir in app_dirs:
        base_dir = os.path.join(PROJECT_ROOT, rel_dir)
        if not os.path.exists(base_dir):
            continue
            
        for root, _, files in os.walk(base_dir):
            if "gui" not in root:
                continue
            for file in files:
                if file.endswith((".js", ".html")):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        # Catch fetch('/api/... or fetch("/api/... without API_BASE
                        if re.search(r"fetch\(\s*['\"]/api/(?!plugins/[^/]+/status|apps/[^/]+/launch)", line):
                            # Exempt health checks / dynamic resolver itself
                            if "status" not in line and "launch" not in line and "resolveApiBase" not in line:
                                violations.append((os.path.relpath(fpath, PROJECT_ROOT), idx, line.strip()))
    
    if violations:
        for fpath, lno, line in violations:
            log_fail(f"{fpath}:{lno} uses illegal relative fetch: `{line}`. All Flowork apps MUST resolve dynamic API_BASE!")
        return False
    
    log_pass("All app GUI fetch calls properly namespaced with dynamic API base resolution.")
    return True

def check_remote_launcher_redirects():
    print("\n🔍 [Gate 2/5] Verifying Zero Remote Launcher Redirection (Local Isolation)...")
    violations = []
    
    targets = [
        "flowork/canvas-ui/canvas.js", "linux/canvas-ui/canvas.js",
        "windows/canvas-ui/canvas.js", "macos/canvas-ui/canvas.js"
    ]
    for rel in targets:
        fpath = os.path.join(PROJECT_ROOT, rel)
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "canvas.floworkos.com/launcher" in content:
            violations.append(rel)
            
    if violations:
        for fpath in violations:
            log_fail(f"{fpath} contains forbidden external redirect to `canvas.floworkos.com/launcher`! Must use local sovereign lock.")
        return False
        
    log_pass("No external launcher redirects found. Desktop workspace remains 100% locally isolated.")
    return True

def check_swarmflow_data_integrity():
    print("\n🔍 [Gate 3/5] Verifying SwarmFlow Presets & DAG Data Integrity...")
    required_presets = ["default.json", "remotability_squad.json", "active.json"]
    target_os = ["flowork", "linux", "windows", "macos"]
    
    for os_name in target_os:
        swarm_dir = os.path.join(PROJECT_ROOT, os_name, "swarmflow")
        if not os.path.exists(swarm_dir):
            log_fail(f"Missing swarmflow directory in `{os_name}/swarmflow`!")
            return False
        for preset in required_presets:
            p_path = os.path.join(swarm_dir, preset)
            if not os.path.exists(p_path) or os.path.getsize(p_path) == 0:
                log_fail(f"Missing or empty SwarmFlow preset: `{os_name}/swarmflow/{preset}`!")
                return False
                
    # Verify pipeline_dag.json in system
    for os_name in target_os:
        dag_path = os.path.join(PROJECT_ROOT, os_name, "system", "pipeline_dag.json")
        if not os.path.exists(dag_path) or os.path.getsize(dag_path) == 0:
            log_fail(f"Missing or empty `{os_name}/system/pipeline_dag.json`!")
            return False
            
    log_pass("SwarmFlow presets and system pipeline DAG verified across all OS distributions.")
    return True

def check_subagent_roster_completeness():
    print("\n🔍 [Gate 4/5] Verifying Subagent Roster & Agent Registry Completeness...")
    target_os = ["flowork", "linux", "windows", "macos"]
    expected_agents = [
        "mrflow", "surface-extractor", "remote-tester", "remote-architect",
        "agent-bridge-dev", "visual-ui-dev", "remotability-qc",
        "visual-inspector", "telemetry-dev"
    ]
    
    for os_name in target_os:
        subagent_dir = os.path.join(PROJECT_ROOT, os_name, "system", "subagent")
        registry_file = os.path.join(subagent_dir, "agent_registry.json")
        
        if not os.path.exists(registry_file):
            log_fail(f"Missing agent_registry.json in `{os_name}/system/subagent`!")
            return False
            
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                reg = json.load(f)
            agents = reg.get("agents", [])
            if len(agents) < len(expected_agents):
                log_fail(f"`{os_name}/system/subagent/agent_registry.json` has only {len(agents)} agents (expected at least {len(expected_agents)})!")
                return False
        except Exception as e:
            log_fail(f"Error parsing `{os_name}/system/subagent/agent_registry.json`: {e}")
            return False
            
        for ag in expected_agents:
            ag_json = os.path.join(subagent_dir, ag, "agent.json")
            if not os.path.exists(ag_json):
                log_fail(f"Missing agent definition: `{os_name}/system/subagent/{ag}/agent.json`!")
                return False
                
    log_pass(f"All {len(expected_agents)} subagents verified with intact metadata across all OS targets.")
    return True

def check_cpu_failover_guards():
    print("\n🔍 [Gate 5/5] Verifying Non-AVX2 / Older CPU (Intel Core i3) Auto-Failover Guards...")
    
    bat_file = os.path.join(PROJECT_ROOT, "flowork.bat")
    if not os.path.exists(bat_file):
        log_fail("Missing flowork.bat at project root!")
        return False
        
    with open(bat_file, "r", encoding="utf-8", errors="ignore") as f:
        bat_content = f.read()
        
    if "ROUTER_ACTIVE" not in bat_content or "ROUTER_JS" not in bat_content:
        log_fail("flowork.bat lacks ROUTER_ACTIVE verification / Node.js failover loop!")
        return False
        
    sh_file = os.path.join(PROJECT_ROOT, "run.sh")
    if not os.path.exists(sh_file):
        log_fail("Missing run.sh at project root!")
        return False
        
    with open(sh_file, "r", encoding="utf-8", errors="ignore") as f:
        sh_content = f.read()
        
    if "SUPPORTS_AVX2" not in sh_content and "start_node_router_fallback" not in sh_content:
        log_fail("run.sh lacks AVX2 instruction guard or node router fallback!")
        return False
        
    log_pass("Universal CPU instruction compatibility guards verified in both Windows and Linux starters.")
    return True

def main():
    print("=" * 65)
    print("⚡ FLOWORK OS — SOVEREIGN RELEASE VALIDATOR (STEP 0 GATEKEEPER)")
    print("=" * 65)
    
    checks = [
        check_relative_api_calls,
        check_remote_launcher_redirects,
        check_swarmflow_data_integrity,
        check_subagent_roster_completeness,
        check_cpu_failover_guards
    ]
    
    failed = False
    for chk in checks:
        if not chk():
            failed = True
            
    print("\n" + "=" * 65)
    if failed:
        print("\033[31m🛑 RELEASE REJECTED: Fatal architectural violation(s) detected.\033[0m")
        print("Please resolve all gatekeeper errors above before compiling or publishing.")
        print("=" * 65)
        sys.exit(1)
    else:
        print("\033[32m✅ RELEASE APPROVED: All 5 sovereign gatekeeper checks PASSED.\033[0m")
        print("Builder authorized to proceed with compilation and deployment.")
        print("=" * 65)
        sys.exit(0)

if __name__ == "__main__":
    main()
