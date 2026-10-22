# System Architecture Design Blueprint

## 1. Architectural Scope & Principles
- **Engine Core:** Multi-platform native asynchronous event bus.
- **Modularity:** Shallow call stacks (<= 3 indirection layers), Deep Module boundaries.
- **Portability:** Dynamic filesystem path resolution (`PathBuf` / relative joins).

## 2. Component Topology
```
[Client Application]
         │ (IPC Socket / Named Pipe)
         ▼
[Sovereign Gateway Service]
   ├── [Authenticator & Rate Limiter]
   ├── [Message Dispatcher & Router]
   └── [Plugin / Subagent Runner]
```

## 3. Technology Stack & Multi-OS Matrix
- **Core Engine:** Rust 1.80+ (zero-cost abstractions, memory safety without GC).
- **Client Protocol:** JSON-RPC 2.0 with framing headers.
- **OS Support:** Linux (x86_64, aarch64), Windows 10/11 (MSVC), macOS (Apple Silicon).

## 4. Security & Isolation Perimeter
- Sandboxed filesystem jail: Operations confined to dynamic workspace root.
- No network listeners opened: Gateway communicates exclusively over local IPC.
- Zero credentials stored in code: API keys resolved via OS keychain or session env.
