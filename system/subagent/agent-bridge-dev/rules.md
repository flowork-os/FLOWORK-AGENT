# Operational Rules (Agent Bridge Dev)
1. Implement atomic REST/WebSocket handlers matching feature_matrix.json specifications.
2. Validate incoming payloads strictly; return structured status and latency telemetry.
3. Broadcast action triggers immediately to connected webviews so the UI reacts instantly.
4. Zero unhandled promise rejections and safe stream cleanup to prevent file descriptor leaks.
