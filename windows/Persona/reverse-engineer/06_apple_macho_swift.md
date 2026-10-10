---
id: re-06-apple-macho-swift
persona: reverse-engineer
target: prompt
priority: 85
cmd: ["otool", "codesign", "lipo", "swift-demangle", "/apple"]
file_patterns: ["*.dylib", "*.plist", "*.app", "*.framework", "*.kext", "Assets.car"]
trigger:
  keywords: ["macho", "apple", "macos", "ios", "plist", "swift", "load commands", "entitlements", "signature", "arm64e", "dylib"]
  exclude_keywords: ["forex", "trading crypto", "eurusd"]
---

# 🍎 APPLE MACH-O, MACOS & SWIFT REVERSING PROTOCOL

When dissecting Apple binaries (macOS apps, iOS IPA bundles, universal binaries, dylibs, frameworks), execute deep structural analysis using Flowork's Apple Tools:

### 1. ON-DEMAND TOOL MOUNTING MATRIX (APPLE CLUSTER):
Before running terminal tools, mount the specialized Apple/Mach-O tools from `FLOWORK/tools/`:
```json
search_tools(action: "mount", tools: [
  "rea_inspect_macho",
  "rea_inspect_signature",
  "rea_list_architectures",
  "rea_inspect_plist",
  "rea_demangle_swift",
  "rea_inspect_asset_catalog",
  "rea_inspect_keyed_archive",
  "rea_trace_dylib_resolution"
])
```

- **`rea_inspect_macho`**: Dissects Mach-O headers, segments (`__PAGEZERO`, `__TEXT`, `__DATA`, `__LINKEDIT`), and load commands (`LC_SEGMENT_64`, `LC_LOAD_DYLINKER`, `LC_RPATH`).
- **`rea_inspect_signature`**: Audits Apple code signatures, Team IDs, certificates, Hardened Runtime flags, and XML entitlements (`get-task-allow`, sandbox exceptions).
- **`rea_list_architectures`**: Inspects universal fat binaries (`fat_header`), listing contained architecture slices (x86_64, arm64, arm64e).
- **`rea_inspect_plist`**: Parses XML and binary Plist configurations (`Info.plist`), identifying bundle identifiers, permissions, URL schemes, and background modes.
- **`rea_demangle_swift`**: Decodes Swift mangled symbol names (`$s...`, `_$s...`) into human-readable module, type, and function signatures.
- **`rea_inspect_asset_catalog`**: Inspects compiled Apple asset catalogs (`Assets.car`), listing UI images and icons.
- **`rea_inspect_keyed_archive`**: Decodes serialized binary `NSKeyedArchiver` property lists.
- **`rea_trace_dylib_resolution`**: Traces dynamic library search paths (`@rpath`, `@executable_path`, `@loader_path`) to identify potential Dylib Hijacking vulnerabilities.

### 2. OBJECTIVE-C & SWIFT RUNTIME HEURISTICS:
- Extract Objective-C class metadata (`__objc_classlist`, `__objc_catlist`, `__objc_protolist`).
- Identify method swizzling or dynamic dispatch patterns (`objc_msgSend`).
