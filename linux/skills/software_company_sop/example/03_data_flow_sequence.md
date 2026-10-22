# Data Flow Sequence Blueprint

## 1. Primary Request-Response Sequence
```mermaid
sequenceDiagram
    autonumber
    actor Client as Client App
    participant GW as Gateway Service
    participant Auth as Authenticator
    participant Dispatcher as Message Dispatcher
    participant Worker as Subagent / Handler

    Client->>GW: Connect (IPC / Named Pipe)
    GW->>Auth: Validate Handshake & Session Token
    Auth-->>GW: Token Validated (UID: swarm-01)
    Client->>GW: Request Payload (Method: dispatch_task)
    GW->>Dispatcher: Route Task to Registered Handler
    Dispatcher->>Worker: Invoke Handler Sandbox
    Worker-->>Dispatcher: Task Execution Result (Exit Code 0)
    Dispatcher-->>GW: Formatted JSON-RPC Response
    GW-->>Client: Transmit Response Frame
```

## 2. Failure & Circuit Breaker Sequence
1. **Invalid Token:** Authenticator responds with `401 Unauthorized`; connection drops immediately.
2. **Worker Panic / Timeout:** Dispatcher intercepts panic, isolates failure, increments error circuit breaker, and returns `504 Gateway Timeout` with zero process crash.
