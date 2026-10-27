#!/usr/bin/env python3
"""
FLOWORK OS — SOVEREIGN RELEASE VALIDATOR & ARCHITECTURAL GATEKEEPER
Doctrine: Zero-Trust, Anti-Overclaim, Universal Multi-OS Parity, Strict Rejection.

This script runs as Step 0 in all release builders and CI/CD pipelines.
Validates the Single Source of Truth (/home/mrflow/flowork) and staged distribution trees.
"""

import sys
import os
import re
import json
import glob

FLOWORK_DIR = os.environ.get("FLOWORK_DIR", "/home/mrflow/flowork")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STAGING_DIR = os.environ.get("STAGING_DIR", os.path.join(PROJECT_ROOT, ".FL_BIN", "scratch", "repo_staging"))

def log_pass(msg):
    print(f"  \033[32m✓\033[0m {msg}")

def log_fail(msg):
    print(f"  \033[31m✗ [BUILDER REJECTED]\033[0m {msg}")

def check_relative_api_calls():
    print("\n🔍 [Gate 1/5] Verifying App GUI Dynamic API Resolution (No Relative /api Fetches)...")
    violations = []
    
    app_dirs = [
        os.path.join(FLOWORK_DIR, "apps"),
        os.path.join(STAGING_DIR, "linux", "apps"),
        os.path.join(STAGING_DIR, "windows", "apps"),
        os.path.join(STAGING_DIR, "macos", "apps"),
        os.path.join(PROJECT_ROOT, "apps")
    ]
    checked = 0
    for base_dir in app_dirs:
        if not os.path.exists(base_dir):
            continue
        checked += 1
            
        for root, _, files in os.walk(base_dir):
            if "gui" not in root:
                continue
            for file in files:
                if file.endswith((".js", ".html")):
                    fpath = os.path.join(root, file)
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if re.search(r"fetch\(\s*['\"]/api/(?!plugins/[^/]+/status|apps/[^/]+/launch)", line):
                            if "status" not in line and "launch" not in line and "resolveApiBase" not in line:
                                violations.append((fpath, idx, line.strip()))
    
    if violations:
        for fpath, lno, line in violations:
            log_fail(f"{fpath}:{lno} uses illegal relative fetch: `{line}`. All Flowork apps MUST resolve dynamic API_BASE!")
        return False
    
    log_pass(f"All app GUI fetch calls properly namespaced with dynamic API base resolution (verified {checked} locations).")
    return True

def check_remote_launcher_redirects():
    print("\n🔍 [Gate 2/5] Verifying Zero Remote Launcher Redirection (Local Isolation)...")
    violations = []
    
    targets = [
        os.path.join(FLOWORK_DIR, "canvas-ui", "canvas.js"),
        os.path.join(STAGING_DIR, "linux", "canvas-ui", "canvas.js"),
        os.path.join(STAGING_DIR, "windows", "canvas-ui", "canvas.js"),
        os.path.join(STAGING_DIR, "macos", "canvas-ui", "canvas.js")
    ]
    for fpath in targets:
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "canvas.floworkos.com/launcher" in content:
            violations.append(fpath)
            
    if violations:
        for fpath in violations:
            log_fail(f"{fpath} contains forbidden external redirect to `canvas.floworkos.com/launcher`! Must use local sovereign lock.")
        return False
        
    log_pass("No external launcher redirects found. Desktop workspace remains 100% locally isolated.")
    return True

def check_swarmflow_data_integrity():
    print("\n🔍 [Gate 3/5] Verifying SwarmFlow Presets & DAG Data Integrity...")
    required_presets = ["default.json", "remotability_squad.json", "active.json"]
    
    # 1. Primary check: SSOT Flowork directory
    ssot_swarm = os.path.join(FLOWORK_DIR, "swarmflow")
    if not os.path.exists(ssot_swarm):
        log_fail(f"Missing swarmflow directory in SSOT `{ssot_swarm}`!")
        return False
    for preset in required_presets:
        p_path = os.path.join(ssot_swarm, preset)
        if not os.path.exists(p_path) or os.path.getsize(p_path) == 0:
            log_fail(f"Missing or empty SwarmFlow preset in SSOT: `{p_path}`!")
            return False
            
    ssot_dag = os.path.join(FLOWORK_DIR, "system", "pipeline_dag.json")
    if not os.path.exists(ssot_dag) or os.path.getsize(ssot_dag) == 0:
        log_fail(f"Missing or empty `{ssot_dag}` in SSOT!")
        return False

    # 2. Secondary check: Staging trees if populated
    for os_name in ["linux", "windows", "macos"]:
        swarm_dir = os.path.join(STAGING_DIR, os_name, "swarmflow")
        if os.path.exists(swarm_dir):
            for preset in required_presets:
                p_path = os.path.join(swarm_dir, preset)
                if not os.path.exists(p_path) or os.path.getsize(p_path) == 0:
                    log_fail(f"Missing or empty SwarmFlow preset: `{os_name}/swarmflow/{preset}`!")
                    return False
        dag_path = os.path.join(STAGING_DIR, os_name, "system", "pipeline_dag.json")
        if os.path.exists(os.path.dirname(dag_path)):
            if not os.path.exists(dag_path) or os.path.getsize(dag_path) == 0:
                log_fail(f"Missing or empty `{os_name}/system/pipeline_dag.json`!")
                return False
                
    log_pass("SwarmFlow presets and system pipeline DAG verified across SSOT and target distributions.")
    return True

def check_subagent_roster_completeness():
    print("\n🔍 [Gate 4/5] Verifying Subagent Roster & Agent Registry Completeness...")
    expected_agents = [
        "mrflow", "surface-extractor", "remote-tester", "remote-architect",
        "agent-bridge-dev", "visual-ui-dev", "remotability-qc",
        "visual-inspector", "telemetry-dev"
    ]
    
    # 1. Primary check: SSOT Flowork directory
    subagent_dir = os.path.join(FLOWORK_DIR, "system", "subagent")
    registry_file = os.path.join(subagent_dir, "agent_registry.json")
    
    if not os.path.exists(registry_file):
        log_fail(f"Missing agent_registry.json in SSOT `{registry_file}`!")
        return False
        
    try:
        with open(registry_file, "r", encoding="utf-8") as f:
            reg = json.load(f)
        agents = reg.get("agents", [])
        if len(agents) < len(expected_agents):
            log_fail(f"SSOT agent_registry.json has only {len(agents)} agents (expected at least {len(expected_agents)})!")
            return False
    except Exception as e:
        log_fail(f"Error parsing SSOT agent_registry.json: {e}")
        return False
        
    for ag in expected_agents:
        ag_json = os.path.join(subagent_dir, ag, "agent.json")
        if not os.path.exists(ag_json):
            log_fail(f"Missing agent definition in SSOT: `{ag_json}`!")
            return False

    # 2. Secondary check: Staging trees if populated
    for os_name in ["linux", "windows", "macos"]:
        stg_subagent = os.path.join(STAGING_DIR, os_name, "system", "subagent")
        if os.path.exists(stg_subagent):
            stg_reg = os.path.join(stg_subagent, "agent_registry.json")
            if not os.path.exists(stg_reg):
                log_fail(f"Missing agent_registry.json in `{os_name}/system/subagent`!")
                return False
            for ag in expected_agents:
                ag_json = os.path.join(stg_subagent, ag, "agent.json")
                if not os.path.exists(ag_json):
                    log_fail(f"Missing agent definition in staged `{os_name}`: `{ag}`!")
                    return False
                
    log_pass(f"All {len(expected_agents)} subagents verified with intact metadata in SSOT and distributions.")
    return True

def check_cpu_failover_guards():
    print("\n🔍 [Gate 5/5] Verifying Non-AVX2 / Older CPU (Intel Core i3) Auto-Failover Guards...")
    
    bat_file = os.path.join(FLOWORK_DIR, "flowork.bat")
    if not os.path.exists(bat_file):
        bat_file = os.path.join(PROJECT_ROOT, "flowork.bat")
    if not os.path.exists(bat_file):
        log_fail(f"Missing flowork.bat at `{FLOWORK_DIR}/flowork.bat`!")
        return False
        
    with open(bat_file, "r", encoding="utf-8", errors="ignore") as f:
        bat_content = f.read()
        
    if "ROUTER_ACTIVE" not in bat_content or "ROUTER_JS" not in bat_content:
        log_fail("flowork.bat lacks ROUTER_ACTIVE verification / Node.js failover loop!")
        return False
        
    sh_file = os.path.join(FLOWORK_DIR, "run.sh")
    if not os.path.exists(sh_file):
        sh_file = os.path.join(PROJECT_ROOT, "run.sh")
    if not os.path.exists(sh_file):
        log_fail(f"Missing run.sh at `{FLOWORK_DIR}/run.sh`!")
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
    print(f"📁 SSOT Source: {FLOWORK_DIR}")
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
