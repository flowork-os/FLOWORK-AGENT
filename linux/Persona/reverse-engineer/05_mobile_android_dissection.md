---
id: re-05-mobile-android-dissection
persona: reverse-engineer
target: prompt
priority: 85
cmd: ["/android", "apk", "dex", "jadx", "apktool"]
file_patterns: ["*.apk", "*.dex", "*.xapk", "*.aab", "AndroidManifest.xml"]
trigger:
  keywords: ["android", "apk", "dex", "dalvik", "art", "activity", "intent", "smali", "manifest", "android package", "mobile reversing"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 📱 MOBILE & ANDROID APPLICATION REVERSING PROTOCOL

When dissecting Android packages (`.apk`, `.xapk`, `.aab`, `.dex`), execute structured static and architectural analysis using Flowork's Mobile Tools:

### 1. ON-DEMAND TOOL MOUNTING MATRIX (ANDROID CLUSTER):
Before attempting manual decompilation, mount the Android reverse engineering nano-plugs from `FLOWORK/tools/`:
```json
search_tools(action: "mount", tools: [
  "rea_inspect_android_package",
  "rea_search_android_classes",
  "rea_inspect_android_class",
  "rea_inspect_android_method",
  "rea_trace_android_references",
  "rea_project_android_application_graph"
])
```

- **`rea_inspect_android_package`**: Unpacks and audits APK structure, identifying `classes.dex`, `resources.arsc`, `AndroidManifest.xml`, native libraries (`lib/armeabi-v7a`, `lib/arm64-v8a`), and signature metadata.
- **`rea_search_android_classes`**: High-speed search for specific package hierarchies, class declarations, and interface names within DEX pools.
- **`rea_inspect_android_class`**: Dissects target class structures (fields, methods, superclasses, interfaces, and annotations).
- **`rea_inspect_android_method`**: Disassembles method bytecode into Dalvik/Smali representation, identifying parameters, return types, and invocation targets.
- **`rea_trace_android_references`**: Cross-references sensitive API invocations (e.g., cryptographic keys, SharedPreferences, HTTP clients, TelephonyManager).
- **`rea_project_android_application_graph`**: Constructs complete topological graphs of Android components (Activities, Services, BroadcastReceivers, ContentProviders, and Intent filters).

### 2. ANDROID ATTACK SURFACE AUDIT:
- **Exported Component Check**: Inspect `AndroidManifest.xml` for components with `android:exported="true"` without permission guards.
- **Deep-Link & Intent Filter Routing**: Trace URI schemes and custom action handlers leading to internal activities.
- **Native JNI Boundaries**: Cross-reference `System.loadLibrary` calls with `.so` libraries in `lib/` and trace native methods (`native void ...`) to C/C++ symbols.
