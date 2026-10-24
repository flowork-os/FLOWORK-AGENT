<!-- CANONICAL_TRIGGER: adb_device | TOOLS: fl_inspect_adb_client -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE STATIC ANALYSIS & FIRST-PARTY RELEASE INTEGRITY AUDIT -->
# Sovereign Directive: ADB Device Discovery & Environment Inspection

## 1. Diagnostic Step-by-Step Workflow
1. **ADB Server & Host Diagnostic**: Audit local ADB daemon connection state and client configuration using `fl_inspect_adb_client`.
2. **Device Enumeration & Target Selection**: Discover connected physical/emulated devices, serial IDs, and connection transports via `fl_list_adb_devices`.
3. **Hardware & OS Fingerprinting**: Retrieve device build properties, Android OS version, SDK API level, and architecture ABI using `fl_inspect_adb_device`.
4. **Display & Capability Mapping**: Query screen resolution, density, orientation metrics with `fl_inspect_adb_display`, catalog hardware features via `fl_list_adb_features`, and inspect running system services via `fl_list_adb_services`.

## 2. Defensive Systems Verification & Robustness Analysis
- **Target Serial Drift**: Always anchor commands to specific verified device serials to prevent accidental execution across multi-device environments.
- **Unauthorized & Offline State**: Handle `unauthorized` or `offline` device states gracefully, validating USB debugging authorization before proceeding.
- **Root & Privilege Boundary**: Verify whether shell context operates as `shell` or `root` (`uid=0`), noting security boundaries and SELinux enforcement modes.
- **Service Enumeration Safety**: Restrict service triage to non-blocking introspection queries, avoiding service state corruption or daemon crashes.

## 3. Strict Guardrails & Anti-Hallucination
- **Physical Device Attestation**: Prohibit synthesizing speculative hardware specs or serial numbers without live proof from `fl_inspect_adb_device`.
- **Zero Blind Execution**: Require active verified target connection before dispatching higher-level package or runtime commands.
