<!-- CANONICAL_TRIGGER: flutter_dart | TOOLS: fl_bin_inspect -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE STATIC ANALYSIS & FIRST-PARTY RELEASE INTEGRITY AUDIT -->
# Sovereign Directive: Flutter Engine & Dart AOT Snapshot Binary Analysis

## 1. Diagnostic Step-by-Step Workflow
1. **Container & Architecture Inspection**: Audit APK/IPA container structure using `fl_inspect_android_package` to identify bundled Flutter assets and `libflutter.so` / `libapp.so` architectures.
2. **Snapshot Header & VM Version Extraction**: Extract the Dart snapshot header, magic constants, and isolate snapshot offsets from `libapp.so` to identify the matching Flutter SDK version and snapshot hash.
3. **Object Pool & Symbol Reification**: Parse Dart object pools, name tables, and class metadata to map high-level widget hierarchies and business logic entry points.
4. **Platform Channel & JNI Bridging**: Trace method channel handlers (`MethodChannel`, `EventChannel`) to bridge Dart execution flows to native Android/iOS platform components using `fl_seam_inspector`.

## 2. Defensive Systems Verification & Robustness Analysis
- **MethodChannel & Intent Injection**: Validate all data crossing Flutter MethodChannels to prevent unvalidated input injection into host platform activities and services.
- **Exported Component Leakage**: Audit Flutter host Activity declarations in `AndroidManifest.xml` to ensure exported flags and intent filters do not leak app state.
- **Secure Keystore & Storage**: Ensure sensitive tokens handled in Dart isolate memory use FlutterSecureStorage backed by hardware KeyStore rather than unencrypted SharedPreferences.
- **JNI Boundary & Memory Integrity**: Trap native runtime exceptions at the C++/Dart FFI boundary to prevent memory corruption and type confusion vulnerabilities.

## 3. Strict Guardrails & Anti-Hallucination
- **Snapshot Hash Ground Truth**: Never infer Dart functions without matching the exact Dart VM snapshot hash found in `libflutter.so`.
- **Verifiable Channel Evidence**: Prohibit declaring platform bridge vulnerabilities without citing verified MethodChannel call invocations and concrete handlers.
