<!-- CANONICAL_TRIGGER: tdd_cycle | TOOLS: fl_diagnostic_tracer -->
<TDD_RED_GREEN_REFACTOR_DOCTRINE>
1. STRICT RED PHASE BEFORE IMPLEMENTATION:
   - Write a minimal failing test on the public interface seam before touching implementation code in `{effective_ws}`.
   - Execute the test via `run_command` in terminal; verify that it FAILS for the expected reason (Exit Code != 0). Never trust an untested test.
2. MINIMAL GREEN IMPLEMENTATION:
   - Write ONLY the minimal production code necessary to turn the failing test green (Exit Code 0).
   - Resist the urge to write anticipatory logic, helper functions, or edge-case handling not exercised by the current failing test.
3. AGGRESSIVE REFACTOR UNDER GREEN SAFETY:
   - Refactor ruthlessly only while all tests pass green: eliminate duplication, improve naming, deepen module interfaces, and prune intermediate allocations.
   - Verify every refactor step with an immediate test run via `run_command`. Never leave broken tests between commits.
</TDD_RED_GREEN_REFACTOR_DOCTRINE>
