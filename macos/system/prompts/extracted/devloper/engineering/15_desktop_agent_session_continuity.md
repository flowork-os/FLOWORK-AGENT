[FL_INDEX: keywords="system_prompt, devloper, 15_desktop_agent_session_continuity" | purpose="Extracted system prompt from DEVLOPER"]
<!-- CANONICAL_TRIGGER: session_continuity | TOOLS: agent_control -->
<DESKTOP_AGENT_SESSION_CONTINUITY_DOCTRINE>
1. DESCRIPTOR-BOUND ADVISORY FILE LOCKING:
   - Guard local session stores in `{sessions_dir}/` using OS-level file locks (`flock` on POSIX, `LockFileEx` on Windows) bound to open file descriptors rather than volatile PID files.
   - Locks auto-release on process termination or SIGKILL. Never unlink lock files; deleting active lock inodes destroys inter-process mutual exclusion.
2. DUAL-LOCK DAEMON SENTINEL & PROBING ARCHITECTURE:
   - Maintain primary `{sessions_dir}/<session_id>.lock` alongside `{sessions_dir}/<session_id>.lock.app` sentinel to distinguish long-running daemon controllers from transient CLI workers.
   - Probe GUI presence via non-blocking shared locks (`try_lock_shared`) to prevent concurrent CLI probes from mutually colliding or blocking execution.
3. SEAMLESS TERMINAL RESUME & ENVIRONMENT ISOLATION (`run_command`):
   - Preserve unadulterated native session identifiers across restarts, enabling instant terminal resumption (`--resume <session_id>`) into active agent workflows.
   - Separate holder diagnostics into detached metadata files (`{sessions_dir}/<session_id>.lock.holder`) to prevent mandatory locking from blocking external state inspection.
</DESKTOP_AGENT_SESSION_CONTINUITY_DOCTRINE>
