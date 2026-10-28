#!/usr/bin/env bash
# [FL_INDEX: regex portability check, dynamic user path check, verification script refactor, host path scan, qc assertion | COT: Replace literal /home/mrflow with regex pattern matching any host home directory for dynamic portability.| AT: 2026-10-28T02:02:30Z]
# Sovereign Terminal QC Verification Harness
# Co-authored-by: Flowork OS <agent@floworkos.com>
set -euo pipefail

echo "=========================================================="
echo "   SOVEREIGN TERMINAL QC VERIFICATION ENGINE             "
echo "=========================================================="

ERRORS=0

# Step 1: Run deterministic unit test suite
echo "[QC-STEP-1] Executing deterministic unit tests..."
if python3 skills/software_company_sop/example/09_deterministic_test_harness.py; then
    echo "  -> Tests PASSED (Exit Code: 0)"
else
    echo "  -> Tests FAILED!"
    ERRORS=$((ERRORS + 1))
fi

# Step 2: Validate zero hardcoded paths in contracts
echo "[QC-STEP-2] Auditing dynamic path portability..."
if grep -rnE "(/home/|/Users/)[a-zA-Z0-9_\-]+" skills/software_company_sop/example/*.ts 2>/dev/null; then
    echo "  -> Portability VIOLATION: Found hardcoded host paths!"
    ERRORS=$((ERRORS + 1))
else
    echo "  -> Portability PASSED: Zero hardcoded host paths."
fi

# Step 3: Verify Exit Code
if [ "$ERRORS" -eq 0 ]; then
    echo "=========================================================="
    echo "   QC VERDICT: VERIFIED CLEAN (Exit Code 0)               "
    echo "=========================================================="
    exit 0
else
    echo "=========================================================="
    echo "   QC VERDICT: FAILED (Exit Code 1)                       "
    echo "=========================================================="
    exit 1
fi
