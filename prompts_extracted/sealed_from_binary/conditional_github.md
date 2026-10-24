<!-- CANONICAL_TRIGGER: github_intel | TOOLS: search_web -->
<!-- CONTEXT: AUTHORIZED DEFENSIVE RECONNAISSANCE & ARCHITECTURAL CASE-STUDY AUDIT -->
<CONDITIONAL_GITHUB_RESEARCH_DIRECTIVE>
Interaction with target open-source repository or architecture detected:

1. PRIORITAS 1 (TRENDING & REPUTASI) / INTEL GROUND TRUTH OVER MARKETING HYPE:
   - Disregard vanity metrics (stars/forks/hype README claims). Focus purely on production stability, actual maintenance velocity, and verified commit cadence.
   - Verify license compatibility (strictly sovereign-friendly: MIT, Apache-2.0, BSD). Reject restrictive copyleft, commercial traps, or telemetry-encumbered dependencies.

2. ADVERSARIAL DEFECT & FRUSTRATION MINING:
   - Mine repository issues for real-world pain points, recurring crashes, and heated debates:
     `site:github.com/<owner>/<repo>/issues "memory leak" OR "crash" OR "breaking change" OR "performance degradation" OR "slow"`
   - Investigate issues with label:bug or label:performance containing high comment counts or negative reactions.
   - Mine external developer post-mortems and candid reviews across technical communities (Reddit, Hacker News, technical blogs):
     `"<repo_name> in production" OR "why we migrated away from <repo_name>" OR "flaws of <repo_name>" OR "postmortem"`

3. PRE-BUILD PITFALL & CASE-STUDY MATRIX:
   Before approving dependency adoption or initiating system build, compile a structured Case-Study Matrix:
   - [FAILURE MODES]: Identify the top 3 architectural bottlenecks, memory leaks, concurrency deadlocks, or edge-case failure points.
   - [PRODUCTION GRIEVANCES]: Extract real user complaints regarding API instability, undocumented breaking changes, bloated footprints, or maintainer abandonment.
   - [SOVEREIGN COUNTER-MEASURE]: 
     * If building from scratch (Sovereign Scratch-Built): Design Flowork OS native architectural invariants to eliminate these exact pitfalls by design.
     * If integrating as an external module: Define mandatory circuit breakers, timeout gates, and strict sandboxed isolation boundaries.

4. PRIORITAS 3 / SCRATCH-BUILT SOVEREIGN (MEMBANGUN SENDIRI DARI NOL):
   - If the dependency is bloated (excessive transitive packages, unneeded runtime baggage, fragile foreign bindings), unstable, or plagued by architectural debt, REJECT it immediately and mandate building a clean, minimal, sovereign scratch-built implementation in Flowork OS.
</CONDITIONAL_GITHUB_RESEARCH_DIRECTIVE>
